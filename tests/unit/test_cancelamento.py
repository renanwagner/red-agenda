"""RF05: cancelar o agendamento e indicar o próximo compatível da fila (um por vez)."""
from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy import select

from app.models import Agendamento, Barbeiro, Cliente, JanelaAtendimento, ListaEspera, Servico
from app.services import cancelamento

DIA = date(2026, 11, 14)


def em(hora, minuto=0):
    return datetime.combine(DIA, time(hora, minuto))


@pytest.fixture
def c(banco):
    """Barbeiros 1 e 2 com janela 09:00–12:00; Corte (30) e Barba (15); agendamento do Barbeiro 1 às 10:00."""
    b1 = Barbeiro(nome="Barbeiro 1", email="b1@exemplo.com", senha_hash="h", papel="barbeiro")
    b2 = Barbeiro(nome="Barbeiro 2", email="b2@exemplo.com", senha_hash="h", papel="barbeiro")
    corte = Servico(nome="Corte", duracao_min=30)
    barba = Servico(nome="Barba", duracao_min=15)
    clientes = [Cliente(nome=f"Cliente {n}", telefone=f"5190000000{n}") for n in range(5)]
    banco.session.add_all([b1, b2, corte, barba, *clientes])
    banco.session.flush()
    for b in (b1, b2):
        banco.session.add(JanelaAtendimento(barbeiro_id=b.id_barbeiro, data=DIA, hora_inicio=time(9),
                                            hora_fim=time(12), tipo="aberto"))
    ag = Agendamento(cliente_id=clientes[0].id_cliente, barbeiro_id=b1.id_barbeiro, servico_id=corte.id_servico,
                     inicio=em(10), fim=em(10, 30), status="confirmado", origem="link")
    banco.session.add(ag)
    banco.session.commit()
    return {"b1": b1.id_barbeiro, "b2": b2.id_barbeiro, "corte": corte.id_servico, "barba": barba.id_servico,
            "clientes": [x.id_cliente for x in clientes], "ag": ag.id_agendamento, "db": banco}


def _fila(c, cliente, barbeiro, minutos, hora=time(10), servico="corte", status="aguardando"):
    """Entrada da fila; `minutos` define a ordem de chegada (entrou_em)."""
    e = ListaEspera(cliente_id=c["clientes"][cliente], servico_id=c[servico],
                    barbeiro_id=c[barbeiro] if barbeiro else None, data_desejada=DIA, hora_desejada=hora,
                    entrou_em=datetime(2026, 11, 10, 8) + timedelta(minutes=minutos), status=status)
    c["db"].session.add(e)
    c["db"].session.commit()
    return e.id_espera


def _status_fila(c):
    s = c["db"].session
    s.expire_all()
    return {e.id_espera: e.status for e in s.scalars(select(ListaEspera))}


def _status_ag(c, id_ag=None):
    s = c["db"].session
    s.expire_all()
    return s.get(Agendamento, id_ag or c["ag"]).status


# ---------- RF05: cancelar e chamar ----------

def test_fila_do_barbeiro_vem_antes_da_fila_por_horario(c):
    por_horario = _fila(c, 1, None, 0)          # entrou antes
    do_barbeiro = _fila(c, 2, "b1", 10)
    r = cancelamento.cancelar_e_chamar(c["ag"])
    assert r.ok and r.id_espera == do_barbeiro
    assert _status_fila(c) == {por_horario: "aguardando", do_barbeiro: "chamado"}


def test_dentro_da_fila_chama_quem_entrou_primeiro(c):
    tarde = _fila(c, 1, "b1", 20)
    cedo = _fila(c, 2, "b1", 5)
    assert cancelamento.cancelar_e_chamar(c["ag"]).id_espera == cedo
    assert _status_fila(c)[tarde] == "aguardando"


def test_sem_fila_do_barbeiro_chama_a_fila_por_horario(c):
    _fila(c, 1, "b2", 0)                        # fila de outro barbeiro não conta
    por_horario = _fila(c, 2, None, 10)
    assert cancelamento.cancelar_e_chamar(c["ag"]).id_espera == por_horario


def test_agendamento_continua_no_banco_como_cancelado(c):
    cancelamento.cancelar_e_chamar(c["ag"])
    assert _status_ag(c) == "cancelado"


