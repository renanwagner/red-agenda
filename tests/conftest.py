import shutil

import pytest

from app import create_app

# Chave fictícia só para teste; cookie Secure desligado porque o cliente de teste usa http
CONFIG_TESTE = {"TESTING": True, "SECRET_KEY": "chave-de-teste", "SESSION_COOKIE_SECURE": False}


def _app_com_banco(caminho):
    return create_app({**CONFIG_TESTE, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{caminho}"})


@pytest.fixture(scope="session")
def _banco_demo_modelo(tmp_path_factory):
    """Monta uma vez por sessão o banco com os 7 serviços e os dados de demonstração."""
    from app.models import db
    from app.repositories.demo import carregar_demo
    from app.repositories.servicos import carregar_servicos_iniciais

    caminho = tmp_path_factory.mktemp("modelo") / "demo.db"
    app = _app_com_banco(caminho)
    with app.app_context():
        db.create_all()
        carregar_servicos_iniciais()
        carregar_demo()
        db.engine.dispose()
    return caminho


@pytest.fixture
def app(tmp_path, _banco_demo_modelo):
    """App com uma cópia própria do banco de demonstração (cada teste isolado)."""
    from app.models import db

    copia = tmp_path / "aceitacao.db"
    shutil.copy(_banco_demo_modelo, copia)
    app = _app_com_banco(copia)
    yield app
    with app.app_context():
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def banco(tmp_path):
    """Banco SQLite temporário vazio, com as tabelas criadas; devolve o `db` dentro do contexto."""
    from app.models import db

    app = _app_com_banco(tmp_path / "teste.db")
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()
