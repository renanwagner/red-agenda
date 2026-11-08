"""Etapa 5: resultado da Tela 4 a partir do registro gravado."""
from datetime import date, time

from app.models import Barbeiro, Cliente, ListaEspera, Servico
from app.services.resultado import resultado


def _entrada(db, status="aguardando", com_barbeiro=False):
    b = Barbeiro(nome="Barbeiro 1", email="b1@exemplo.com", senha_hash="h", papel="barbeiro")
    s, c = Servico(nome="Corte", duracao_min=30), Cliente(nome="Cliente Exemplo", telefone="51900000000")
    db.session.add_all([b, s, c])
    db.session.flush()
    e = ListaEspera(cliente_id=c.id_cliente, servico_id=s.id_servico, data_desejada=date(2026, 11, 14),
                    hora_desejada=time(11), status=status, barbeiro_id=b.id_barbeiro if com_barbeiro else None)
    db.session.add(e)
    db.session.flush()
    id_espera = e.id_espera
    db.session.commit()
    return id_espera


def test_fila_por_horario_e_do_barbeiro(banco):
    r = resultado("fila", _entrada(banco), duplicada=True)
    assert (r["estado"], r["barbeiro"], r["hora"], r["duplicada"]) == ("fila_horario", None, "11:00", True)
    assert r["servico"] == {"nome": "Corte", "duracao_min": 30}


def test_fila_do_barbeiro(banco):
    r = resultado("fila", _entrada(banco, com_barbeiro=True))
    assert (r["estado"], r["barbeiro"], r["duplicada"]) == ("fila_barbeiro", "Barbeiro 1", False)


def test_entrada_que_ja_nao_aguarda_nao_e_mostrada(banco):
    assert resultado("fila", _entrada(banco, status="chamado")) is None


def test_inexistente_ou_tipo_invalido(banco):
    assert resultado("agendamento", 9999) is None
    assert resultado("fila", 9999) is None
    assert resultado("outro", 1) is None
    assert resultado(None, None) is None
