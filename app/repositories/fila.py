"""Repositório da lista de espera (RF04)."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Barbeiro, ListaEspera, db


def barbeiro_ativo(id_barbeiro):
    return db.session.scalar(
        select(Barbeiro.id_barbeiro).where(Barbeiro.id_barbeiro == id_barbeiro, Barbeiro.ativo.is_(True))
    ) is not None


def id_entrada_aguardando(cliente_id, servico_id, barbeiro_id, data, hora):
    """Id da entrada `aguardando` igual (barbeiro nulo = fila por horário), ou None."""
    filtro_barbeiro = (ListaEspera.barbeiro_id.is_(None) if barbeiro_id is None
                       else ListaEspera.barbeiro_id == barbeiro_id)
    return db.session.scalar(select(ListaEspera.id_espera).where(
        ListaEspera.cliente_id == cliente_id, ListaEspera.servico_id == servico_id, filtro_barbeiro,
        ListaEspera.data_desejada == data, ListaEspera.hora_desejada == hora,
        ListaEspera.status == "aguardando",
    ))


def criar_entrada(cliente_id, servico_id, barbeiro_id, data, hora):
    """Cria a entrada `aguardando`. Devolve o id, ou None se já existe uma igual aguardando
    (o índice único uq_espera_aguardando decide, mesmo com pedidos simultâneos)."""
    try:
        with db.session.begin_nested():
            entrada = ListaEspera(cliente_id=cliente_id, servico_id=servico_id, barbeiro_id=barbeiro_id,
                                  data_desejada=data, hora_desejada=hora, status="aguardando")
            db.session.add(entrada)
        return entrada.id_espera
    except IntegrityError:
        return None
