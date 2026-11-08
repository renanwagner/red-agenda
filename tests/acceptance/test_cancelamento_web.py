"""RF05 pelo painel: confirmação, cancelamento, próximo da fila e permissões."""
import re
from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy import select
from werkzeug.security import generate_password_hash

from app.models import Agendamento, Barbeiro, Cliente, JanelaAtendimento, ListaEspera, Servico, db
from app.services.autenticacao import criar_administrador

SENHA = "senha-de-teste-1"
DIA = date(2027, 2, 6)   # sábado fora do período da demonstração


@pytest.fixture
def contas(app):
    with app.app_context():
        b1 = db.session.get(Barbeiro, 1)
        b1.senha_hash = generate_password_hash(SENHA)
        db.session.commit()
        criar_administrador("Admin Exemplo", "admin@exemplo.com", SENHA)
    return {"comum": "barbeiro1@exemplo.com", "admin": "admin@exemplo.com"}


@pytest.fixture
def cenario(app):
    """Barbeiros 1 e 2 com janela 09:00–12:00 e um agendamento de Corte às 10:00 para cada um."""
    with app.app_context():
        corte = db.session.scalar(select(Servico).where(Servico.nome == "Corte"))
        cliente = Cliente(nome="Cliente Exemplo", telefone="51900000099")
        db.session.add(cliente)
        db.session.flush()
        ids = {"corte": corte.id_servico}
        for b in (1, 2):
            db.session.add(JanelaAtendimento(barbeiro_id=b, data=DIA, hora_inicio=time(9), hora_fim=time(12),
                                             tipo="aberto"))
            ag = Agendamento(cliente_id=cliente.id_cliente, barbeiro_id=b, servico_id=corte.id_servico,
                             inicio=datetime.combine(DIA, time(10)), fim=datetime.combine(DIA, time(10, 30)),
                             status="confirmado", origem="link")
            db.session.add(ag)
            db.session.flush()
            ids[f"ag{b}"] = ag.id_agendamento
        db.session.commit()
    return ids


def _fila(app, cenario, nome, telefone, barbeiro, minutos):
    with app.app_context():
        c = Cliente(nome=nome, telefone=telefone)
        db.session.add(c)
        db.session.flush()
        e = ListaEspera(cliente_id=c.id_cliente, servico_id=cenario["corte"], barbeiro_id=barbeiro,
                        data_desejada=DIA, hora_desejada=time(10),
                        entrou_em=datetime(2027, 2, 1, 8) + timedelta(minutes=minutos))
        db.session.add(e)
        db.session.commit()
        return e.id_espera


def _status(app, modelo, id_):
    with app.app_context():
        return db.session.get(modelo, id_).status


def _html(resp):
    return resp.get_data(as_text=True)


def _token(client, url):
    m = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', _html(client.get(url)))
    assert m, url
    return m.group(1)


def _entrar(client, email):
    t = _token(client, "/painel/entrar")
    assert client.post("/painel/entrar", data={"email": email, "senha": SENHA, "csrf_token": t}).status_code == 302


def _url(id_ag):
    return f"/painel/agendamentos/{id_ag}/cancelar"


def _cancelar(client, id_ag):
    t = _token(client, _url(id_ag))
    return client.post(_url(id_ag), data={"csrf_token": t}, follow_redirects=True)


def test_sem_login_redireciona(client, cenario):
    for resp in (client.get(_url(cenario["ag1"])), client.get("/painel/cancelado")):
        assert resp.status_code == 302 and "/painel/entrar" in resp.headers["Location"]


def test_agenda_tem_cancelar_e_confirmacao_tem_os_textos(client, contas, cenario):
    _entrar(client, contas["comum"])
    agenda = _html(client.get(f"/painel/agenda?data={DIA.isoformat()}"))
    assert f'href="{_url(cenario["ag1"])}">Cancelar</a>' in agenda

    html = _html(client.get(_url(cenario["ag1"])))
    for texto in ["<h1>Cancelar agendamento</h1>",
                  "sábado, 06/02/2027 · 10:00 – 10:30 · Corte – 30 min · Cliente Exemplo · 51 90000-0099",
                  ">Confirmar cancelamento</button>", ">Voltar</a>"]:
        assert texto in html, texto
    assert _status(client.application, Agendamento, cenario["ag1"]) == "confirmado"   # GET não cancela


