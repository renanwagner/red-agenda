"""Leitura da agenda: janelas e confirmados do dia (disponibilidade) e do período (painel, RF06)."""
from datetime import datetime, time, timedelta

from sqlalchemy import select

from app.models import Agendamento, Barbeiro, Cliente, JanelaAtendimento, Servico, db


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


def confirmados_do_periodo(id_barbeiro, inicio, fim):
    """Confirmados do barbeiro com início em [inicio, fim), em ordem de horário (RF06).

    Cada item: inicio, fim, cliente, telefone (só dígitos), servico_nome, servico_duracao.
    """
    linhas = db.session.execute(
        select(Agendamento.inicio, Agendamento.fim, Cliente.nome.label("cliente"), Cliente.telefone,
               Servico.nome.label("servico_nome"), Servico.duracao_min.label("servico_duracao"))
        .join(Cliente, Agendamento.cliente_id == Cliente.id_cliente)
        .join(Servico, Agendamento.servico_id == Servico.id_servico)
        .where(Agendamento.barbeiro_id == id_barbeiro, Agendamento.status == "confirmado",
               Agendamento.inicio >= inicio, Agendamento.inicio < fim)
        .order_by(Agendamento.inicio)
    )
    return [dict(linha._mapping) for linha in linhas]
