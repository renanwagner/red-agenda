"""RF02 pela Tela 3: confirmar grava no banco; horário tomado no meio do caminho volta à Tela 2."""
import re
from urllib.parse import urlencode

from sqlalchemy import func, select

from app.models import Agendamento, Cliente, db

# Barbeiro 2 livre às 10:00 para Corte + barba nos dados de demonstração
PARAMS = {"servico": 2, "data": "2026-11-14", "hora": "10:00", "barbeiro": 2}
URL = f"/dados?{urlencode({**PARAMS, 'modo': 'confirmacao'})}"


def _token(client):
    html = client.get(URL).get_data(as_text=True)
    return re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html).group(1)


def _post(client, telefone="51 90000-0000"):
    return client.post(URL, data={"nome": "Cliente Exemplo", "telefone": telefone, "csrf_token": _token(client)})


def _do_link(app):
    with app.app_context():
        return db.session.scalar(
            select(func.count()).select_from(Agendamento).where(Agendamento.origem == "link"))


def test_confirmar_grava_agendamento_e_cliente(app, client):
    resp = _post(client)
    assert resp.status_code == 302 and resp.headers["Location"] == "/resultado"
    with app.app_context():
        a = db.session.scalar(select(Agendamento).where(Agendamento.origem == "link"))
        assert (a.barbeiro_id, a.status, a.inicio.strftime("%H:%M"), a.fim.strftime("%H:%M")) == \
            (2, "confirmado", "10:00", "10:45")
        assert db.session.get(Cliente, a.cliente_id).telefone == "51900000000"


def test_horario_tomado_antes_do_envio_volta_a_tela2(app, client):
    token = _token(client)              # cliente B abre a Tela 3 ...
    assert _post(client).status_code == 302   # ... cliente A confirma antes
    resp = client.post(URL, data={"nome": "Cliente Exemplo", "telefone": "51 90000-0009", "csrf_token": token})
    assert resp.status_code == 302 and "/disponibilidade" in resp.headers["Location"]
    assert _do_link(app) == 1
    html = client.get(resp.headers["Location"]).get_data(as_text=True)
    assert "Barbeiro 2 não está livre às 10:00" in html   # caso b, com as alternativas


def test_dados_invalidos_nao_gravam(app, client):
    assert _post(client, telefone="51 9").status_code == 200
    assert _do_link(app) == 0