def test_ignora_outro_servico_outra_hora_e_quem_nao_esta_aguardando(c):
    _fila(c, 1, "b1", 0, servico="barba")
    _fila(c, 2, "b1", 1, hora=time(10, 30))
    _fila(c, 3, "b1", 2, status="desistiu")
    r = cancelamento.cancelar_e_chamar(c["ag"])
    assert r.ok and r.id_espera is None
    assert _status_ag(c) == "cancelado"


def test_fila_vazia_cancela_sem_chamar(c):
    r = cancelamento.cancelar_e_chamar(c["ag"])
    assert r.ok and r.id_espera is None and _status_ag(c) == "cancelado"


def test_nao_chama_se_o_servico_nao_cabe_mais_no_bloco(c):
    c["db"].session.add(JanelaAtendimento(barbeiro_id=c["b1"], data=DIA, hora_inicio=time(10, 15),
                                          hora_fim=time(10, 45), tipo="bloqueado"))
    c["db"].session.commit()
    _fila(c, 1, "b1", 0)
    r = cancelamento.cancelar_e_chamar(c["ag"])
    assert r.ok and r.id_espera is None


def test_nao_chama_se_o_servico_foi_inativado(c):
    c["db"].session.get(Servico, c["corte"]).ativo = False
    c["db"].session.commit()
    _fila(c, 1, "b1", 0)
    assert cancelamento.cancelar_e_chamar(c["ag"]).id_espera is None


def test_barbeiro_inativo_cancela_sem_chamar(c):
    c["db"].session.get(Barbeiro, c["b1"]).ativo = False
    c["db"].session.commit()
    _fila(c, 1, None, 0)
    r = cancelamento.cancelar_e_chamar(c["ag"])
    assert r.ok and r.id_espera is None and _status_ag(c) == "cancelado"


def test_ja_cancelado_e_recusado_sem_mudar_nada(c):
    _fila(c, 1, "b1", 0)
    assert cancelamento.cancelar_e_chamar(c["ag"]).ok
    antes = _status_fila(c)
    r = cancelamento.cancelar_e_chamar(c["ag"])
    assert not r.ok and r.erro == "nao_cancelavel"
    assert _status_fila(c) == antes


def test_agendamento_de_outro_barbeiro_e_recusado(c):
    _fila(c, 1, "b1", 0)
    r = cancelamento.cancelar_e_chamar(c["ag"], id_barbeiro=c["b2"])
    assert not r.ok and r.erro == "nao_encontrado"
    assert _status_ag(c) == "confirmado"
    assert set(_status_fila(c).values()) == {"aguardando"}


def test_dono_e_administrador_podem_cancelar(c):
    assert cancelamento.cancelar_e_chamar(c["ag"], id_barbeiro=c["b1"]).ok   # dono
    assert not cancelamento.cancelar_e_chamar(999).ok                       # inexistente


def test_dois_cancelamentos_no_mesmo_horario_nao_chamam_a_mesma_pessoa(c):
    s = c["db"].session
    outro = Agendamento(cliente_id=c["clientes"][4], barbeiro_id=c["b2"], servico_id=c["corte"],
                        inicio=em(10), fim=em(10, 30), status="confirmado", origem="link")
    s.add(outro)
    s.commit()
    primeiro = _fila(c, 1, None, 0)
    segundo = _fila(c, 2, None, 5)
    assert cancelamento.cancelar_e_chamar(c["ag"]).id_espera == primeiro
    assert cancelamento.cancelar_e_chamar(outro.id_agendamento).id_espera == segundo


def test_falha_no_meio_desfaz_tudo(c, monkeypatch):
    _fila(c, 1, "b1", 0)

    def quebra(*_a, **_k):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(cancelamento.repo_fila, "marcar_chamado", quebra)
    with pytest.raises(RuntimeError):
        cancelamento.cancelar_e_chamar(c["ag"])
    assert _status_ag(c) == "confirmado"
    assert set(_status_fila(c).values()) == {"aguardando"}


def test_se_outro_pedido_chamou_antes_chama_o_seguinte(c, monkeypatch):
    primeiro = _fila(c, 1, "b1", 0)
    segundo = _fila(c, 2, "b1", 5)
    original = cancelamento.repo_fila.marcar_chamado

    def corrida(id_espera):
        if id_espera == primeiro:
            return False                        # simula outro cancelamento que chamou o primeiro
        return original(id_espera)

    monkeypatch.setattr(cancelamento.repo_fila, "marcar_chamado", corrida)
    assert cancelamento.cancelar_e_chamar(c["ag"]).id_espera == segundo


