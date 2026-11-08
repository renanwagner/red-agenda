"""RF07: janelas de atendimento. Sem Flask nem SQL.

Regras (docs/02 e decisão de 08/11/2026):
- hora_fim > hora_inicio; janelas do mesmo barbeiro, dia e tipo não se sobrepõem (encostadas podem);
- nenhuma mudança (criar, alterar, excluir) pode deixar um agendamento confirmado fora do horário
  de atendimento (fora de janela aberta ou dentro de bloqueio).
O limite de horários por dia é o próprio conjunto de janelas abertas.
"""
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations

from app.repositories import agendamentos as repo_agendamentos
from app.repositories import janelas as repo
from app.repositories import transacao
from app.services.horarios import AgendaDoDia, barbeiro_livre

TIPOS = ("aberto", "bloqueado")


@dataclass
class ResultadoJanela:
    ok: bool
    erro: str | None = None      # fim_antes, sobreposta, agendamento_fora, nao_encontrada, tipo
    id_janela: int | None = None


def validar_dia(propostas, agendamentos):
    """`propostas`: todas as janelas do dia depois da mudança, como (início, fim, tipo) em datetime.
    `agendamentos`: intervalos confirmados. Devolve o código do erro ou None."""
    if any(fim <= ini for ini, fim, _ in propostas):
        return "fim_antes"
    for (a_ini, a_fim, a_tipo), (b_ini, b_fim, b_tipo) in combinations(propostas, 2):
        if a_tipo == b_tipo and a_ini < b_fim and b_ini < a_fim:
            return "sobreposta"
    agenda = AgendaDoDia(abertas=[(i, f) for i, f, t in propostas if t == "aberto"],
                         bloqueadas=[(i, f) for i, f, t in propostas if t == "bloqueado"])
    if any(not barbeiro_livre(ini, fim, agenda) for ini, fim in agendamentos):
        return "agendamento_fora"
    return None


def _intervalo(j):
    return (datetime.combine(j["data"], j["hora_inicio"]), datetime.combine(j["data"], j["hora_fim"]), j["tipo"])


def obter(id_barbeiro, id_janela):
    """Janela do barbeiro (ou de qualquer barbeiro, se `id_barbeiro` é None: administrador)."""
    j = repo.obter(id_janela)
    if j is None or (id_barbeiro is not None and j["barbeiro_id"] != id_barbeiro):
        return None
    return j


def listar(id_barbeiro, data):
    return repo.do_dia(id_barbeiro, data)


def _validar_e_aplicar(id_barbeiro, data, ignorar, nova, aplicar):
    outras = [_intervalo(j) for j in repo.do_dia(id_barbeiro, data) if j["id_janela"] != ignorar]
    propostas = outras + ([nova] if nova else [])
    erro = validar_dia(propostas, repo.confirmados_do_dia(id_barbeiro, data))
    if erro:
        transacao.desfazer_transacao()
        return ResultadoJanela(ok=False, erro=erro)
    id_janela = aplicar()
    transacao.confirmar_transacao()
    return ResultadoJanela(ok=True, id_janela=id_janela)


def salvar(id_barbeiro, data, hora_inicio, hora_fim, tipo, id_janela=None):
    """Cria (sem `id_janela`) ou altera a janela. Na alteração, a data é a da própria janela e
    `id_barbeiro` None permite ao administrador alterar a de qualquer barbeiro."""
    if tipo not in TIPOS:
        return ResultadoJanela(ok=False, erro="tipo")
    transacao.nova_transacao()
    try:
        if id_janela is not None:
            atual = obter(id_barbeiro, id_janela)
            if atual is None:
                transacao.desfazer_transacao()
                return ResultadoJanela(ok=False, erro="nao_encontrada")
            id_barbeiro, data = atual["barbeiro_id"], atual["data"]
        # Mesma trava da gravação de agendamento: janela e agendamento não mudam ao mesmo tempo
        if not repo_agendamentos.travar_barbeiro_ativo(id_barbeiro):
            transacao.desfazer_transacao()
            return ResultadoJanela(ok=False, erro="nao_encontrada")
        nova = (datetime.combine(data, hora_inicio), datetime.combine(data, hora_fim), tipo)
        if id_janela is None:
            def aplicar():
                return repo.criar(id_barbeiro, data, hora_inicio, hora_fim, tipo)
        else:
            def aplicar():
                repo.atualizar(id_janela, hora_inicio, hora_fim, tipo)
                return id_janela
        return _validar_e_aplicar(id_barbeiro, data, id_janela, nova, aplicar)
    except Exception:
        transacao.desfazer_transacao()
        raise


def excluir(id_barbeiro, id_janela):
    """Exclui a janela, se nenhum agendamento confirmado ficar fora do atendimento."""
    transacao.nova_transacao()
    try:
        atual = obter(id_barbeiro, id_janela)
        if atual is None or not repo_agendamentos.travar_barbeiro_ativo(atual["barbeiro_id"]):
            transacao.desfazer_transacao()
            return ResultadoJanela(ok=False, erro="nao_encontrada")

        def aplicar():
            repo.excluir(id_janela)
            return id_janela

        return _validar_e_aplicar(atual["barbeiro_id"], atual["data"], id_janela, None, aplicar)
    except Exception:
        transacao.desfazer_transacao()
        raise
