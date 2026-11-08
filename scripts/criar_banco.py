"""Cria as tabelas e carrega os 7 serviços. Repetível: não duplica nem sobrescreve dados.

Uso: python scripts/criar_banco.py   (usa DATABASE_URL; sem ela, sqlite:///red_agenda.db)
"""
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.models import db  # noqa: E402
from app.repositories.servicos import carregar_servicos_iniciais  # noqa: E402


def criar_banco(url=None):
    config = {"SECRET_KEY": os.environ.get("SECRET_KEY") or secrets.token_hex(16)}  # chave descartável: o script não atende requisições
    if url:
        config["SQLALCHEMY_DATABASE_URI"] = url
    app = create_app(config)
    with app.app_context():
        db.create_all()
        criados = carregar_servicos_iniciais()
    print(f"Banco pronto. Serviços criados agora: {criados}.")
    return app


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # acentos no terminal do Windows
    criar_banco()
