"""RF04 pela Tela 3: os dois tipos de fila gravam no banco; repetir não duplica."""
import re
from datetime import time
from urllib.parse import urlencode

from sqlalchemy import select

from app.models import ListaEspera, db

BASE = {"servico": 2, "data": "2026-11-14"}
FILA_BARBEIRO = f"/dados?{urlencode({**BASE, 'hora': '10:00', 'barbeiro': 1, 'modo': 'fila_barbeiro'})}"
FILA_HORARIO = f"/dados?{urlencode({**BASE, 'hora': '11:00', 'barbeiro': 'qualquer', 'modo': 'fila_horario'})}"


def _post(client, url, telefone="51 90000-0000"):
    html = client.get(url).get_data(as_text=True)
    token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html).group(1)
    return client.post(url, data={"nome": "Cliente Exemplo", "telefone": telefone, "csrf_token": token})


def _entradas(app):
    with app.app_context():
        return [(e.barbeiro_id, e.hora_desejada, e.status)
                for e in db.session.scalars(select(ListaEspera).order_by(ListaEspera.id_espera))]


def test_fila_do_barbeiro_grava_e_mostra_resultado(app, client):
    resp = _post(client, FILA_BARBEIRO)
    assert resp.status_code == 302 and resp.headers["Location"].startswith("/resultado/fila_barbeiro")
    assert _entradas(app) == [(1, time(10), "aguardando")]


def test_fila_por_horario_grava_barbeiro_nulo(app, client):
    resp = _post(client, FILA_HORARIO)
    assert resp.status_code == 302 and resp.headers["Location"].startswith("/resultado/fila_horario")
    assert _entradas(app) == [(None, time(11), "aguardando")]


def test_repetir_a_mesma_fila_nao_duplica(app, client):
    _post(client, FILA_HORARIO)
    resp = _post(client, FILA_HORARIO, telefone="(51) 90000-0000")
    assert resp.status_code == 302
    assert len(_entradas(app)) == 1


def test_dados_invalidos_nao_entram_na_fila(app, client):
    assert _post(client, FILA_BARBEIRO, telefone="51 9").status_code == 200
    assert _entradas(app) == []
