"""Aceitação do protótipo: fluxo em 4 telas (escolha → disponibilidade → dados → resultado)."""
import re
from urllib.parse import urlencode

import pytest

from app.web.dados_demo import CLIENTE_EXEMPLO


def _url(rota, **p):
    base = {"servico": 2, "data": "2026-11-14"}
    base.update(p)
    return f"{rota}?{urlencode(base)}"


def _html(resp):
    return resp.get_data(as_text=True)


def _token(html):
    m = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html)
    assert m, "token CSRF ausente"
    return m.group(1)


URL_DADOS = _url("/dados", hora="10:00", barbeiro=2, modo="confirmacao")
URL_RESULT = {
    "confirmado": _url("/resultado/confirmado", hora="10:00", barbeiro=2),
    "fila_horario": _url("/resultado/fila_horario", hora="11:00", barbeiro="qualquer"),
    "fila_barbeiro": _url("/resultado/fila_barbeiro", hora="10:00", barbeiro=1),
}
TODAS = [
    "/",
    _url("/", hora="10:00", barbeiro="qualquer"),
    _url("/disponibilidade", hora="10:00", barbeiro=2),
    _url("/disponibilidade", hora="10:00", barbeiro=1),
    _url("/disponibilidade", hora="10:00", barbeiro="qualquer"),
    _url("/disponibilidade", hora="11:00", barbeiro="qualquer"),
    URL_DADOS,
    _url("/dados", hora="10:00", barbeiro=1, modo="fila_barbeiro"),
    _url("/dados", hora="11:00", barbeiro="qualquer", modo="fila_horario"),
    *URL_RESULT.values(),
]


def _post_dados(client, url=URL_DADOS, **campos):
    dados = {"nome": CLIENTE_EXEMPLO["nome"], "telefone": CLIENTE_EXEMPLO["telefone"],
             "csrf_token": _token(_html(client.get(url)))}
    dados.update(campos)
    return client.post(url, data=dados)


# ---------- Tela 1 ----------

