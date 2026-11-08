"""Gravação de agendamentos (RF02). Controle da transação fica aqui, na persistência."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Agendamento, Barbeiro, Cliente, db


def nova_transacao():
    """Encerra leituras anteriores da requisição para a gravação começar numa transação nova."""
    db.session.rollback()


def travar_barbeiro_ativo(id_barbeiro):
    """Trava a linha do barbeiro até o fim da transação (FOR UPDATE no PostgreSQL; no SQLite a
    trava é o BEGIN IMMEDIATE). Devolve False se o barbeiro não existe ou está inativo."""
    encontrado = db.session.scalar(
        select(Barbeiro.id_barbeiro)
        .where(Barbeiro.id_barbeiro == id_barbeiro, Barbeiro.ativo.is_(True))
        .with_for_update()
    )
    return encontrado is not None


def obter_ou_criar_cliente(nome, telefone):
    """Id do cliente com esse telefone; cria se não existe. O nome de um cliente existente não muda."""
    existente = db.session.scalar(select(Cliente.id_cliente).where(Cliente.telefone == telefone))
    if existente is not None:
        return existente
    try:
        with db.session.begin_nested():   # outro pedido pode ter criado o mesmo telefone agora
            cliente = Cliente(nome=nome, telefone=telefone)
            db.session.add(cliente)
        return cliente.id_cliente
    except IntegrityError:
        return db.session.scalar(select(Cliente.id_cliente).where(Cliente.telefone == telefone))


def criar_agendamento(cliente_id, barbeiro_id, servico_id, inicio, fim):
    agendamento = Agendamento(cliente_id=cliente_id, barbeiro_id=barbeiro_id, servico_id=servico_id,
                              inicio=inicio, fim=fim, status="confirmado", origem="link")
    db.session.add(agendamento)
    db.session.flush()
    return agendamento.id_agendamento


def confirmar_transacao():
    db.session.commit()


def desfazer_transacao():
    db.session.rollback()
