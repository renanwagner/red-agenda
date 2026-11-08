"""RF08 e RNF01: hash scrypt, senha mínima, bloqueio por tentativas e autenticação."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.models import Barbeiro
from app.services.autenticacao import (
    ControleTentativas, SenhaCurta, EmailEmUso, autenticar, barbeiro_da_sessao, criar_administrador,
)

SENHA = "senha-de-teste-1"


class Relogio:
    def __init__(self):
        self.agora = datetime(2026, 11, 14, 9, 0)

    def __call__(self):
        return self.agora

    def avanca(self, **delta):
        self.agora += timedelta(**delta)


# ---------- bloqueio: 5 falhas seguidas por e-mail → 15 min ----------

def test_quatro_falhas_nao_bloqueiam_e_a_quinta_bloqueia():
    c = ControleTentativas(relogio=Relogio())
    for _ in range(4):
        c.registrar_falha("a@exemplo.com")
    assert not c.bloqueado("a@exemplo.com")
    c.registrar_falha("a@exemplo.com")
    assert c.bloqueado("a@exemplo.com")


def test_bloqueio_dura_15_minutos():
    relogio = Relogio()
    c = ControleTentativas(relogio=relogio)
    for _ in range(5):
        c.registrar_falha("a@exemplo.com")
    relogio.avanca(minutes=14, seconds=59)
    assert c.bloqueado("a@exemplo.com")
    relogio.avanca(seconds=1)
    assert not c.bloqueado("a@exemplo.com")
    c.registrar_falha("a@exemplo.com")          # contagem recomeça depois do bloqueio
    assert not c.bloqueado("a@exemplo.com")


def test_sucesso_zera_a_contagem_e_emails_sao_independentes():
    c = ControleTentativas(relogio=Relogio())
    for _ in range(4):
        c.registrar_falha("a@exemplo.com")
    c.registrar_sucesso("a@exemplo.com")
    for _ in range(4):
        c.registrar_falha("a@exemplo.com")
    assert not c.bloqueado("a@exemplo.com")
    for _ in range(5):
        c.registrar_falha("b@exemplo.com")
    assert c.bloqueado("b@exemplo.com") and not c.bloqueado("a@exemplo.com")


def test_email_conta_sem_diferenciar_maiusculas_e_espacos():
    c = ControleTentativas(relogio=Relogio())
    for email in ["A@exemplo.com", " a@EXEMPLO.com", "a@exemplo.com ", "a@exemplo.COM", "a@exemplo.com"]:
        c.registrar_falha(email)
    assert c.bloqueado("A@Exemplo.com")


# ---------- cadastro do administrador ----------

def test_cria_administrador_so_com_hash_scrypt(banco):
    id_barbeiro = criar_administrador("Admin Exemplo", " Admin@Exemplo.com ", SENHA)
    b = banco.session.get(Barbeiro, id_barbeiro)
    assert (b.email, b.papel, b.ativo) == ("admin@exemplo.com", "administrador", True)
    assert b.senha_hash.startswith("scrypt:") and SENHA not in b.senha_hash


def test_senha_com_menos_de_10_caracteres_e_recusada(banco):
    with pytest.raises(SenhaCurta):
        criar_administrador("Admin Exemplo", "admin@exemplo.com", "123456789")
    assert banco.session.scalars(select(Barbeiro)).all() == []


def test_email_ja_usado_e_recusado(banco):
    criar_administrador("Admin Exemplo", "admin@exemplo.com", SENHA)
    with pytest.raises(EmailEmUso):
        criar_administrador("Outro", "ADMIN@exemplo.com", SENHA)


# ---------- autenticação ----------

@pytest.fixture
def admin(banco):
    return criar_administrador("Admin Exemplo", "admin@exemplo.com", SENHA)


def test_login_valido(admin):
    r = autenticar("Admin@Exemplo.com", SENHA, ControleTentativas())
    assert r.status == "ok" and r.barbeiro["id_barbeiro"] == admin
    assert "senha_hash" not in r.barbeiro


@pytest.mark.parametrize("email,senha", [("admin@exemplo.com", "senha-errada-1"),
                                         ("ninguem@exemplo.com", SENHA)])
def test_senha_errada_ou_email_inexistente_dao_o_mesmo_resultado(admin, email, senha):
    r = autenticar(email, senha, ControleTentativas())
    assert r.status == "invalido" and r.barbeiro is None


def test_barbeiro_inativo_e_recusado(banco, admin):
    banco.session.get(Barbeiro, admin).ativo = False
    banco.session.commit()
    assert autenticar("admin@exemplo.com", SENHA, ControleTentativas()).status == "invalido"
    assert barbeiro_da_sessao(admin) is None          # sessão aberta também cai


def test_sexta_tentativa_bloqueada_mesmo_com_senha_correta(admin):
    c = ControleTentativas()
    for _ in range(5):
        assert autenticar("admin@exemplo.com", "senha-errada-1", c).status == "invalido"
    assert autenticar("admin@exemplo.com", SENHA, c).status == "bloqueado"


def test_email_inexistente_tambem_bloqueia(admin):
    c = ControleTentativas()
    for _ in range(5):
        autenticar("ninguem@exemplo.com", SENHA, c)
    assert autenticar("ninguem@exemplo.com", SENHA, c).status == "bloqueado"


def test_barbeiro_da_sessao(admin):
    assert barbeiro_da_sessao(admin) == {"id_barbeiro": admin, "nome": "Admin Exemplo", "papel": "administrador"}
    assert barbeiro_da_sessao(9999) is None
    assert barbeiro_da_sessao("x") is None
