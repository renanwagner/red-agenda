"""Entidades SQLAlchemy (docs/03-modelo-dados.md). Única definição das seis tabelas."""
from datetime import date, datetime, time

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    CheckConstraint, ForeignKey, Index, String, event, func, text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def _ativa_chaves_estrangeiras_no_sqlite(conexao, _registro):
    # O SQLite ignora chaves estrangeiras por padrão; o PostgreSQL já as aplica
    if conexao.__class__.__module__.startswith("sqlite3"):
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Barbeiro(db.Model):
    __tablename__ = "barbeiro"
    __table_args__ = (
        CheckConstraint("papel IN ('administrador', 'barbeiro')", name="ck_barbeiro_papel"),
    )

    id_barbeiro: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    senha_hash: Mapped[str]  # só o hash scrypt, nunca a senha
    papel: Mapped[str]
    ativo: Mapped[bool] = mapped_column(default=True)


class Cliente(db.Model):
    __tablename__ = "cliente"

    id_cliente: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    telefone: Mapped[str] = mapped_column(String(13), unique=True)  # só dígitos com DDD
    criado_em: Mapped[datetime] = mapped_column(default=datetime.now)


class Servico(db.Model):
    __tablename__ = "servico"
    __table_args__ = (
        CheckConstraint("duracao_min > 0 AND duracao_min % 5 = 0", name="ck_servico_duracao"),
    )

    id_servico: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(60), unique=True)
    duracao_min: Mapped[int]
    ativo: Mapped[bool] = mapped_column(default=True)


class JanelaAtendimento(db.Model):
    __tablename__ = "janela_atendimento"
    __table_args__ = (
        CheckConstraint("hora_fim > hora_inicio", name="ck_janela_horas"),
        CheckConstraint("tipo IN ('aberto', 'bloqueado')", name="ck_janela_tipo"),
        Index("ix_janela_barbeiro_data", "barbeiro_id", "data"),
    )

    id_janela: Mapped[int] = mapped_column(primary_key=True)
    barbeiro_id: Mapped[int] = mapped_column(ForeignKey("barbeiro.id_barbeiro"))
    data: Mapped[date]
    hora_inicio: Mapped[time]
    hora_fim: Mapped[time]
    tipo: Mapped[str]


class Agendamento(db.Model):
    __tablename__ = "agendamento"
    __table_args__ = (
        CheckConstraint("fim > inicio", name="ck_agendamento_fim"),
        CheckConstraint("status IN ('confirmado', 'cancelado', 'concluido')", name="ck_agendamento_status"),
        CheckConstraint("origem IN ('link', 'painel')", name="ck_agendamento_origem"),
        Index("ix_agendamento_barbeiro_inicio", "barbeiro_id", "inicio"),
    )

    id_agendamento: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))
    barbeiro_id: Mapped[int] = mapped_column(ForeignKey("barbeiro.id_barbeiro"))
    servico_id: Mapped[int] = mapped_column(ForeignKey("servico.id_servico"))
    inicio: Mapped[datetime]
    fim: Mapped[datetime]
    status: Mapped[str]
    origem: Mapped[str]
    criado_em: Mapped[datetime] = mapped_column(default=datetime.now)


class ListaEspera(db.Model):
    __tablename__ = "lista_espera"
    __table_args__ = (
        CheckConstraint("status IN ('aguardando', 'chamado', 'atendido', 'desistiu')", name="ck_espera_status"),
        Index("ix_espera_data_hora_status", "data_desejada", "hora_desejada", "status"),
    )

    id_espera: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))
    servico_id: Mapped[int] = mapped_column(ForeignKey("servico.id_servico"))
    # Preenchido = fila do barbeiro; nulo = fila por horário (qualquer barbeiro)
    barbeiro_id: Mapped[int | None] = mapped_column(ForeignKey("barbeiro.id_barbeiro"))
    data_desejada: Mapped[date]
    hora_desejada: Mapped[time]
    entrou_em: Mapped[datetime] = mapped_column(default=datetime.now)
    status: Mapped[str] = mapped_column(default="aguardando")


# Sem duas entradas "aguardando" iguais; o barbeiro nulo conta como um valor (coalesce)
Index(
    "uq_espera_aguardando",
    ListaEspera.cliente_id,
    ListaEspera.servico_id,
    ListaEspera.data_desejada,
    ListaEspera.hora_desejada,
    func.coalesce(ListaEspera.barbeiro_id, 0),
    unique=True,
    sqlite_where=text("status = 'aguardando'"),
    postgresql_where=text("status = 'aguardando'"),
)
