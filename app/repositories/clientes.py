"""Repositório de clientes: telefone único (só dígitos com DDD)."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Cliente, db


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
