"""Repositório de barbeiros (leitura pública: nunca expõe e-mail nem senha_hash)."""
from sqlalchemy import select

from app.models import Barbeiro, db


def barbeiros_ativos():
    """Barbeiros ativos em ordem de id, como dicionários (id_barbeiro, nome)."""
    linhas = db.session.execute(
        select(Barbeiro.id_barbeiro, Barbeiro.nome)
        .where(Barbeiro.ativo.is_(True)).order_by(Barbeiro.id_barbeiro)
    )
    return [dict(linha._mapping) for linha in linhas]
