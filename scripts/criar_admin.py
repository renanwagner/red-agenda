"""Cria o administrador do painel (primeiro acesso). A senha é digitada sem eco e só o hash é gravado.

Uso: python scripts/criar_admin.py   (usa DATABASE_URL; rode antes scripts/criar_banco.py)
"""
import getpass
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.services.autenticacao import SENHA_MINIMA, EmailEmUso, criar_administrador  # noqa: E402


def _pedir_senha(pedir_senha):
    while True:
        senha = pedir_senha("Senha (mínimo 10 caracteres): ")
        if len(senha) < SENHA_MINIMA:
            print(f"A senha precisa ter pelo menos {SENHA_MINIMA} caracteres.")
            continue
        if pedir_senha("Repita a senha: ") != senha:
            print("As senhas não conferem.")
            continue
        return senha


def main(url=None, entrada=input, pedir_senha=getpass.getpass):
    config = {"SECRET_KEY": os.environ.get("SECRET_KEY") or secrets.token_hex(16)}  # o script não atende requisições
    if url:
        config["SQLALCHEMY_DATABASE_URI"] = url
    app = create_app(config)
    nome = entrada("Nome: ").strip()
    email = entrada("E-mail: ").strip()
    senha = _pedir_senha(pedir_senha)
    with app.app_context():
        try:
            criar_administrador(nome, email, senha)
        except EmailEmUso:
            print("Este e-mail já está em uso. Nada foi criado.")
            return app
    print(f"Administrador criado: {email.lower()}")
    return app


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # acentos no terminal do Windows
    main()
