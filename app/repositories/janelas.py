"""Repositório de janelas de atendimento (RF07)."""
from datetime import datetime, time, timedelta

from sqlalchemy import select

from app.models import Agendamento, JanelaAtendimento, db

_CAMPOS = ("id_janela", "barbeiro_id", "data", "hora_inicio", "hora_fim", "tipo")


def _dict(j):
    return {c: getattr(j, c) for c in _CAMPOS}


def do_dia(id_barbeiro, data):
    janelas = db.session.scalars(
        select(JanelaAtendimento)
        .where(JanelaAtendimento.barbeiro_id == id_barbeiro, JanelaAtendimento.data == data)
        .order_by(JanelaAtendimento.hora_inicio, JanelaAtendimento.tipo)
    )
    return [_dict(j) for j in janelas]


def obter(id_janela):
    j = db.session.get(JanelaAtendimento, id_janela)
    return _dict(j) if j else None


def criar(id_barbeiro, data, hora_inicio, hora_fim, tipo):
    j = JanelaAtendimento(barbeiro_id=id_barbeiro, data=data, hora_inicio=hora_inicio,
                          hora_fim=hora_fim, tipo=tipo)
    db.session.add(j)
    db.session.flush()
    return j.id_janela


def atualizar(id_janela, hora_inicio, hora_fim, tipo):
    j = db.session.get(JanelaAtendimento, id_janela)
    j.hora_inicio, j.hora_fim, j.tipo = hora_inicio, hora_fim, tipo
    db.session.flush()


def excluir(id_janela):
    db.session.delete(db.session.get(JanelaAtendimento, id_janela))
    db.session.flush()


def confirmados_do_dia(id_barbeiro, data):
    """Intervalos (início, fim) dos agendamentos confirmados do barbeiro que começam na data."""
    comeco = datetime.combine(data, time())
    linhas = db.session.execute(
        select(Agendamento.inicio, Agendamento.fim).where(
            Agendamento.barbeiro_id == id_barbeiro, Agendamento.status == "confirmado",
            Agendamento.inicio >= comeco, Agendamento.inicio < comeco + timedelta(days=1))
    )
    return [tuple(linha) for linha in linhas]
