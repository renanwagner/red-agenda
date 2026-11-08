"""Leitura da agenda do dia: janelas e agendamentos confirmados dos barbeiros ativos."""
from datetime import datetime, time, timedelta

from sqlalchemy import select

from app.models import Agendamento, Barbeiro, JanelaAtendimento, Servico, db


def duracao_servico_ativo(id_servico):
    """Duração em minutos do serviço ativo, ou None se não existe ou está inativo."""
    return db.session.scalar(
        select(Servico.duracao_min).where(Servico.id_servico == id_servico, Servico.ativo.is_(True))
    )


def agendas_do_dia(data, id_barbeiro=None):
    """{id_barbeiro: {"abertas", "bloqueadas", "ocupados"}} com intervalos (início, fim) em datetime.

    Só barbeiros ativos (ou só `id_barbeiro`, se informado); só agendamentos confirmados que começam no dia.
    """
    consulta = select(Barbeiro.id_barbeiro).where(Barbeiro.ativo.is_(True))
    if id_barbeiro is not None:
        consulta = consulta.where(Barbeiro.id_barbeiro == id_barbeiro)
    ids = db.session.scalars(consulta)
    agendas = {i: {"abertas": [], "bloqueadas": [], "ocupados": []} for i in ids}
    if not agendas:
        return agendas

    janelas = db.session.scalars(
        select(JanelaAtendimento).where(
            JanelaAtendimento.data == data, JanelaAtendimento.barbeiro_id.in_(agendas)
        )
    )
    for j in janelas:
        chave = "abertas" if j.tipo == "aberto" else "bloqueadas"
        agendas[j.barbeiro_id][chave].append(
            (datetime.combine(data, j.hora_inicio), datetime.combine(data, j.hora_fim))
        )

    comeco = datetime.combine(data, time())
    confirmados = db.session.scalars(
        select(Agendamento).where(
            Agendamento.status == "confirmado",
            Agendamento.barbeiro_id.in_(agendas),
            Agendamento.inicio >= comeco,
            Agendamento.inicio < comeco + timedelta(days=1),
        )
    )
    for a in confirmados:
        agendas[a.barbeiro_id]["ocupados"].append((a.inicio, a.fim))
    return agendas
