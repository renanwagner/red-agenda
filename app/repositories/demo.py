"""Dados FICTÍCIOS de demonstração (python scripts/criar_banco.py --demo). Repetível, sem duplicar.

Reproduz a tabela do protótipo para "Corte + barba – 45 min" em cada dia do período:
09:30 → Barbeiro 2; 10:00 → Barbeiros 2 e 3; 10:30 → Barbeiro 3; 11:00 → nenhum.
"""
import secrets
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from werkzeug.security import generate_password_hash

from app.models import Agendamento, Barbeiro, Cliente, JanelaAtendimento, Servico, db

INICIO_DEMO = date(2026, 11, 14)  # sábado, data padrão da Tela 1
DIAS_DEMO = 30
JANELA = (time(9, 30), time(11, 30))

# (barbeiro, serviço, início): ocupações que geram a tabela acima
OCUPACOES = (
    (1, "Corte", time(9, 30)), (1, "Corte", time(10)), (1, "Corte", time(10, 30)), (1, "Corte", time(11)),
    (2, "Corte + barba", time(10, 45)),
    (3, "Corte", time(9, 30)),
)


def _barbeiros():
    barbeiros = []
    for n in (1, 2, 3):
        email = f"barbeiro{n}@exemplo.com"
        b = db.session.scalar(select(Barbeiro).where(Barbeiro.email == email))
        if b is None:
            # Senha aleatória descartável: ninguém entra no painel com estes usuários
            b = Barbeiro(nome=f"Barbeiro {n}", email=email, papel="barbeiro",
                         senha_hash=generate_password_hash(secrets.token_urlsafe(16)))
            db.session.add(b)
        barbeiros.append(b)
    db.session.flush()
    return barbeiros


def _cliente():
    telefone = "51900000001"
    c = db.session.scalar(select(Cliente).where(Cliente.telefone == telefone))
    if c is None:
        c = Cliente(nome="Cliente Demonstração", telefone=telefone)
        db.session.add(c)
        db.session.flush()
    return c


def carregar_demo(inicio=INICIO_DEMO, dias=DIAS_DEMO):
    """Cria barbeiros, janelas e agendamentos fictícios que ainda não existem."""
    barbeiros = _barbeiros()
    cliente = _cliente()
    servicos = {s.nome: s for s in db.session.scalars(select(Servico))}
    for d in range(dias):
        dia = inicio + timedelta(days=d)
        for b in barbeiros:
            ja_tem = db.session.scalar(select(JanelaAtendimento.id_janela).where(
                JanelaAtendimento.barbeiro_id == b.id_barbeiro, JanelaAtendimento.data == dia))
            if ja_tem is None:
                db.session.add(JanelaAtendimento(barbeiro_id=b.id_barbeiro, data=dia, tipo="aberto",
                                                 hora_inicio=JANELA[0], hora_fim=JANELA[1]))
        for n, nome_servico, hora in OCUPACOES:
            b, s = barbeiros[n - 1], servicos[nome_servico]
            inicio_ag = datetime.combine(dia, hora)
            ja_tem = db.session.scalar(select(Agendamento.id_agendamento).where(
                Agendamento.barbeiro_id == b.id_barbeiro, Agendamento.inicio == inicio_ag))
            if ja_tem is None:
                db.session.add(Agendamento(
                    cliente_id=cliente.id_cliente, barbeiro_id=b.id_barbeiro, servico_id=s.id_servico,
                    inicio=inicio_ag, fim=inicio_ag + timedelta(minutes=s.duracao_min),
                    status="confirmado", origem="painel"))
    db.session.commit()
