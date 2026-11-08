"""RF07: janelas de atendimento (abertas e bloqueadas) e a proteção dos agendamentos confirmados."""
from datetime import date, datetime, time

import pytest

from app.models import Agendamento, Barbeiro, Cliente, JanelaAtendimento, Servico
from app.services import janelas
from app.services.consulta_disponibilidade import barbeiros_livres_no_horario, horarios_do_dia

DIA = date(2026, 11, 14)


def h(hora, minuto=0):
    return datetime.combine(DIA, time(hora, minuto))


# ---------- regra pura ----------

def _v(propostas, agendamentos=()):
    return janelas.validar_dia(propostas, list(agendamentos))


def test_fim_precisa_ser_depois_do_inicio():
    assert _v([(h(10), h(10), "aberto")]) == "fim_antes"
    assert _v([(h(10), h(9), "bloqueado")]) == "fim_antes"


def test_mesmo_tipo_nao_se_sobrepoe_mas_encostado_e_tipos_diferentes_podem():
    assert _v([(h(9), h(11), "aberto"), (h(10), h(12), "aberto")]) == "sobreposta"
    assert _v([(h(9), h(10), "aberto"), (h(10), h(11), "aberto")]) is None
    assert _v([(h(9), h(12), "aberto"), (h(10), h(10, 30), "bloqueado")]) is None


def test_agendamento_confirmado_nao_pode_ficar_fora_do_atendimento():
    ag = [(h(10), h(10, 30))]
    assert _v([(h(9), h(12), "aberto")], ag) is None
    assert _v([(h(9), h(10, 15), "aberto")], ag) == "agendamento_fora"            # encolher
    assert _v([], ag) == "agendamento_fora"                                         # excluir
    assert _v([(h(9), h(12), "aberto"), (h(10, 15), h(11), "bloqueado")], ag) == "agendamento_fora"
    assert _v([(h(9), h(10), "aberto"), (h(10), h(11), "aberto")], ag) is None     # janelas encostadas


# ---------- com o banco ----------

@pytest.fixture
def cenario(banco):
    b1 = Barbeiro(nome="Barbeiro 1", email="b1@exemplo.com", senha_hash="h", papel="barbeiro")
    b2 = Barbeiro(nome="Barbeiro 2", email="b2@exemplo.com", senha_hash="h", papel="barbeiro")
    s = Servico(nome="Corte", duracao_min=30)
    c = Cliente(nome="Cliente Exemplo", telefone="51900000000")
    banco.session.add_all([b1, b2, s, c])
    banco.session.flush()
    ids = {"b1": b1.id_barbeiro, "b2": b2.id_barbeiro, "servico": s.id_servico, "cliente": c.id_cliente}
    banco.session.commit()
    return ids


def _salva(c, ini, fim, tipo="aberto", barbeiro="b1", id_janela=None):
    return janelas.salvar(c[barbeiro], DIA, ini, fim, tipo, id_janela=id_janela)


def _agenda(db, c, ini, status="confirmado"):
    db.session.add(Agendamento(cliente_id=c["cliente"], barbeiro_id=c["b1"], servico_id=c["servico"],
                               inicio=h(*ini), fim=h(ini[0], ini[1] + 30), status=status, origem="painel"))
    db.session.commit()


def test_rf07_janela_criada_aparece_na_disponibilidade(cenario):
    r = _salva(cenario, time(9), time(12))
    assert r.ok and r.erro is None
    assert horarios_do_dia(DIA)[:2] == ["09:00", "09:30"] and horarios_do_dia(DIA)[-1] == "11:30"
    assert barbeiros_livres_no_horario(cenario["servico"], DIA, time(9)) == [cenario["b1"]]


def test_listar_em_ordem_e_so_do_barbeiro(cenario):
    _salva(cenario, time(14), time(18))
    _salva(cenario, time(9), time(12))
    _salva(cenario, time(10), time(11), tipo="bloqueado")
    _salva(cenario, time(9), time(12), barbeiro="b2")
    lista = janelas.listar(cenario["b1"], DIA)
    assert [(j["hora_inicio"], j["tipo"]) for j in lista] == [
        (time(9), "aberto"), (time(10), "bloqueado"), (time(14), "aberto")]