def test_cancela_e_indica_o_proximo_da_fila_do_barbeiro(app, client, contas, cenario):
    _fila(app, cenario, "Cliente Horario", "51900000097", None, 0)
    do_barbeiro = _fila(app, cenario, "Cliente Fila", "51900000098", 1, 10)
    _entrar(client, contas["comum"])

    resp = _cancelar(client, cenario["ag1"])

    html = _html(resp)
    assert resp.request.path == "/painel/cancelado"                    # sem nome nem telefone na URL
    for texto in ["<h1>Agendamento cancelado.</h1>", "<h2>Próximo da fila</h2>",
                  "<strong>Cliente Fila</strong> · <span class=\"agenda__fone\">51 90000-0098</span>", "Corte – 30 min · sábado, 06/02/2027 às 10:00",
                  "Fila do Barbeiro 1", "Chame o cliente pelo WhatsApp.",
                  ">Não conseguiu falar? Chamar o próximo</button>", ">Voltar à agenda</a>"]:
        assert texto in html, texto
    assert _status(app, Agendamento, cenario["ag1"]) == "cancelado"
    assert _status(app, ListaEspera, do_barbeiro) == "chamado"
    agenda = _html(client.get(f"/painel/agenda?data={DIA.isoformat()}"))
    assert "Nenhum agendamento confirmado nesta data." in agenda     # cancelado sai da agenda


def test_chamar_o_proximo_ate_acabar_a_fila(app, client, contas, cenario):
    primeiro = _fila(app, cenario, "Cliente Fila", "51900000098", 1, 0)
    segundo = _fila(app, cenario, "Cliente Horario", "51900000097", None, 10)
    _entrar(client, contas["comum"])
    _cancelar(client, cenario["ag1"])

    t = _token(client, "/painel/cancelado")
    html = _html(client.post("/painel/cancelado/proximo", data={"csrf_token": t}, follow_redirects=True))
    assert "<strong>Cliente Horario</strong>" in html and "Fila por horário" in html
    assert (_status(app, ListaEspera, primeiro), _status(app, ListaEspera, segundo)) == ("desistiu", "chamado")

    t = _token(client, "/painel/cancelado")
    html = _html(client.post("/painel/cancelado/proximo", data={"csrf_token": t}, follow_redirects=True))
    assert "Ninguém na fila de espera para este horário." in html
    assert "Chamar o próximo" not in html


def test_sem_fila_mostra_ninguem(client, contas, cenario):
    _entrar(client, contas["comum"])
    html = _html(_cancelar(client, cenario["ag1"]))
    assert "Ninguém na fila de espera para este horário." in html
    assert "Chame o cliente pelo WhatsApp." not in html


def test_barbeiro_nao_cancela_agendamento_de_outro(app, client, contas, cenario):
    _entrar(client, contas["comum"])
    assert client.get(_url(cenario["ag2"])).status_code == 404
    t = _token(client, _url(cenario["ag1"]))
    assert client.post(_url(cenario["ag2"]), data={"csrf_token": t}).status_code == 404
    assert _status(app, Agendamento, cenario["ag2"]) == "confirmado"


def test_administrador_cancela_de_qualquer_barbeiro(app, client, contas, cenario):
    _entrar(client, contas["admin"])
    html = _html(_cancelar(client, cenario["ag2"]))
    assert "<h1>Agendamento cancelado.</h1>" in html
    assert f'href="/painel/agenda?data={DIA.isoformat()}&amp;barbeiro=2"' in html
    assert _status(app, Agendamento, cenario["ag2"]) == "cancelado"


def test_post_sem_csrf_e_recusado(app, client, contas, cenario):
    _entrar(client, contas["comum"])
    assert client.post(_url(cenario["ag1"])).status_code == 400
    assert client.post("/painel/cancelado/proximo").status_code == 400
    assert _status(app, Agendamento, cenario["ag1"]) == "confirmado"


def test_ja_cancelado_mostra_erro_na_agenda(app, client, contas, cenario):
    _entrar(client, contas["comum"])
    t = _token(client, _url(cenario["ag1"]))
    _cancelar(client, cenario["ag1"])
    resp = client.post(_url(cenario["ag1"]), data={"csrf_token": t}, follow_redirects=True)   # segundo envio
    assert "Este agendamento não pode mais ser cancelado." in _html(resp)
    resp = client.get(_url(cenario["ag1"]), follow_redirects=True)
    assert "Este agendamento não pode mais ser cancelado." in _html(resp)
    assert "<h1>Agenda</h1>" in _html(resp)


def test_resultado_sem_cancelamento_volta_para_a_agenda(client, contas):
    _entrar(client, contas["comum"])
    resp = client.get("/painel/cancelado")
    assert resp.status_code == 302 and resp.headers["Location"].startswith("/painel/agenda")
    resp = client.post("/painel/cancelado/proximo", data={"csrf_token": _token(client, "/painel")})
    assert resp.status_code == 302 and resp.headers["Location"] == "/painel/cancelado"


def test_sair_limpa_o_resultado(client, contas, cenario):
    _entrar(client, contas["comum"])
    _cancelar(client, cenario["ag1"])
    client.post("/painel/sair", data={"csrf_token": _token(client, "/painel")})
    _entrar(client, contas["comum"])
    assert client.get("/painel/cancelado").status_code == 302
