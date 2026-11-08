"""Dados de demonstração (--demo): reproduzem a tabela do protótipo e são repetíveis."""
from datetime import date, time

from sqlalchemy import func, select

from app.models import Agendamento, Barbeiro, JanelaAtendimento
from app.repositories.demo import DIAS_DEMO, carregar_demo
from app.repositories.servicos import carregar_servicos_iniciais
from app.services.consulta_disponibilidade import barbeiros_livres_no_horario, horarios_do_dia

DIA = date(2026, 11, 14)
CORTE_BARBA = 2  # 45 min


def _carrega(db):
    carregar_servicos_iniciais()
    carregar_demo()


def test_tabela_do_prototipo_para_corte_e_barba(banco):
    _carrega(banco)
    esperado = {"09:30": [2], "10:00": [2, 3], "10:30": [3], "11:00": []}
    assert horarios_do_dia(DIA) == list(esperado)
    for hora, livres in esperado.items():
        assert barbeiros_livres_no_horario(CORTE_BARBA, DIA, time.fromisoformat(hora)) == livres, hora


def test_mesmo_padrao_em_outra_data_do_periodo(banco):
    _carrega(banco)
    assert horarios_do_dia(date(2026, 11, 21)) == ["09:30", "10:00", "10:30", "11:00"]
    assert barbeiros_livres_no_horario(CORTE_BARBA, date(2026, 11, 21), time(10)) == [2, 3]


def test_repetir_nao_duplica(banco):
    _carrega(banco)
    carregar_demo()
    assert banco.session.scalar(select(func.count()).select_from(Barbeiro)) == 3
    assert banco.session.scalar(select(func.count()).select_from(JanelaAtendimento)) == 3 * DIAS_DEMO
    assert banco.session.scalar(select(func.count()).select_from(Agendamento)) == 6 * DIAS_DEMO


def test_senha_dos_barbeiros_demo_so_como_hash_scrypt(banco):
    _carrega(banco)
    for b in banco.session.scalars(select(Barbeiro)):
        assert b.senha_hash.startswith("scrypt:")
