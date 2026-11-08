"""RF06: agenda do dia e da semana (só confirmados, do barbeiro pedido, em ordem de horário)."""
from datetime import date, datetime, time, timedelta

import pytest

from app.models import Agendamento, Barbeiro, Cliente, Servico
from app.services import agenda_painel

SABADO = date(2026, 11, 14)


def em(dia, hora, minuto=0):
    return datetime.combine(dia, time(hora, minuto))


@pytest.fixture
def base(banco):
    """Dois barbeiros, dois clientes e um serviço fictícios."""
    b1 = Barbeiro(nome="Barbeiro 1", email="b1@exemplo.com", senha_hash="x", papel="barbeiro")
    b2 = Barbeiro(nome="Barbeiro 2", email="b2@exemplo.com", senha_hash="x", papel="barbeiro")
    c1 = Cliente(nome="Cliente Um", telefone="51900000001")
    c2 = Cliente(nome="Cliente Dois", telefone="5132000000")
    corte = Servico(nome="Corte", duracao_min=30)
    banco.session.add_all([b1, b2, c1, c2, corte])
    banco.session.commit()
    return {"b1": b1.id_barbeiro, "b2": b2.id_barbeiro, "c1": c1.id_cliente, "c2": c2.id_cliente,
            "corte": corte.id_servico}


def _agendar(banco, base, inicio, barbeiro="b1", cliente="c1", status="confirmado"):
    banco.session.add(Agendamento(cliente_id=base[cliente], barbeiro_id=base[barbeiro], servico_id=base["corte"],
                                  inicio=inicio, fim=inicio + timedelta(minutes=30), status=status, origem="link"))
    banco.session.commit()


def _horas(itens):
    return [i["inicio"].strftime("%H:%M") for i in itens]


# ---------- regras puras ----------

def test_semana_vai_de_segunda_a_domingo():
    assert agenda_painel.semana_de(SABADO) == (date(2026, 11, 9), date(2026, 11, 15))
    assert agenda_painel.semana_de(date(2026, 11, 9)) == (date(2026, 11, 9), date(2026, 11, 15))
    assert agenda_painel.semana_de(date(2026, 11, 15)) == (date(2026, 11, 9), date(2026, 11, 15))


def test_semana_que_atravessa_o_mes():
    assert agenda_painel.semana_de(date(2026, 12, 2)) == (date(2026, 11, 30), date(2026, 12, 6))


@pytest.mark.parametrize("digitos, texto", [("51900000001", "51 90000-0001"), ("5132000000", "51 3200-0000"),
                                            ("123", "123")])
def test_telefone_formatado(digitos, texto):
    assert agenda_painel.telefone_txt(digitos) == texto


# ---------- com banco ----------

def test_dia_mostra_confirmados_do_barbeiro_em_ordem_sem_cancelado(banco, base):
    """Cenário do RF06: 5 confirmados e 1 cancelado."""
    for hora, minuto in [(11, 0), (9, 0), (10, 30), (9, 30), (10, 0)]:
        _agendar(banco, base, em(SABADO, hora, minuto))
    _agendar(banco, base, em(SABADO, 11, 30), status="cancelado")

    itens = agenda_painel.do_dia(base["b1"], SABADO)

    assert _horas(itens) == ["09:00", "09:30", "10:00", "10:30", "11:00"]
    primeiro = itens[0]
    assert primeiro["fim"] == em(SABADO, 9, 30)
    assert primeiro["cliente"] == "Cliente Um"
    assert primeiro["telefone"] == "51 90000-0001"
    assert primeiro["servico"] == {"nome": "Corte", "duracao_min": 30}


def test_dia_nao_mostra_outro_barbeiro_nem_concluido(banco, base):
    _agendar(banco, base, em(SABADO, 9), barbeiro="b2", cliente="c2")
    _agendar(banco, base, em(SABADO, 10), status="concluido")
    assert agenda_painel.do_dia(base["b1"], SABADO) == []
    assert [i["cliente"] for i in agenda_painel.do_dia(base["b2"], SABADO)] == ["Cliente Dois"]


def test_limites_do_dia(banco, base):
    _agendar(banco, base, em(SABADO, 0))
    _agendar(banco, base, em(SABADO, 23, 59))
    _agendar(banco, base, em(SABADO + timedelta(days=1), 0))
    _agendar(banco, base, em(SABADO - timedelta(days=1), 23, 59))
    assert _horas(agenda_painel.do_dia(base["b1"], SABADO)) == ["00:00", "23:59"]


def test_semana_agrupa_por_dia_so_dias_com_agendamento(banco, base):
    _agendar(banco, base, em(SABADO, 10))
    _agendar(banco, base, em(SABADO, 9))
    _agendar(banco, base, em(date(2026, 11, 10), 15))
    _agendar(banco, base, em(date(2026, 11, 12), 9), status="cancelado")       # dia só com cancelado: some
    _agendar(banco, base, em(date(2026, 11, 15), 23, 59))                      # domingo, último minuto: entra
    _agendar(banco, base, em(date(2026, 11, 16), 0))                           # segunda seguinte: fora
    _agendar(banco, base, em(date(2026, 11, 8), 23, 59))                       # domingo anterior: fora

    dias = agenda_painel.da_semana(base["b1"], SABADO)

    assert [d["data"] for d in dias] == [date(2026, 11, 10), SABADO, date(2026, 11, 15)]
    assert _horas(dias[1]["itens"]) == ["09:00", "10:00"]


def test_semana_vazia(banco, base):
    assert agenda_painel.da_semana(base["b1"], SABADO) == []
