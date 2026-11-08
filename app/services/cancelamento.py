"""RF05: cancelar o agendamento e indicar o próximo da fila, um por vez. Sem Flask nem SQL.

Regras (docs/02 e decisões de 08/11/2026):
- cancelar muda o status para `cancelado` (não apaga); só o dono ou o administrador cancela;
- o próximo é escolhido por `fila.escolher_proximo` (fila do barbeiro antes da fila por horário,
  ordem de entrada), se o serviço ainda cabe no bloco liberado; o escolhido passa a `chamado`;
- "Não conseguiu falar? Chamar o próximo": o chamado passa a `desistiu` e indica-se o seguinte;
- tudo numa transação: se algo falha, nada muda.
O horário liberado não fica reservado: ele volta a aparecer no link público.
"""
from dataclasses import dataclass

from app.repositories import agenda as repo_agenda
from app.repositories import agendamentos as repo
from app.repositories import fila as repo_fila
from app.repositories import transacao
from app.services.agenda_painel import telefone_txt
from app.services.fila import escolher_proximo
from app.services.horarios import AgendaDoDia, barbeiro_livre, intervalo


@dataclass
class ResultadoCancelamento:
    ok: bool
    erro: str | None = None       # nao_encontrado, nao_cancelavel, ja_atualizado
    id_espera: int | None = None  # entrada chamada (None: ninguém compatível)


def _do_usuario(ag, id_barbeiro):
    """`id_barbeiro` None = administrador (qualquer agendamento)."""
    return ag is not None and (id_barbeiro is None or ag["barbeiro_id"] == id_barbeiro)


def _cabe_no_bloco(ag):
    """O serviço ainda cabe no horário liberado, com a agenda de agora (sem o cancelado)."""
    data = ag["inicio"].date()
    agenda = repo_agenda.agendas_do_dia(data, ag["barbeiro_id"]).get(ag["barbeiro_id"])   # None: inativo
    duracao = repo_agenda.duracao_servico_ativo(ag["servico_id"])
    if agenda is None or duracao is None:
        return False
    inicio, fim = intervalo(data, ag["inicio"].time(), duracao)
    return barbeiro_livre(inicio, fim, AgendaDoDia(**agenda))


def _chamar(ag):
    """Marca como `chamado` o próximo compatível e devolve o id dele (ou None)."""
    if not _cabe_no_bloco(ag):
        return None
    entradas = repo_fila.aguardando_da_data(ag["inicio"].date())
    while True:
        id_espera = escolher_proximo(entradas, id_servico=ag["servico_id"], id_barbeiro=ag["barbeiro_id"],
                                     hora=ag["inicio"].time(), cabe=True)
        if id_espera is None or repo_fila.marcar_chamado(id_espera):
            return id_espera
        entradas = [e for e in entradas if e["id_espera"] != id_espera]   # outro pedido chamou antes


def _em_transacao(id_agendamento, id_barbeiro, status_esperado, passo):
    transacao.nova_transacao()
    try:
        ag = repo.obter(id_agendamento, travar=True)
        if not _do_usuario(ag, id_barbeiro):
            transacao.desfazer_transacao()
            return ResultadoCancelamento(ok=False, erro="nao_encontrado")
        if ag["status"] != status_esperado:
            transacao.desfazer_transacao()
            return ResultadoCancelamento(ok=False, erro="nao_cancelavel")
        r = passo(ag)
        if r.ok:
            transacao.confirmar_transacao()
        else:
            transacao.desfazer_transacao()
        return r
    except Exception:
        transacao.desfazer_transacao()
        raise


def cancelar_e_chamar(id_agendamento, id_barbeiro=None):
    """Cancela o agendamento confirmado e chama o próximo compatível da fila."""
    def passo(ag):
        repo.cancelar(id_agendamento)       # a linha está travada: ainda confirmado
        return ResultadoCancelamento(ok=True, id_espera=_chamar(ag))
    return _em_transacao(id_agendamento, id_barbeiro, "confirmado", passo)


def chamar_proximo(id_agendamento, id_espera_atual, id_barbeiro=None):
    """O chamado não atendeu: passa a `desistiu` e chama o seguinte para o mesmo horário liberado."""
    def passo(ag):
        atual = repo_fila.entrada(id_espera_atual)
        mesmo_horario = atual is not None and (
            atual["servico_id"] == ag["servico_id"] and atual["data_desejada"] == ag["inicio"].date()
            and atual["hora_desejada"] == ag["inicio"].time() and atual["barbeiro_id"] in (ag["barbeiro_id"], None))
        if not (mesmo_horario and repo_fila.mudar_status(id_espera_atual, "chamado", "desistiu")):
            return ResultadoCancelamento(ok=False, erro="ja_atualizado")   # ex.: toque repetido
        return ResultadoCancelamento(ok=True, id_espera=_chamar(ag))
    return _em_transacao(id_agendamento, id_barbeiro, "cancelado", passo)


# ---------- leitura para as telas ----------

def _servico(linha):
    return {"nome": linha["servico_nome"], "duracao_min": linha["servico_duracao"]}


def obter(id_agendamento, id_barbeiro=None):
    """Agendamento para a confirmação e o resultado, ou None se não existe ou é de outro barbeiro."""
    ag = repo.obter(id_agendamento)
    if not _do_usuario(ag, id_barbeiro):
        return None
    return {"id_agendamento": ag["id_agendamento"], "barbeiro_id": ag["barbeiro_id"], "inicio": ag["inicio"],
            "fim": ag["fim"], "status": ag["status"], "cliente": ag["cliente"],
            "telefone": telefone_txt(ag["telefone"]), "servico": _servico(ag)}


def resumo_chamado(id_espera):
    """Cliente chamado: nome, telefone, serviço, data, hora e barbeiro (None = fila por horário)."""
    e = repo_fila.entrada(id_espera)
    if e is None:
        return None
    return {"id_espera": e["id_espera"], "cliente": e["cliente"], "telefone": telefone_txt(e["telefone"]),
            "servico": _servico(e), "data": e["data_desejada"], "hora": e["hora_desejada"],
            "barbeiro": e["barbeiro"]}
