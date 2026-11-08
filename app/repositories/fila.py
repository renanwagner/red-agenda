"""Repositório da lista de espera (RF04) e da chamada (RF05)."""
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models import Barbeiro, Cliente, ListaEspera, Servico, db


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


def aguardando_da_data(data):
    """Entradas `aguardando` da data, no formato que a regra de chamada espera."""
    linhas = db.session.execute(
        select(ListaEspera.id_espera, ListaEspera.barbeiro_id, ListaEspera.servico_id,
               ListaEspera.hora_desejada, ListaEspera.entrou_em)
        .where(ListaEspera.data_desejada == data, ListaEspera.status == "aguardando")
    )
    return [dict(linha._mapping) for linha in linhas]


def mudar_status(id_espera, de, para):
    """Muda o status só se ainda for `de` (dois pedidos não mexem na mesma entrada). True se mudou."""
    r = db.session.execute(
        update(ListaEspera).where(ListaEspera.id_espera == id_espera, ListaEspera.status == de)
        .values(status=para)
    )
    return r.rowcount == 1


def marcar_chamado(id_espera):
    return mudar_status(id_espera, "aguardando", "chamado")


def entrada(id_espera):
    """Entrada com cliente, telefone (dígitos), serviço e barbeiro (None na fila por horário), ou None."""
    linha = db.session.execute(
        select(ListaEspera.id_espera, ListaEspera.status, ListaEspera.servico_id,
               ListaEspera.barbeiro_id, ListaEspera.data_desejada, ListaEspera.hora_desejada,
               Cliente.nome.label("cliente"), Cliente.telefone,
               Servico.nome.label("servico_nome"), Servico.duracao_min.label("servico_duracao"),
               Barbeiro.nome.label("barbeiro"))
        .join(Cliente, ListaEspera.cliente_id == Cliente.id_cliente)
        .join(Servico, ListaEspera.servico_id == Servico.id_servico)
        .outerjoin(Barbeiro, ListaEspera.barbeiro_id == Barbeiro.id_barbeiro)
        .where(ListaEspera.id_espera == id_espera)
    ).first()
    return dict(linha._mapping) if linha else None
