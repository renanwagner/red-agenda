"""Persistência (docs/03): seis entidades, unicidades e restrições. Dados fictícios."""
from datetime import date, datetime, time

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.models import (
    Agendamento, Barbeiro, Cliente, JanelaAtendimento, ListaEspera, Servico,
)


def _barbeiro(nome="Barbeiro 1", email="barbeiro1@exemplo.com", **extra):
    return Barbeiro(nome=nome, email=email, senha_hash="hash-fictício", papel="barbeiro", **extra)


def _cliente(telefone="51900000000"):
    return Cliente(nome="Cliente Exemplo", telefone=telefone)


def _servico(nome="Corte", duracao_min=30):
    return Servico(nome=nome, duracao_min=duracao_min)


def _grava(db, *objetos):
    db.session.add_all(objetos)
    db.session.commit()


def _recusa(db, *objetos):
    db.session.add_all(objetos)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_seis_tabelas_com_os_nomes_do_modelo(banco):
    esperado = {"barbeiro", "cliente", "servico", "janela_atendimento", "agendamento", "lista_espera"}
    assert set(inspect(banco.engine).get_table_names()) == esperado


def test_chaves_primarias_id_entidade(banco):
    inspetor = inspect(banco.engine)
    for tabela, pk in [("barbeiro", "id_barbeiro"), ("cliente", "id_cliente"), ("servico", "id_servico"),
                       ("janela_atendimento", "id_janela"), ("agendamento", "id_agendamento"),
                       ("lista_espera", "id_espera")]:
        assert inspetor.get_pk_constraint(tabela)["constrained_columns"] == [pk]


def test_padroes_de_barbeiro_cliente_e_servico(banco):
    b, c, s = _barbeiro(), _cliente(), _servico()
    _grava(banco, b, c, s)
    assert b.ativo is True and s.ativo is True
    assert isinstance(c.criado_em, datetime)


def test_email_do_barbeiro_e_unico(banco):
    _grava(banco, _barbeiro())
    _recusa(banco, _barbeiro(nome="Outro"))


def test_papel_do_barbeiro_so_aceita_administrador_ou_barbeiro(banco):
    _recusa(banco, Barbeiro(nome="X", email="x@exemplo.com", senha_hash="h", papel="gerente"))
    _grava(banco, Barbeiro(nome="Admin", email="admin@exemplo.com", senha_hash="h", papel="administrador"))


def test_telefone_do_cliente_e_unico(banco):
    _grava(banco, _cliente())
    _recusa(banco, _cliente())


def test_nome_do_servico_e_unico(banco):
    _grava(banco, _servico())
    _recusa(banco, _servico())


@pytest.mark.parametrize("duracao", [0, -5, 7, 32])
def test_duracao_deve_ser_positiva_e_multiplo_de_5(banco, duracao):
    _recusa(banco, _servico(duracao_min=duracao))


def test_duracao_valida(banco):
    _grava(banco, _servico(duracao_min=45))


def test_janela_hora_fim_maior_que_hora_inicio(banco):
    b = _barbeiro()
    _grava(banco, b)
    base = dict(barbeiro_id=b.id_barbeiro, data=date(2026, 11, 14), tipo="aberto")
    _recusa(banco, JanelaAtendimento(hora_inicio=time(10), hora_fim=time(10), **base))
    _recusa(banco, JanelaAtendimento(hora_inicio=time(10), hora_fim=time(9), **base))
    _grava(banco, JanelaAtendimento(hora_inicio=time(9), hora_fim=time(12), **base))


def test_janela_tipo_aberto_ou_bloqueado(banco):
    b = _barbeiro()
    _grava(banco, b)
    _recusa(banco, JanelaAtendimento(barbeiro_id=b.id_barbeiro, data=date(2026, 11, 14),
                                     hora_inicio=time(9), hora_fim=time(10), tipo="livre"))


def _agendamento(b, c, s, **extra):
    dados = dict(cliente_id=c.id_cliente, barbeiro_id=b.id_barbeiro, servico_id=s.id_servico,
                 inicio=datetime(2026, 11, 14, 10, 0), fim=datetime(2026, 11, 14, 10, 30),
                 status="confirmado", origem="link")
    dados.update(extra)
    return Agendamento(**dados)


def test_agendamento_valido_e_restricoes(banco):
    b, c, s = _barbeiro(), _cliente(), _servico()
    _grava(banco, b, c, s)
    _grava(banco, _agendamento(b, c, s))
    _recusa(banco, _agendamento(b, c, s, fim=datetime(2026, 11, 14, 10, 0)))      # fim == inicio
    _recusa(banco, _agendamento(b, c, s, status="pendente"))
    _recusa(banco, _agendamento(b, c, s, origem="telefone"))


def test_agendamento_exige_referencias_existentes(banco):
    b, c, s = _barbeiro(), _cliente(), _servico()
    _grava(banco, b, c, s)
    _recusa(banco, _agendamento(b, c, s, cliente_id=9999))


def _espera(c, s, barbeiro_id=None, hora=time(10), status="aguardando"):
    return ListaEspera(cliente_id=c.id_cliente, servico_id=s.id_servico, barbeiro_id=barbeiro_id,
                       data_desejada=date(2026, 11, 14), hora_desejada=hora, status=status)


def test_fila_sem_duplicidade_aguardando_barbeiro_nulo_conta_como_valor(banco):
    b, c, s = _barbeiro(), _cliente(), _servico()
    _grava(banco, b, c, s)
    _grava(banco, _espera(c, s))                       # fila por horário (barbeiro nulo)
    _recusa(banco, _espera(c, s))                      # igual: recusada
    _grava(banco, _espera(c, s, barbeiro_id=b.id_barbeiro))   # outro barbeiro: aceita
    _recusa(banco, _espera(c, s, barbeiro_id=b.id_barbeiro))
    _grava(banco, _espera(c, s, hora=time(10, 30)))    # outra hora: aceita


def test_fila_desfecho_nao_bloqueia_nova_entrada(banco):
    c, s = _cliente(), _servico()
    _grava(banco, c, s)
    _grava(banco, _espera(c, s, status="chamado"))
    _grava(banco, _espera(c, s))                       # aguardando de novo, ok
    _recusa(banco, _espera(c, s, status="esperando"))  # status inválido


def test_fila_exige_hora_desejada(banco):
    c, s = _cliente(), _servico()
    _grava(banco, c, s)
    _recusa(banco, _espera(c, s, hora=None))
