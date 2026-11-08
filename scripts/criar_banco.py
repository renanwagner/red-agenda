"""Cria as tabelas e carrega os 7 serviços. Repetível: não duplica nem sobrescreve dados.

Uso: python scripts/criar_banco.py [--demo]   (usa DATABASE_URL; sem ela, sqlite:///red_agenda.db)
  --demo  carrega também barbeiros, janelas e agendamentos FICTÍCIOS (protótipo e validação)
"""
import argparse
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.models import db  # noqa: E402
from app.repositories.demo import carregar_demo  # noqa: E402
from app.repositories.servicos import carregar_servicos_iniciais  # noqa: E402


def criar_banco(url=None, demo=False):
    config = {"SECRET_KEY": os.environ.get("SECRET_KEY") or secrets.token_hex(16)}  # chave descartável: o script não atende requisições
    if url:
        config["SQLALCHEMY_DATABASE_URI"] = url
    app = create_app(config)
    with app.app_context():
        db.create_all()
        criados = carregar_servicos_iniciais()
        if demo:
            carregar_demo()
    print(f"Banco pronto. Serviços criados agora: {criados}.")
    if demo:
        print("Dados de demonstração carregados (fictícios).")
    return app


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # acentos no terminal do Windows
    parser = argparse.ArgumentParser(description="Cria as tabelas e carrega os 7 serviços.")
    parser.add_argument("--demo", action="store_true", help="carrega dados fictícios de demonstração")
    criar_banco(demo=parser.parse_args().demo)
