import pytest

from app import create_app


@pytest.fixture
def app():
    # Chave fictícia só para teste; cookie Secure desligado porque o cliente de teste usa http
    return create_app({"TESTING": True, "SECRET_KEY": "chave-de-teste", "SESSION_COOKIE_SECURE": False})


@pytest.fixture
def client(app):
    return app.test_client()
