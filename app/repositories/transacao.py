"""Controle de transação usado pelas gravações (a regra decide; a persistência executa)."""
from app.models import db


def nova_transacao():
    """Encerra leituras anteriores da requisição para a gravação começar numa transação nova."""
    db.session.rollback()


def confirmar_transacao():
    db.session.commit()


def desfazer_transacao():
    db.session.rollback()
