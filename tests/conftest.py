import pytest

from app import create_app


@pytest.fixture
def app():
    # Chave fictícia só para teste; cookie Secure desligado porque o cliente de teste usa http
    return create_app({"TESTING": True, "SECRET_KEY": "chave-de-teste", "SESSION_COOKIE_SECURE": False})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def banco(tmp_path):
    """App com banco SQLite temporário e tabelas criadas; devolve (app, db)."""
    from app.models import db

    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "chave-de-teste",
        "SESSION_COOKIE_SECURE": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'teste.db'}",
    })
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()
