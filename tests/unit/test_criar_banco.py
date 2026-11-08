"""scripts/criar_banco.py: cria tabelas e carrega os 7 serviços, repetível e sem duplicar."""
from sqlalchemy import select

from app.models import Servico
from scripts import criar_banco

SERVICOS = {
    "Corte": 30, "Corte + barba": 45, "Corte infantil": 45, "Barba": 15,
    "Sobrancelha": 10, "Corte na zero": 15, "Zero + barba": 30,
}


def _servicos(db):
    return {s.nome: s.duracao_min for s in db.session.scalars(select(Servico))}


def test_carrega_os_sete_servicos_com_as_duracoes(tmp_path):
    url = f"sqlite:///{tmp_path / 'novo.db'}"
    app = criar_banco.criar_banco(url)
    with app.app_context():
        from app.models import db
        assert _servicos(db) == SERVICOS


def test_repetir_nao_duplica_nem_sobrescreve(tmp_path):
    url = f"sqlite:///{tmp_path / 'novo.db'}"
    app = criar_banco.criar_banco(url)
    with app.app_context():
        from app.models import db
        servico = db.session.scalar(select(Servico).where(Servico.nome == "Barba"))
        servico.duracao_min = 20
        servico.ativo = False
        db.session.commit()
    app = criar_banco.criar_banco(url)
    with app.app_context():
        from app.models import db
        assert len(_servicos(db)) == 7
        barba = db.session.scalar(select(Servico).where(Servico.nome == "Barba"))
        assert barba.duracao_min == 20 and barba.ativo is False
