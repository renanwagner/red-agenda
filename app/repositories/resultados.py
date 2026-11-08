"""Leitura do que foi gravado, para a Tela 4 (sem dados do cliente)."""
from sqlalchemy import select

from app.models import Agendamento, Barbeiro, ListaEspera, Servico, db


def resumo_agendamento(id_agendamento):
    linha = db.session.execute(
        select(Agendamento.status, Agendamento.inicio, Servico.nome, Servico.duracao_min, Barbeiro.nome)
        .join(Servico, Servico.id_servico == Agendamento.servico_id)
        .join(Barbeiro, Barbeiro.id_barbeiro == Agendamento.barbeiro_id)
        .where(Agendamento.id_agendamento == id_agendamento)
    ).first()
    if linha is None:
        return None
    status, inicio, servico, duracao, barbeiro = linha
    return {"status": status, "data": inicio.date(), "hora": inicio.time(),
            "servico": {"nome": servico, "duracao_min": duracao}, "barbeiro": barbeiro}


def resumo_entrada(id_espera):
    linha = db.session.execute(
        select(ListaEspera.status, ListaEspera.data_desejada, ListaEspera.hora_desejada,
               Servico.nome, Servico.duracao_min, Barbeiro.nome)
        .join(Servico, Servico.id_servico == ListaEspera.servico_id)
        .outerjoin(Barbeiro, Barbeiro.id_barbeiro == ListaEspera.barbeiro_id)
        .where(ListaEspera.id_espera == id_espera)
    ).first()
    if linha is None:
        return None
    status, data, hora, servico, duracao, barbeiro = linha
    return {"status": status, "data": data, "hora": hora,
            "servico": {"nome": servico, "duracao_min": duracao}, "barbeiro": barbeiro}
