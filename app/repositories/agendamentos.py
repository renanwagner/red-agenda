"""Gravação (RF02) e cancelamento (RF05) de agendamentos."""
from sqlalchemy import select, update

from app.models import Agendamento, Barbeiro, Cliente, Servico, db
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


def obter(id_agendamento, travar=False):
    """Agendamento com cliente e serviço, ou None. `travar`: trava a linha até o fim da transação
    (FOR UPDATE no PostgreSQL; no SQLite a trava é o BEGIN IMMEDIATE)."""
    consulta = (
        select(Agendamento.id_agendamento, Agendamento.barbeiro_id, Agendamento.servico_id,
               Agendamento.inicio, Agendamento.fim, Agendamento.status,
               Cliente.nome.label("cliente"), Cliente.telefone,
               Servico.nome.label("servico_nome"), Servico.duracao_min.label("servico_duracao"))
        .join(Cliente, Agendamento.cliente_id == Cliente.id_cliente)
        .join(Servico, Agendamento.servico_id == Servico.id_servico)
        .where(Agendamento.id_agendamento == id_agendamento)
    )
    if travar:
        consulta = consulta.with_for_update(of=Agendamento)
    linha = db.session.execute(consulta).first()
    return dict(linha._mapping) if linha else None


def cancelar(id_agendamento):
    """confirmado → cancelado (não apaga). Devolve False se não estava mais confirmado."""
    r = db.session.execute(
        update(Agendamento)
        .where(Agendamento.id_agendamento == id_agendamento, Agendamento.status == "confirmado")
        .values(status="cancelado")
    )
    return r.rowcount == 1
