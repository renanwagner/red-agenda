"""Dados fictícios do protótipo. Só dados, sem regra de negócio."""
from datetime import date

# Os sete serviços com as durações de docs/03-modelo-dados.md
SERVICOS = (
    {"id_servico": 1, "nome": "Corte", "duracao_min": 30},
    {"id_servico": 2, "nome": "Corte + barba", "duracao_min": 45},
    {"id_servico": 3, "nome": "Corte infantil", "duracao_min": 45},
    {"id_servico": 4, "nome": "Barba", "duracao_min": 15},
    {"id_servico": 5, "nome": "Sobrancelha", "duracao_min": 10},
    {"id_servico": 6, "nome": "Corte na zero", "duracao_min": 15},
    {"id_servico": 7, "nome": "Zero + barba", "duracao_min": 30},
)

BARBEIROS = (
    {"id_barbeiro": 1, "nome": "Barbeiro 1"},
    {"id_barbeiro": 2, "nome": "Barbeiro 2"},
    {"id_barbeiro": 3, "nome": "Barbeiro 3"},
)

# Valor da opção "Qualquer barbeiro" (padrão da Tela 1)
QUALQUER = "qualquer"
NOME_QUALQUER = "Qualquer barbeiro"

HORARIOS = ("09:30", "10:00", "10:30", "11:00")

# Barbeiros livres em cada horário (ids), iguais para qualquer data no protótipo
DISPONIBILIDADE = {
    "09:30": (2,),
    "10:00": (2, 3),
    "10:30": (3,),
    "11:00": (),
}

DATA_PADRAO = date(2026, 11, 14)  # sábado

# Usado só como placeholder de exemplo
CLIENTE_EXEMPLO = {"nome": "Cliente Exemplo", "telefone": "51 90000-0000"}
