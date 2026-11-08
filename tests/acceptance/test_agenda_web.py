"""RF06 pelo painel: agenda do dia e da semana, textos e permissão (próprio barbeiro / administrador)."""
import re
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from werkzeug.security import generate_password_hash

from app.models import Agendamento, Barbeiro, Cliente, Servico, db
from app.services.autenticacao import criar_administrador

SENHA = "senha-de-teste-1"
DIA = "2027-02-06"   # sábado fora do período da demonstração (sem agendamentos prévios)


@pytest.fixture
def contas(app):
    with app.app_context():
        b1 = db.session.get(Barbeiro, 1)
        b1.senha_hash = generate_password_hash(SENHA)
        db.session.commit()
        criar_administrador("Admin Exemplo", "admin@exemplo.com", SENHA)
    return {"comum": "barbeiro1@exemplo.com", "admin": "admin@exemplo.com"}


def _html(resp):
    return resp.get_data(as_text=True)


def _entrar(client, email):
    m = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', _html(client.get("/painel/entrar")))
    resp = client.post("/painel/entrar", data={"email": email, "senha": SENHA, "csrf_token": m.group(1)})
    assert resp.status_code == 302


def _agendar(app, barbeiro, inicio, nome="Cliente Exemplo", telefone="51900000099", status="confirmado"):
    with app.app_context():
        cliente = db.session.scalar(select(Cliente).where(Cliente.telefone == telefone))
        if cliente is None:
            cliente = Cliente(nome=nome, telefone=telefone)
            db.session.add(cliente)
            db.session.flush()
        corte = db.session.scalar(select(Servico).where(Servico.nome == "Corte"))
        db.session.add(Agendamento(cliente_id=cliente.id_cliente, barbeiro_id=barbeiro, servico_id=corte.id_servico,
                                   inicio=inicio, fim=inicio + timedelta(minutes=30), status=status, origem="link"))
        db.session.commit()


def _em(hora, minuto=0, dia=DIA):
    return datetime.fromisoformat(f"{dia}T{hora:02d}:{minuto:02d}")


def test_sem_login_redireciona(client):
    resp = client.get("/painel/agenda")
    assert resp.status_code == 302
    assert "/painel/entrar" in resp.headers["Location"]


def test_painel_tem_botao_agenda(client, contas):
    _entrar(client, contas["comum"])
    assert ">Agenda</a>" in _html(client.get("/painel"))


def test_rf06_dia_com_cinco_confirmados_e_um_cancelado(app, client, contas):
    for hora, minuto in [(11, 0), (9, 0), (10, 30), (9, 30), (10, 0)]:
        _agendar(app, 1, _em(hora, minuto))
    _agendar(app, 1, _em(11, 30), status="cancelado")
    _agendar(app, 2, _em(9, 0), nome="Cliente Outro", telefone="51900000098")
    _entrar(client, contas["comum"])

    html = _html(client.get(f"/painel/agenda?data={DIA}"))

    horas = re.findall(r'<span class="agenda__hora">(\d\d:\d\d) – ', html)
    assert horas == ["09:00", "09:30", "10:00", "10:30", "11:00"]
    assert "11:30 – 12:00" not in html                         # cancelado não aparece
    assert "Cliente Outro" not in html                         # agenda de outro barbeiro
    assert "Cliente Exemplo · 51 90000-0099" in html
    assert "Corte – 30 min" in html


def test_textos_da_tela(client, contas):
    _entrar(client, contas["comum"])
    html = _html(client.get(f"/painel/agenda?data={DIA}"))
    for texto in ["<h1>Agenda</h1>", '<label class="rotulo" for="data">Data</label>', ">Ver dia</button>",
                  ">Ver semana</button>", "Nenhum agendamento confirmado nesta data.", ">Voltar</a>"]:
        assert texto in html, texto
    assert 'for="barbeiro"' not in html                        # campo Barbeiro só para administrador
    semana = _html(client.get(f"/painel/agenda?data={DIA}&visao=semana"))
    assert "Nenhum agendamento confirmado nesta semana." in semana


def test_semana_agrupa_por_dia_e_omite_dias_vazios(app, client, contas):
    _agendar(app, 1, _em(9, dia="2027-02-02"))     # terça
    _agendar(app, 1, _em(10))                       # sábado
    _agendar(app, 1, _em(9, dia="2027-02-08"))     # segunda seguinte: fora
    _entrar(client, contas["comum"])

    html = _html(client.get(f"/painel/agenda?data={DIA}&visao=semana"))

    assert re.findall(r"<h2>([^<]+)</h2>", html) == ["terça-feira, 02/02/2027", "sábado, 06/02/2027"]
    assert "08/02/2027" not in html


def test_barbeiro_comum_nao_ve_agenda_de_outro(app, client, contas):
    _agendar(app, 2, _em(9), nome="Cliente Outro", telefone="51900000098")
    _entrar(client, contas["comum"])
    html = _html(client.get(f"/painel/agenda?data={DIA}&barbeiro=2"))
    assert "Cliente Outro" not in html
    assert "Nenhum agendamento confirmado nesta data." in html


def test_administrador_escolhe_o_barbeiro(app, client, contas):
    _agendar(app, 2, _em(9), nome="Cliente Outro", telefone="51900000098")
    _entrar(client, contas["admin"])
    html = _html(client.get(f"/painel/agenda?data={DIA}&barbeiro=2"))
    assert 'for="barbeiro"' in html
    assert "Cliente Outro · 51 90000-0098" in html


def test_nome_do_cliente_e_escapado(app, client, contas):
    _agendar(app, 1, _em(9), nome="<script>alert(1)</script>")
    _entrar(client, contas["comum"])
    html = _html(client.get(f"/painel/agenda?data={DIA}"))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_visao_e_data_invalidas_usam_padrao(client, contas):
    _entrar(client, contas["comum"])
    resp = client.get("/painel/agenda?data=xx&visao=mes")
    assert resp.status_code == 200                             # data de hoje, visão do dia
    assert "nesta semana." not in _html(resp)