# ---------- um por vez: não conseguiu falar → chamar o próximo ----------

def test_chamar_o_proximo_marca_desistiu_e_indica_o_seguinte(c):
    a = _fila(c, 1, "b1", 0)
    b = _fila(c, 2, None, 5)
    assert cancelamento.cancelar_e_chamar(c["ag"]).id_espera == a
    r = cancelamento.chamar_proximo(c["ag"], a)
    assert r.ok and r.id_espera == b
    assert _status_fila(c) == {a: "desistiu", b: "chamado"}
    r = cancelamento.chamar_proximo(c["ag"], b)
    assert r.ok and r.id_espera is None
    assert _status_fila(c)[b] == "desistiu"


def test_chamar_o_proximo_nao_chama_se_a_vaga_ja_foi_ocupada(c):
    a = _fila(c, 1, "b1", 0)
    _fila(c, 2, "b1", 5)
    cancelamento.cancelar_e_chamar(c["ag"])
    s = c["db"].session                         # alguém agendou pelo link na vaga liberada
    s.add(Agendamento(cliente_id=c["clientes"][4], barbeiro_id=c["b1"], servico_id=c["corte"],
                      inicio=em(10), fim=em(10, 30), status="confirmado", origem="link"))
    s.commit()
    r = cancelamento.chamar_proximo(c["ag"], a)
    assert r.ok and r.id_espera is None


def test_chamar_o_proximo_repetido_nao_avanca_duas_vezes(c):
    a = _fila(c, 1, "b1", 0)
    b = _fila(c, 2, "b1", 5)
    _fila(c, 3, "b1", 10)
    cancelamento.cancelar_e_chamar(c["ag"])
    assert cancelamento.chamar_proximo(c["ag"], a).id_espera == b
    r = cancelamento.chamar_proximo(c["ag"], a)          # duplo toque com a entrada antiga
    assert not r.ok and r.erro == "ja_atualizado"
    assert list(_status_fila(c).values()) == ["desistiu", "chamado", "aguardando"]


def test_chamar_o_proximo_recusa_agendamento_nao_cancelado_ou_de_outro(c):
    a = _fila(c, 1, "b1", 0)
    assert cancelamento.chamar_proximo(c["ag"], a).erro == "nao_cancelavel"     # ainda confirmado
    cancelamento.cancelar_e_chamar(c["ag"])
    assert cancelamento.chamar_proximo(c["ag"], a, id_barbeiro=c["b2"]).erro == "nao_encontrado"
    assert _status_fila(c)[a] == "chamado"


def test_chamar_o_proximo_recusa_entrada_de_outro_horario(c):
    outra = _fila(c, 1, "b1", 0, hora=time(11), status="chamado")
    cancelamento.cancelar_e_chamar(c["ag"])
    assert cancelamento.chamar_proximo(c["ag"], outra).erro == "ja_atualizado"
    assert _status_fila(c)[outra] == "chamado"


# ---------- leitura para as telas ----------

def test_obter_respeita_o_dono(c):
    assert cancelamento.obter(c["ag"], id_barbeiro=c["b2"]) is None
    a = cancelamento.obter(c["ag"], id_barbeiro=c["b1"])
    assert (a["inicio"], a["cliente"], a["telefone"], a["status"]) == (em(10), "Cliente 0", "51 90000-0000",
                                                                       "confirmado")
    assert a["servico"] == {"nome": "Corte", "duracao_min": 30}
    assert cancelamento.obter(c["ag"])["barbeiro_id"] == c["b1"]


def test_resumo_do_chamado(c):
    a = _fila(c, 1, "b1", 0)
    p = _fila(c, 2, None, 5, hora=time(11))
    r = cancelamento.resumo_chamado(a)
    assert (r["cliente"], r["telefone"], r["data"], r["hora"], r["barbeiro"]) == (
        "Cliente 1", "51 90000-0001", DIA, time(10), "Barbeiro 1")
    assert r["servico"] == {"nome": "Corte", "duracao_min": 30}
    assert cancelamento.resumo_chamado(p)["barbeiro"] is None
    assert cancelamento.resumo_chamado(999) is None
