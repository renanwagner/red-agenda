"""Gravação de agendamentos (RF02)."""
from sqlalchemy import select

from app.models import Agendamento, Barbeiro, db
from app.repositories.clientes import obter_ou_criar_cliente  # noqa: F401 (usado pela regra)
from app.repositories.transacao import (  # noqa: F401 (usados pela regra)
    confirmar_transacao, desfazer_transacao, nova_transacao,
)


def travar_barbeiro_ativo(id_barbeiro):
    """Trava a linha do barbeiro até o fim da transação (FOR UPDATE no PostgreSQL; no SQLite a
    trava é o BEGIN IMMEDIATE). Devolve False se o barbeiro não existe ou está inativo."""
    encontrado = db.session.scalar(
        select(Barbeiro.id_barbeiro)
        .where(Barbeiro.id_barbeiro == id_barbeiro, Barbeiro.ativo.is_(True))
        .with_for_update()
    )
    return encontrado is not None


def criar_agendamento(cliente_id, barbeiro_id, servico_id, inicio, fim):
    agendamento = Agendamento(cliente_id=cliente_id, barbeiro_id=barbeiro_id, servico_id=servico_id,
                              inicio=inicio, fim=fim, status="confirmado", origem="link")
    db.session.add(agendamento)
    db.session.flush()
    return agendamento.id_agendamento
