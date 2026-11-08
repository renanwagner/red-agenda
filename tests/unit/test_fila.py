"""RF04 (entrar na fila) e regra de chamada do RF05 (fila do barbeiro antes da fila por horário)."""
from datetime import date, datetime, time

import pytest
from sqlalchemy import func, select

from app.models import Barbeiro, Cliente, ListaEspera, Servico
from app.services.fila import entrar_na_fila, escolher_proximo

DIA = date(2026, 11, 14)
TEL = "51 90000-0000"


@pytest.fixture
def cenario(banco):
    b1 = Barbeiro(nome="Barbeiro 1", email="b1@exemplo.com", senha_hash="h", papel="barbeiro")
    b2 = Barbeiro(nome="Barbeiro 2", email="b2@exemplo.com", senha_hash="h", papel="barbeiro")
    corte = Servico(nome="Corte", duracao_min=30)
    banco.session.add_all([b1, b2, corte])
    banco.session.flush()
    ids = {"b1": b1.id_barbeiro, "b2": b2.id_barbeiro, "corte": corte.id_servico}
    banco.session.commit()
    return ids


def _entra(c, barbeiro="b1", hora=time(10), telefone=TEL, servico="corte"):
    id_barbeiro = c[barbeiro] if barbeiro else None
    return entrar_na_fila(c[servico], id_barbeiro, DIA, hora, "Cliente Exemplo", telefone)


def _entradas(db):
    return db.session.scalars(select(ListaEspera).order_by(ListaEspera.id_espera)).all()


# ---------- RF04: entrar na fila ----------

def test_fila_do_barbeiro_grava_aguardando_com_hora(banco, cenario):
    r = _entra(cenario)
    assert r.entrou and not r.duplicada
    (e,) = _entradas(banco)
    assert (e.barbeiro_id, e.data_desejada, e.hora_desejada, e.status) == (cenario["b1"], DIA, time(10), "aguardando")
    assert isinstance(e.entrou_em, datetime)
    assert banco.session.get(Cliente, e.cliente_id).telefone == "51900000000"


def test_fila_por_horario_grava_barbeiro_nulo(banco, cenario):
    assert _entra(cenario, barbeiro=None, hora=time(11)).entrou
    (e,) = _entradas(banco)
    assert e.barbeiro_id is None and e.hora_desejada == time(11)


@pytest.mark.parametrize("barbeiro", ["b1", None])
def test_segunda_entrada_igual_e_recusada_como_duplicada(banco, cenario, barbeiro):
    assert _entra(cenario, barbeiro=barbeiro).entrou
    r = _entra(cenario, barbeiro=barbeiro, telefone="(51) 90000-0000")   # mesmo telefone, outro formato
    assert not r.entrou and r.duplicada
    assert len(_entradas(banco)) == 1


def test_outra_hora_ou_outro_barbeiro_ou_outra_fila_e_aceita(banco, cenario):
    assert _entra(cenario).entrou
    assert _entra(cenario, hora=time(10, 30)).entrou
    assert _entra(cenario, barbeiro="b2").entrou
    assert _entra(cenario, barbeiro=None).entrou
    assert len(_entradas(banco)) == 4
    assert banco.session.scalar(select(func.count()).select_from(Cliente)) == 1   # mesmo cliente


def test_depois_de_chamado_pode_entrar_de_novo(banco, cenario):
    _entra(cenario)
    _entradas(banco)[0].status = "chamado"
    banco.session.commit()
    assert _entra(cenario).entrou


def test_servico_ou_barbeiro_inativo_ou_inexistente_e_recusado(banco, cenario):
    banco.session.get(Barbeiro, cenario["b1"]).ativo = False
    banco.session.commit()
    r = _entra(cenario)
    assert not r.entrou and not r.duplicada
    assert not entrar_na_fila(9999, None, DIA, time(10), "Cliente Exemplo", TEL).entrou
    assert _entradas(banco) == []
    assert banco.session.scalar(select(func.count()).select_from(Cliente)) == 0


def test_falha_no_meio_desfaz_tudo(banco, cenario, monkeypatch):
    from app.repositories import fila as repo

    def quebra(*_args):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(repo, "criar_entrada", quebra)
    with pytest.raises(RuntimeError):
        _entra(cenario)
    assert banco.session.scalar(select(func.count()).select_from(Cliente)) == 0


# ---------- RF05: regra de chamada (função pura) ----------

def _e(id_espera, barbeiro_id, minuto, hora=time(10), servico_id=1):
    return {"id_espera": id_espera, "barbeiro_id": barbeiro_id, "servico_id": servico_id,
            "hora_desejada": hora, "entrou_em": datetime(2026, 11, 10, 8, minuto)}


def _proximo(entradas, cabe=True):
    return escolher_proximo(entradas, id_servico=1, id_barbeiro=2, hora=time(10), cabe=cabe)


def test_chamada_prefere_a_fila_do_barbeiro_mesmo_que_entrou_depois():
    entradas = [_e(1, None, 0), _e(2, 2, 30)]
    assert _proximo(entradas) == 2


def test_chamada_dentro_da_fila_por_ordem_de_entrada():
    assert _proximo([_e(1, 2, 30), _e(2, 2, 10), _e(3, 2, 20)]) == 2
    assert _proximo([_e(1, None, 30), _e(2, None, 10)]) == 2


def test_sem_fila_do_barbeiro_chama_a_fila_por_horario():
    entradas = [_e(1, 3, 0), _e(2, None, 20)]   # fila de outro barbeiro não conta
    assert _proximo(entradas) == 2


def test_chamada_ignora_outra_hora_e_outro_servico():
    entradas = [_e(1, 2, 0, hora=time(10, 30)), _e(2, None, 0, servico_id=9), _e(3, None, 50)]
    assert _proximo(entradas) == 3


def test_chamada_sem_compativel_ou_sem_caber_devolve_none():
    assert _proximo([]) is None
    assert _proximo([_e(1, 2, 0)], cabe=False) is None