def test_tela1_textos_e_padroes(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = _html(resp)
    for texto in ["Agende seu horário na RED Barbearia", "Estância Velha, RS", "Escolha o serviço",
                  "Escolha a data", "Escolha o horário", "Escolha o barbeiro",
                  "Corte – 30 min", "Corte + barba – 45 min", "Corte infantil – 45 min",
                  "Barba – 15 min", "Sobrancelha – 10 min", "Corte na zero – 15 min",
                  "Zero + barba – 30 min", "09:30", "10:00", "10:30", "11:00",
                  "Qualquer barbeiro", "Barbeiro 1", "Barbeiro 2", "Barbeiro 3"]:
        assert texto in html, texto
    assert 'value="2026-11-14"' in html
    assert "Selecionado: 14/11/2026" in html
    assert "Selecionado: Qualquer barbeiro" in html


def test_tela1_sem_aplicar_data(client):
    assert "Aplicar data" not in _html(client.get("/"))


@pytest.mark.parametrize("params", [{}, {"servico": 2}, {"hora": "10:00"}, {"servico": 2, "data": "x"}])
def test_tela1_botao_desabilitado_sem_as_tres_escolhas(client, params):
    html = _html(client.get(f"/?{urlencode(params)}"))
    if "data" in params:  # data inválida volta ao padrão, mas falta o horário
        assert "Selecionado: 14/11/2026" in html
    assert re.search(r"<button[^>]*disabled[^>]*>Ver disponibilidade", html)
    assert "Selecione serviço, data e horário para continuar" in html


def test_tela1_habilita_com_servico_data_hora(client):
    html = _html(client.get(_url("/", hora="10:00", barbeiro="qualquer")))
    assert not re.search(r"<button[^>]*disabled[^>]*>Ver disponibilidade", html)
    assert "Selecionado: Corte + barba – 45 min" in html
    assert "Selecionado: 10:00" in html


def test_tela1_botao_de_opcao_mantem_demais_escolhas(client):
    html = _html(client.get("/?servico=2&data=2026-11-21&barbeiro=3&escolher=hora:10:30"))
    for texto in ["Selecionado: Corte + barba – 45 min", "Selecionado: 21/11/2026",
                  "Selecionado: 10:30", "Selecionado: Barbeiro 3"]:
        assert texto in html, texto


# ---------- Tela 2 ----------

def test_tela2_caso_a_barbeiro_livre(client):
    html = _html(client.get(_url("/disponibilidade", hora="10:00", barbeiro=2)))
    assert "Barbeiro 2 está livre às 10:00" in html
    assert "Continuar com Barbeiro 2" in html
    assert "modo=confirmacao" in html


def test_tela2_caso_b_barbeiro_ocupado(client):
    html = _html(client.get(_url("/disponibilidade", hora="10:00", barbeiro=1)))
    assert "Barbeiro 1 não está livre às 10:00" in html
    assert "Entrar na fila para o Barbeiro 1 às 10:00" in html
    assert "modo=fila_barbeiro" in html
    assert "Ver outros barbeiros livres às 10:00" in html
    assert "Barbeiro 2 – 10:00" in html and "Barbeiro 3 – 10:00" in html
    assert 'class="icone"' in html


def test_tela2_caso_b_sem_outros_livres_esconde_botao(client):
    html = _html(client.get(_url("/disponibilidade", hora="11:00", barbeiro=1)))
    assert "Barbeiro 1 não está livre às 11:00" in html
    assert "Ver outros barbeiros livres" not in html


def test_tela2_caso_c_qualquer_com_livres(client):
    html = _html(client.get(_url("/disponibilidade", hora="10:00", barbeiro="qualquer")))
    assert "Barbeiro 2 – 10:00" in html and "Barbeiro 3 – 10:00" in html
    assert "Barbeiro 1 – 10:00" not in html


def test_tela2_caso_d_qualquer_sem_livres(client):
    html = _html(client.get(_url("/disponibilidade", hora="11:00", barbeiro="qualquer")))
    assert "Nenhum barbeiro está livre às 11:00" in html
    assert "Entrar na fila para 11:00" in html
    assert "modo=fila_horario" in html


def test_tela2_resumo_e_voltar_mantem_escolha(client):
    html = _html(client.get(_url("/disponibilidade", hora="10:00", barbeiro=2)))
    assert "Corte + barba – 45 min · 14/11/2026 às 10:00" in html
    assert re.search(r'href="/\?servico=2&amp;data=2026-11-14&amp;hora=10:00&amp;barbeiro=2">Voltar', html)


@pytest.mark.parametrize("url", ["/disponibilidade", _url("/disponibilidade", hora="12:00", barbeiro=2),
                                 _url("/disponibilidade", hora="10:00", barbeiro=9)])
def test_tela2_parametros_invalidos_redirecionam(client, url):
    resp = client.get(url)
    assert resp.status_code == 302
    assert resp.headers["Location"].startswith("/?") or resp.headers["Location"] == "/"


# ---------- Tela 3 ----------

@pytest.mark.parametrize("url,resumo,botao", [
    (URL_DADOS, "Corte + barba – 45 min · Barbeiro 2 · 14/11/2026 às 10:00", "Confirmar agendamento"),
    (_url("/dados", hora="10:00", barbeiro=1, modo="fila_barbeiro"),
     "Fila de espera · Corte + barba – 45 min · Barbeiro 1 · 14/11/2026 às 10:00", "Entrar na fila de espera"),
    (_url("/dados", hora="11:00", barbeiro="qualquer", modo="fila_horario"),
     "Fila de espera · Corte + barba – 45 min · Qualquer barbeiro · 14/11/2026 às 11:00",
     "Entrar na fila de espera"),
])
def test_tela3_textos_por_modo(client, url, resumo, botao):
    html = _html(client.get(url))
    assert "Seus dados" in html and resumo in html and botao in html and "Voltar" in html
    assert '<label class="rotulo" for="nome">Nome</label>' in html
    assert '<label class="rotulo" for="telefone">Telefone (com DDD)</label>' in html
    assert 'placeholder="Cliente Exemplo"' in html and 'placeholder="51 90000-0000"' in html
    assert 'value="Cliente' not in html and 'value="51' not in html  # campos vazios


def test_tela3_modo_incoerente_volta_tela2(client):
    resp = client.get(_url("/dados", hora="10:00", barbeiro=1, modo="confirmacao"))
    assert resp.status_code == 302
    assert "/disponibilidade" in resp.headers["Location"]


@pytest.mark.parametrize("telefone", ["51 9000", "", "abc", "51 90000-0000-99", "0000000000"])
def test_tela3_telefone_invalido_nao_redireciona(client, telefone):
    resp = _post_dados(client, telefone=telefone)
    assert resp.status_code == 200
    html = _html(resp)
    assert "Telefone incompleto. Informe DDD e número, como 51 90000-0000" in html
    assert 'aria-live="assertive"' in html and 'class="icone"' in html
    assert re.search(r'<input[^>]*autofocus[^>]*id="telefone"', html)


def test_tela3_nome_vazio_mostra_erro(client):
    resp = _post_dados(client, nome="")
    assert resp.status_code == 200
    assert "Informe seu nome." in _html(resp)


@pytest.mark.parametrize("url,destino", [
    (URL_DADOS, "/resultado/confirmado"),
    (_url("/dados", hora="10:00", barbeiro=1, modo="fila_barbeiro"), "/resultado/fila_barbeiro"),
    (_url("/dados", hora="11:00", barbeiro="qualquer", modo="fila_horario"), "/resultado/fila_horario"),
])
def test_tela3_sucesso_redireciona_sem_dados_pessoais(client, url, destino):
    resp = _post_dados(client, url=url)
    assert resp.status_code == 302
    local = resp.headers["Location"]
    assert local.startswith(destino)
    assert "telefone" not in local and "90000" not in local and "nome" not in local
    assert "Cliente" not in _html(client.get(local))


def test_tela3_sem_csrf_400(client):
    assert client.post(URL_DADOS, data={"nome": "Cliente Exemplo", "telefone": "51 90000-0000"}).status_code == 400


def test_tela3_script_no_nome_e_escapado(client):
    html = _html(_post_dados(client, nome="<script>alert(1)</script>", telefone="51 9"))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


# ---------- Tela 4 ----------

@pytest.mark.parametrize("estado,textos", [
    ("confirmado", ["Agendamento confirmado", "Corte + barba – 45 min", "Barbeiro 2", "14/11/2026",
                    "10:00", "Serviço", "Barbeiro", "Data", "Hora", "Voltar ao início", "<table"]),
    ("fila_horario", ["Você está na fila de espera para 14/11/2026 às 11:00",
                      "Vamos chamar você pelo WhatsApp se surgir vaga em qualquer barbeiro neste horário.",
                      "Voltar ao início"]),
    ("fila_barbeiro", ["Você está na fila do Barbeiro 1 para 14/11/2026 às 10:00",
                       "Vamos chamar você pelo WhatsApp se o Barbeiro 1 liberar este horário.",
                       "Voltar ao início"]),
])
def test_tela4_estados(client, estado, textos):
    resp = client.get(URL_RESULT[estado])
    assert resp.status_code == 200
    html = _html(resp)
    for texto in textos:
        assert texto in html, texto
    assert 'aria-live="polite"' in html and "<h1>" in html


def test_tela4_estado_invalido_404(client):
    resp = client.get(_url("/resultado/x", hora="10:00", barbeiro=2))
    assert resp.status_code == 404
    assert "Traceback" not in _html(resp)


def test_tela4_parametros_invalidos_voltam_ao_inicio(client):
    assert client.get("/resultado/confirmado").status_code == 302


# ---------- todas as telas ----------

@pytest.mark.parametrize("url", TODAS)
def test_datas_em_ptbr_sem_data_errada(client, url):
    html = _html(client.get(url))
    assert '<html lang="pt-BR">' in html
    assert "11/03/2026" not in html
    assert not re.search(r"\b11/14/2026\b", html)  # nada em mm/dd/aaaa


@pytest.mark.parametrize("url", TODAS)
def test_sem_script_inline_e_com_csp(client, url):
    resp = client.get(url)
    html = _html(resp)
    for tag in re.findall(r"<script[^>]*>", html, re.I):
        assert re.search(r'src="/static/', tag), tag  # só arquivo local
    assert not re.search(r"<script[^>]*>\s*[^<\s]", html)  # sem código entre as tags
    assert not re.search(r"\son\w+=", html)  # sem onclick/onchange
    assert resp.headers["Content-Security-Policy"] == "default-src 'self'"


@pytest.mark.parametrize("url", TODAS)
def test_sem_recursos_externos_e_logo(client, url):
    html = _html(client.get(url))
    assert not re.search(r'(src|href)="https?://', html)
    assert 'src="/static/img/logo-red.png" alt="Logo RED Barbearia"' in html


def test_sem_imagem_em_templates():
    from pathlib import Path
    pasta = Path(__file__).resolve().parents[2] / "app" / "web" / "templates"
    assert not [p for p in pasta.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".svg", ".webp"}]


def test_sem_secret_key_falha(monkeypatch):
    from app import create_app
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        create_app()


def test_erro_500_forcado_e_generico_sem_rastreio():
    """RNF02: erro 500 mostra só a mensagem genérica, sem rastreio, caminho ou SQL."""
    from app import create_app
    app = create_app({"TESTING": True, "SECRET_KEY": "chave-de-teste",
                      "SESSION_COOKIE_SECURE": False, "PROPAGATE_EXCEPTIONS": False})

    @app.route("/forcar-erro")
    def forcar_erro():
        raise RuntimeError("SELECT * FROM cliente /tmp/segredo.py")

    resp = app.test_client().get("/forcar-erro")
    html = _html(resp)
    assert resp.status_code == 500
    assert "Não foi possível confirmar agora. Tente novamente." in html
    for vazamento in ("Traceback", "RuntimeError", "SELECT", "segredo.py", "File \""):
        assert vazamento not in html
