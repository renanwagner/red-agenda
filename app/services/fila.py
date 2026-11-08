"""Fila de espera: entrar (RF04) e escolher o próximo a chamar (regra do RF05). Sem Flask nem SQL."""
from dataclasses import dataclass

from app.repositories import agenda as repo_agenda
from app.repositories import clientes as repo_clientes
from app.repositories import fila as repo
from app.repositories import transacao
from app.services.agendamento import normalizar_telefone


@dataclass
class ResultadoFila:
    entrou: bool
    duplicada: bool = False
    id_espera: int | None = None


def entrar_na_fila(id_servico, id_barbeiro, data, hora, nome, telefone):
    """Grava a entrada `aguardando`. `id_barbeiro` preenchido = fila do barbeiro; None = fila por horário.

    Recusa se o serviço ou o barbeiro não estão ativos, e marca `duplicada` se já existe a mesma
    entrada aguardando (cliente, serviço, data, hora e barbeiro, com o nulo contando como valor).
    """
    transacao.nova_transacao()
    try:
        valido = repo_agenda.duracao_servico_ativo(id_servico) is not None and (
            id_barbeiro is None or repo.barbeiro_ativo(id_barbeiro))
        if not valido:
            transacao.desfazer_transacao()
            return ResultadoFila(entrou=False)
        id_cliente = repo_clientes.obter_ou_criar_cliente(nome, normalizar_telefone(telefone))
        id_espera = repo.criar_entrada(id_cliente, id_servico, id_barbeiro, data, hora)
        if id_espera is None:
            existente = repo.id_entrada_aguardando(id_cliente, id_servico, id_barbeiro, data, hora)
            transacao.desfazer_transacao()
            return ResultadoFila(entrou=False, duplicada=True, id_espera=existente)
        transacao.confirmar_transacao()
        return ResultadoFila(entrou=True, id_espera=id_espera)
    except Exception:
        transacao.desfazer_transacao()
        raise


def escolher_proximo(entradas, *, id_servico, id_barbeiro, hora, cabe):
    """Regra de chamada (docs/02, RF05): id da entrada a chamar quando um horário é liberado, ou None.

    `entradas`: entradas `aguardando` da data, como dicionários (id_espera, barbeiro_id, servico_id,
    hora_desejada, entrou_em). Compatível = mesmo serviço e hora_desejada igual ao início liberado,
    se o serviço cabe no bloco liberado (`cabe`). Primeiro a fila do barbeiro liberado; se não houver,
    a fila por horário (barbeiro_id nulo). Dentro de cada fila, por ordem de entrada.
    """
    if not cabe:
        return None
    compativeis = [e for e in entradas if e["servico_id"] == id_servico and e["hora_desejada"] == hora]
    for fila in (id_barbeiro, None):
        candidatos = sorted((e for e in compativeis if e["barbeiro_id"] == fila), key=lambda e: e["entrou_em"])
        if candidatos:
            return candidatos[0]["id_espera"]
    return None
