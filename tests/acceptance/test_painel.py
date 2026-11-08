"""RF08 e RNF01 pelo navegador: login, mensagem única, bloqueio, sessão de 8 h, sair e autorização."""
import re
from datetime import timedelta

import pytest
from flask_login import login_required

from app.models import Barbeiro, db
from app.services.autenticacao import criar_administrador
from app.web.painel import exige_administrador

SENHA = "senha-de-teste-1"
ERRO = "E-mail ou senha incorretos. Confira e tente novamente."
BLOQUEIO = "Muitas tentativas. Tente novamente em 15 minutos."


@pytest.fixture
def admin(app):
    with app.app_context():
        return criar_administrador("Admin Exemplo", "admin@exemplo.com", SENHA)


def _html(resp):
    return resp.get_data(as_text=True)


def _entrar(client, email="admin@exemplo.com", senha=SENHA, url="/painel/entrar"):
    token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', _html(client.get(url))).group(1)
    return client.post(url, data={"email": email, "senha": senha, "csrf_token": token})


def _token_da_pagina(client, url):
    return re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', _html(client.get(url))).group(1)


def test_painel_sem_login_redireciona_para_entrar(client):
    resp = client.get("/painel")
    assert resp.status_code == 302 and resp.headers["Location"].startswith("/painel/entrar")


def test_tela_de_entrada_textos_rotulos_e_cabecalhos(client):
    resp = client.get("/painel/entrar")
    html = _html(resp)
    for texto in ["<h1>Entrar no painel</h1>", "RED Barbearia – área do barbeiro", ">Entrar</button>"]:
        assert texto in html, texto
    assert '<label class="rotulo" for="email">E-mail</label>' in html
    assert '<label class="rotulo" for="senha">Senha</label>' in html
    assert 'type="password"' in html
    assert resp.headers["Content-Security-Policy"] == "default-src 'self'"
    assert resp.headers["X-Frame-Options"] == "DENY"


def test_login_valido_abre_o_painel(client, admin):
    resp = _entrar(client)
    assert resp.status_code == 302 and resp.headers["Location"] == "/painel"
    html = _html(client.get("/painel"))
    assert "<h1>Painel – Admin Exemplo</h1>" in html and ">Sair</button>" in html


def test_login_ignora_next_externo(client, admin):
    resp = _entrar(client, url="/painel/entrar?next=https://exemplo.invalid/")
    assert resp.headers["Location"] == "/painel"


@pytest.mark.parametrize("email,senha", [("admin@exemplo.com", "senha-errada-1"), ("ninguem@exemplo.com", SENHA)])
def test_erro_unico_para_email_ou_senha(client, admin, email, senha):
    resp = _entrar(client, email=email, senha=senha)
    html = _html(resp)
    assert resp.status_code == 200 and ERRO in html
    assert 'aria-live="assertive"' in html and 'class="icone"' in html
    assert senha not in html


def test_campos_vazios(client):
    html = _html(_entrar(client, email="", senha=""))
    assert "Informe o e-mail." in html and "Informe a senha." in html


def test_sexta_tentativa_bloqueada_mesmo_com_senha_correta(client, admin):
    for _ in range(5):
        assert ERRO in _html(_entrar(client, senha="senha-errada-1"))
    html = _html(_entrar(client))
    assert BLOQUEIO in html and ERRO not in html
    assert client.get("/painel").status_code == 302      # não entrou


def test_barbeiro_inativo_e_recusado(app, client, admin):
    with app.app_context():
        db.session.get(Barbeiro, admin).ativo = False
        db.session.commit()
    assert ERRO in _html(_entrar(client))


def test_sair_encerra_a_sessao_so_por_post(client, admin):
    _entrar(client)
    assert client.get("/painel/sair").status_code == 405
    token = _token_da_pagina(client, "/painel")
    resp = client.post("/painel/sair", data={"csrf_token": token})
    assert resp.status_code == 302 and resp.headers["Location"] == "/painel/entrar"
    assert client.get("/painel").status_code == 302


def test_sair_sem_csrf_400(client, admin):
    _entrar(client)
    assert client.post("/painel/sair").status_code == 400


def test_entrar_sem_csrf_400(client, admin):
    assert client.post("/painel/entrar", data={"email": "admin@exemplo.com", "senha": SENHA}).status_code == 400


def test_sessao_expira_em_8_horas_e_cookie_seguro(app, client, admin):
    assert app.config["PERMANENT_SESSION_LIFETIME"] == timedelta(hours=8)
    assert app.config["SESSION_COOKIE_HTTPONLY"] and app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    _entrar(client)
    with client.session_transaction() as sessao:
        assert sessao.permanent                      # vale o limite de 8 h
        assert SENHA not in str(dict(sessao))
    assert client.get_cookie("session").expires is not None


def test_barbeiro_comum_recebe_403_em_rota_de_administrador(app, client):
    @app.route("/painel/teste-admin")
    @login_required
    @exige_administrador
    def so_admin():
        return "ok"

    with app.app_context():
        criar_administrador("Admin Exemplo", "admin@exemplo.com", SENHA)
        comum = db.session.get(Barbeiro, 1)          # Barbeiro 1 da demonstração: papel barbeiro
        from werkzeug.security import generate_password_hash
        comum.senha_hash = generate_password_hash(SENHA)
        email_comum = comum.email
        db.session.commit()

    assert client.get("/painel/teste-admin").status_code == 302          # sem login
    _entrar(client, email=email_comum)
    resp = client.get("/painel/teste-admin")
    assert resp.status_code == 403 and "Acesso não permitido." in _html(resp)
    token = _token_da_pagina(client, "/painel")
    client.post("/painel/sair", data={"csrf_token": token})
    _entrar(client)
    assert client.get("/painel/teste-admin").status_code == 200
