"""Etapa 5: a Tela 4 mostra o que foi gravado no servidor, não o que vem na URL (RNF02)."""
import re
from urllib.parse import urlencode

from sqlalchemy import select

from app.models import Agendamento, db

BASE = {"servico": 2, "data": "2026-11-14"}
DADOS = {
    "confirmado": {**BASE, "hora": "10:00", "barbeiro": 2, "modo": "confirmacao"},
    "fila_barbeiro": {**BASE, "hora": "10:00", "barbeiro": 1, "modo": "fila_barbeiro"},
    "fila_horario": {**BASE, "hora": "11:00", "barbeiro": "qualquer", "modo": "fila_horario"},
}


def _envia(client, estado, telefone="51 90000-0000", nome="Cliente Exemplo"):
    url = f"/dados?{urlencode(DADOS[estado])}"
    html = client.get(url).get_data(as_text=True)
    token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html).group(1)
    return client.post(url, data={"nome": nome, "telefone": telefone, "csrf_token": token})


def test_envio_redireciona_para_resultado_sem_parametros(client):
    resp = _envia(client, "confirmado")
    assert resp.status_code == 302 and resp.headers["Location"] == "/resultado"


def test_resultado_vem_do_banco(app, client):
    _envia(client, "confirmado")
    html = client.get("/resultado").get_data(as_text=True)
    assert "Agendamento confirmado" in html and "Barbeiro 2" in html and "10:00" in html
    with app.app_context():
        a = db.session.scalar(select(Agendamento).where(Agendamento.origem == "link"))
        a.status = "cancelado"   # o que vale é o registro: cancelado não aparece como confirmado
        db.session.commit()
    resp = client.get("/resultado")
    assert resp.status_code == 302 and resp.headers["Location"] == "/"


def test_url_forjada_nao_mostra_resultado(client):
    forjada = f"/resultado/confirmado?{urlencode({**BASE, 'hora': '10:00', 'barbeiro': 2})}"
    assert client.get(forjada).status_code == 404
    resp = client.get("/resultado?" + urlencode({**BASE, "hora": "10:00", "barbeiro": 2}))
    assert resp.status_code == 302 and resp.headers["Location"] == "/"   # sem envio, sem resultado


def test_sessao_guarda_so_o_id_sem_dados_pessoais(client):
    _envia(client, "fila_horario", nome="Nome Fictício Único")
    with client.session_transaction() as sessao:
        conteudo = str(dict(sessao))
    assert "Nome Fictício Único" not in conteudo and "90000" not in conteudo
    assert "resultado" in conteudo


def test_resultado_nao_mostra_nome_nem_telefone(client):
    _envia(client, "confirmado", nome="Nome Fictício Único")
    html = client.get("/resultado").get_data(as_text=True)
    assert "Nome Fictício Único" not in html and "90000" not in html


def test_fila_repetida_mostra_mensagem_de_duplicidade(client):
    _envia(client, "fila_horario")
    primeira = client.get("/resultado").get_data(as_text=True)
    assert "Você está na fila de espera para 14/11/2026 às 11:00" in primeira
    assert "Você já está nesta fila de espera." not in primeira
    _envia(client, "fila_horario", telefone="(51) 90000-0000")
    html = client.get("/resultado").get_data(as_text=True)
    assert "<h1>Você já está nesta fila de espera.</h1>" in html
    assert "Corte + barba – 45 min · Qualquer barbeiro · 14/11/2026 às 11:00" in html
    assert "Vamos chamar você pelo WhatsApp se surgir vaga em qualquer barbeiro neste horário." in html
    assert 'class="icone"' in html and 'aria-live="polite"' in html and "Voltar ao início" in html


def test_fila_do_barbeiro_repetida_mostra_duplicidade(client):
    _envia(client, "fila_barbeiro")
    _envia(client, "fila_barbeiro")
    html = client.get("/resultado").get_data(as_text=True)
    assert "<h1>Você já está nesta fila de espera.</h1>" in html
    assert "Corte + barba – 45 min · Barbeiro 1 · 14/11/2026 às 10:00" in html
    assert "Vamos chamar você pelo WhatsApp se o Barbeiro 1 liberar este horário." in html
