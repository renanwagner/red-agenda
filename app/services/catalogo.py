"""Catálogo público da Tela 1: serviços e barbeiros ativos."""
from app.repositories import barbeiros as repo_barbeiros
from app.repositories import servicos as repo_servicos


def servicos_ativos():
    return repo_servicos.servicos_ativos()


def barbeiros_ativos():
    return repo_barbeiros.barbeiros_ativos()
