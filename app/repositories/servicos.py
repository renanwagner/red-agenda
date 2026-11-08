"""Repositório de serviços (docs/03: valores iniciais)."""
from sqlalchemy import select

from app.models import Servico, db

SERVICOS_INICIAIS = (
    ("Corte", 30),
    ("Corte + barba", 45),
    ("Corte infantil", 45),
    ("Barba", 15),
    ("Sobrancelha", 10),
    ("Corte na zero", 15),
    ("Zero + barba", 30),
)


def carregar_servicos_iniciais():
    """Cria os serviços que faltam, sem duplicar nem sobrescrever os existentes. Devolve quantos criou."""
    existentes = set(db.session.scalars(select(Servico.nome)))
    novos = [Servico(nome=n, duracao_min=d) for n, d in SERVICOS_INICIAIS if n not in existentes]
    db.session.add_all(novos)
    db.session.commit()
    return len(novos)
