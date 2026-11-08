"""Repositório de barbeiros. A leitura pública nunca expõe e-mail nem senha_hash."""
from sqlalchemy import select

from app.models import Barbeiro, db


def barbeiros_ativos():
    """Barbeiros ativos em ordem de id, como dicionários (id_barbeiro, nome)."""
    linhas = db.session.execute(
        select(Barbeiro.id_barbeiro, Barbeiro.nome)
        .where(Barbeiro.ativo.is_(True)).order_by(Barbeiro.id_barbeiro)
    )
    return [dict(linha._mapping) for linha in linhas]


def credenciais_por_email(email):
    """Uso interno do login: id, nome, papel, ativo e senha_hash (nunca vai para tela nem log)."""
    linha = db.session.execute(
        select(Barbeiro.id_barbeiro, Barbeiro.nome, Barbeiro.papel, Barbeiro.ativo, Barbeiro.senha_hash)
        .where(Barbeiro.email == email)
    ).first()
    return dict(linha._mapping) if linha else None


def perfil_ativo(id_barbeiro):
    """id, nome e papel do barbeiro ativo, ou None."""
    linha = db.session.execute(
        select(Barbeiro.id_barbeiro, Barbeiro.nome, Barbeiro.papel)
        .where(Barbeiro.id_barbeiro == id_barbeiro, Barbeiro.ativo.is_(True))
    ).first()
    return dict(linha._mapping) if linha else None


def email_em_uso(email):
    return db.session.scalar(select(Barbeiro.id_barbeiro).where(Barbeiro.email == email)) is not None


def criar_barbeiro(nome, email, senha_hash, papel):
    barbeiro = Barbeiro(nome=nome, email=email, senha_hash=senha_hash, papel=papel)
    db.session.add(barbeiro)
    db.session.commit()
    return barbeiro.id_barbeiro