def test_rf07_sobreposta_do_mesmo_tipo_e_recusada(cenario):
    _salva(cenario, time(9), time(12))
    r = _salva(cenario, time(11), time(13))
    assert not r.ok and r.erro == "sobreposta"
    assert len(janelas.listar(cenario["b1"], DIA)) == 1
    assert _salva(cenario, time(12), time(13)).ok      # encostada é aceita
    assert _salva(cenario, time(9), time(13), barbeiro="b2").ok   # outro barbeiro não conflita


def test_rf07_excluir_com_agendamento_confirmado_e_bloqueado(banco, cenario):
    id_janela = _salva(cenario, time(9), time(12)).id_janela
    _agenda(banco, cenario, (10, 0))
    r = janelas.excluir(cenario["b1"], id_janela)
    assert not r.ok and r.erro == "agendamento_fora"
    assert banco.session.get(JanelaAtendimento, id_janela) is not None


def test_excluir_sem_agendamento_ou_com_cancelado(banco, cenario):
    id_janela = _salva(cenario, time(9), time(12)).id_janela
    _agenda(banco, cenario, (10, 0), status="cancelado")
    assert janelas.excluir(cenario["b1"], id_janela).ok
    assert janelas.listar(cenario["b1"], DIA) == []


def test_alterar_encolhendo_sobre_agendamento_e_recusado(banco, cenario):
    id_janela = _salva(cenario, time(9), time(12)).id_janela
    _agenda(banco, cenario, (11, 0))
    r = _salva(cenario, time(9), time(11), id_janela=id_janela)
    assert not r.ok and r.erro == "agendamento_fora"
    r = _salva(cenario, time(8), time(12), id_janela=id_janela)         # alterar sem conflito
    assert r.ok and janelas.listar(cenario["b1"], DIA)[0]["hora_inicio"] == time(8)


def test_bloqueio_sobre_agendamento_e_recusado(banco, cenario):
    _salva(cenario, time(9), time(12))
    _agenda(banco, cenario, (10, 0))
    assert _salva(cenario, time(10), time(10, 15), tipo="bloqueado").erro == "agendamento_fora"
    assert _salva(cenario, time(11), time(11, 30), tipo="bloqueado").ok


def test_janela_de_outro_barbeiro_nao_e_encontrada(cenario):
    id_janela = _salva(cenario, time(9), time(12), barbeiro="b2").id_janela
    assert janelas.obter(cenario["b1"], id_janela) is None
    assert janelas.excluir(cenario["b1"], id_janela).erro == "nao_encontrada"
    assert _salva(cenario, time(9), time(10), id_janela=id_janela).erro == "nao_encontrada"
    assert janelas.obter(cenario["b2"], id_janela)["hora_inicio"] == time(9)


def test_tipo_invalido_ou_barbeiro_inexistente(cenario):
    assert _salva(cenario, time(9), time(12), tipo="livre").erro == "tipo"
    assert janelas.salvar(9999, DIA, time(9), time(12), "aberto").erro == "nao_encontrada"


def test_fim_antes_do_inicio_pelo_servico(cenario):
    assert _salva(cenario, time(12), time(9)).erro == "fim_antes"


def test_falha_no_meio_desfaz(banco, cenario, monkeypatch):
    from app.repositories import janelas as repo

    def quebra(*_a, **_k):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(repo, "criar", quebra)
    with pytest.raises(RuntimeError):
        _salva(cenario, time(9), time(12))
    assert janelas.listar(cenario["b1"], DIA) == []


def test_falha_ao_excluir_desfaz(banco, cenario, monkeypatch):
    from app.repositories import janelas as repo

    id_janela = _salva(cenario, time(9), time(12)).id_janela

    def quebra(*_a, **_k):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(repo, "excluir", quebra)
    with pytest.raises(RuntimeError):
        janelas.excluir(cenario["b1"], id_janela)
    assert len(janelas.listar(cenario["b1"], DIA)) == 1
