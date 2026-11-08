"""RF01 e RF03: regras de horário livre, sem banco (funções puras)."""
from datetime import date, datetime, time

from app.services.horarios import (
    AgendaDoDia, barbeiro_livre, barbeiros_livres, intervalo, sugestoes,
)

DIA = date(2026, 11, 14)


def h(hora, minuto=0):
    return datetime.combine(DIA, time(hora, minuto))


def test_intervalo_usa_a_duracao_do_servico():
    assert intervalo(DIA, time(9, 30), 45) == (h(9, 30), h(10, 15))


def test_rf01_exemplo_do_documento():
    # Janela aberta 09:00–10:00 e agendamento confirmado 09:00–09:30
    agenda = AgendaDoDia(abertas=[(h(9), h(10))], ocupados=[(h(9), h(9, 30))])
    assert not barbeiro_livre(*intervalo(DIA, time(9, 30), 45), agenda)   # 45 min não cabe
    assert barbeiro_livre(*intervalo(DIA, time(9, 30), 30), agenda)       # 30 min cabe


def test_fora_de_janela_aberta_nao_e_livre():
    agenda = AgendaDoDia(abertas=[(h(9), h(10))])
    assert not barbeiro_livre(h(8, 30), h(9), agenda)
    assert not barbeiro_livre(h(10), h(10, 30), agenda)
    assert not barbeiro_livre(h(9), h(9, 30), AgendaDoDia())   # sem janela, nada livre


def test_bloqueio_impede_mesmo_dentro_da_janela():
    agenda = AgendaDoDia(abertas=[(h(9), h(12))], bloqueadas=[(h(10), h(10, 30))])
    assert not barbeiro_livre(h(9, 45), h(10, 15), agenda)
    assert barbeiro_livre(h(9, 30), h(10), agenda)        # termina quando o bloqueio começa
    assert barbeiro_livre(h(10, 30), h(11), agenda)       # começa quando o bloqueio termina


def test_agendamentos_encostados_nao_se_sobrepoem():
    agenda = AgendaDoDia(abertas=[(h(9), h(12))], ocupados=[(h(10), h(10, 30))])
    assert barbeiro_livre(h(9, 30), h(10), agenda)
    assert barbeiro_livre(h(10, 30), h(11), agenda)
    assert not barbeiro_livre(h(10, 15), h(10, 45), agenda)
    assert not barbeiro_livre(h(9, 45), h(11), agenda)    # engloba o agendamento


def test_janelas_abertas_contiguas_sao_unidas():
    agenda = AgendaDoDia(abertas=[(h(10), h(11)), (h(9), h(10))])
    assert barbeiro_livre(h(9, 30), h(10, 15), agenda)
    separadas = AgendaDoDia(abertas=[(h(9), h(10)), (h(10, 15), h(11))])
    assert not barbeiro_livre(h(9, 30), h(10, 30), separadas)


def test_barbeiros_livres_em_ordem_de_id():
    livre = AgendaDoDia(abertas=[(h(9), h(12))])
    ocupado = AgendaDoDia(abertas=[(h(9), h(12))], ocupados=[(h(10), h(10, 30))])
    agendas = {3: livre, 1: ocupado, 2: livre}
    assert barbeiros_livres(h(10), h(10, 30), agendas) == [2, 3]
    assert barbeiros_livres(h(10), h(10, 30), {}) == []


def test_rf03_sugere_os_outros_livres():
    assert sugestoes(1, [2, 3]) == [2, 3]
    assert sugestoes(2, [2, 3]) == [3]
    assert sugestoes(1, []) == []
