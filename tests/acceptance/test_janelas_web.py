"""RF07 pelo painel: textos, permissões (próprias janelas / administrador escolhe) e mensagens."""
import re
from datetime import date

import pytest
from sqlalchemy import select
from werkzeug.security import generate_password_hash

from app.models import Barbeiro, JanelaAtendimento, db
from app.services.autenticacao import criar_administrador

SENHA = "senha-de-teste-1"
DIA = "2026-11-14"   # demonstração: cada barbeiro com janela 09:30–11:30; Barbeiro 1 lotado


@pytest.fixture
def contas(app):
    """Barbeiro 1 (comum, da demonstração) com senha conhecida e um administrador."""
    with app.app_context():
        b1 = db.session.get(Barbeiro, 1)
        b1.senha_hash = generate_password_hash(SENHA)
        db.session.commit()
        criar_administrador("Admin Exemplo", "admin@exemplo.com", SENHA)
    return {"comum": "barbeiro1@exemplo.com", "admin": "admin@exemplo.com"}


def _html(resp):
    return resp.get_data(as_text=True)


def _token(client, url):
    m = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', _html(client.get(url)))
    assert m, url
    return m.group(1)


def _entrar(client, email):
    t = _token(client, "/painel/entrar")
    assert client.post("/painel/entrar", data={"email": email, "senha": SENHA, "csrf_token": t}).status_code == 302


def _do_dia(app, barbeiro, dia=DIA):
    with app.app_context():
        return [(j.id_janela, j.hora_inicio.strftime("%H:%M"), j.hora_fim.strftime("%H:%M"), j.tipo)
                for j in db.session.scalars(select(JanelaAtendimento).where(
                    JanelaAtendimento.barbeiro_id == barbeiro,
                    JanelaAtendimento.data == date.fromisoformat(dia)).order_by(JanelaAtendimento.hora_inicio))]


def _criar(client, url, inicio, fim, tipo="aberto"):
    t = _token(client, url)
    return client.post(url, data={"inicio": inicio, "fim": fim, "tipo": tipo, "csrf_token": t},
                       follow_redirects=True)


def test_sem_login_redireciona(client):
    assert client.get("/painel/janelas").status_code == 302


def test_textos_da_tela(client, contas):
    _entrar(client, contas["comum"])
    html = _html(client.get(f"/painel/janelas?data={DIA}"))
    for texto in ["<h1>Janelas de atendimento</h1>", '<label class="rotulo" for="data">Data</label>', ">Ver dia</button>",
                  "09:30 – 11:30 · Aberta", ">Alterar</a>", ">Excluir</button>", "Nova janela",
                  '<label class="rotulo" for="inicio">Início</label>', '<label class="rotulo" for="fim">Fim</label>',
                  "<legend>Tipo</legend>", "Aberta", "Bloqueada", ">Salvar janela</button>"]:
        assert texto in html, texto
    assert 'for="barbeiro"' not in html                      # campo Barbeiro só para administrador
    assert "Nenhuma janela nesta data." in _html(client.get("/painel/janelas?data=2027-01-05"))


def test_painel_tem_link_para_as_janelas(client, contas):
    _entrar(client, contas["comum"])
    assert 'href="/painel/janelas"' in _html(client.get("/painel"))


def test_criar_janela_mostra_sucesso(app, client, contas):
    _entrar(client, contas["comum"])
    html = _html(_criar(client, f"/painel/janelas?data={DIA}", "14:00", "18:00"))
    assert "Janela salva." in html and "14:00 – 18:00 · Aberta" in html
    assert [j[1:] for j in _do_dia(app, 1)] == [("09:30", "11:30", "aberto"), ("14:00", "18:00", "aberto")]


@pytest.mark.parametrize("inicio,fim,mensagem", [
    ("", "12:00", "Informe o início."), ("09:00", "", "Informe o fim."), ("xx", "12:00", "Informe o início."),
    ("12:00", "09:00", "O fim precisa ser depois do início."),
    ("10:00", "12:00", "Já existe uma janela deste tipo nesse período."),
])
def test_erros_ao_criar(app, client, contas, inicio, fim, mensagem):
    _entrar(client, contas["comum"])
    resp = _criar(client, f"/painel/janelas?data={DIA}", inicio, fim)
    html = _html(resp)
    assert mensagem in html and 'aria-live="assertive"' in html and 'class="icone"' in html
    assert len(_do_dia(app, 1)) == 1


def test_bloqueio_sobre_agendamento_e_recusado(app, client, contas):
    _entrar(client, contas["comum"])
    html = _html(_criar(client, f"/painel/janelas?data={DIA}", "10:00", "10:30", tipo="bloqueado"))
    assert "Não é possível salvar: um agendamento confirmado ficaria fora do horário de atendimento." in html


def test_excluir_com_agendamento_confirmado_e_bloqueado(app, client, contas):
    _entrar(client, contas["comum"])
    (id_janela, *_), = _do_dia(app, 1)
    t = _token(client, f"/painel/janelas?data={DIA}")
    html = _html(client.post(f"/painel/janelas/{id_janela}/excluir", data={"csrf_token": t}, follow_redirects=True))
    assert "Não é possível excluir: há agendamento confirmado nesta janela." in html
    assert len(_do_dia(app, 1)) == 1


def test_excluir_sem_agendamento(app, client, contas):
    _entrar(client, contas["comum"])
    _criar(client, f"/painel/janelas?data={DIA}", "14:00", "18:00")
    id_nova = _do_dia(app, 1)[1][0]
    t = _token(client, f"/painel/janelas?data={DIA}")
    html = _html(client.post(f"/painel/janelas/{id_nova}/excluir", data={"csrf_token": t}, follow_redirects=True))
    assert "Janela excluída." in html and len(_do_dia(app, 1)) == 1


def test_alterar_janela(app, client, contas):
    _entrar(client, contas["comum"])
    _criar(client, f"/painel/janelas?data={DIA}", "14:00", "18:00")
    id_nova = _do_dia(app, 1)[1][0]
    url = f"/painel/janelas/{id_nova}/alterar"
    html = _html(client.get(url))
    assert "Alterar janela" in html and 'value="14:00"' in html and ">Cancelar</a>" in html
    resp = _criar(client, url, "15:00", "18:00")
    assert "Janela salva." in _html(resp)
    assert _do_dia(app, 1)[1][1:] == ("15:00", "18:00", "aberto")


def test_alterar_encolhendo_sobre_agendamento_e_recusado(app, client, contas):
    _entrar(client, contas["comum"])
    (id_janela, *_), = _do_dia(app, 1)
    html = _html(_criar(client, f"/painel/janelas/{id_janela}/alterar", "09:30", "10:00"))
    assert "Não é possível salvar: um agendamento confirmado ficaria fora do horário de atendimento." in html
    assert _do_dia(app, 1)[0][1:] == ("09:30", "11:30", "aberto")


def test_barbeiro_comum_nao_mexe_em_janela_de_outro(app, client, contas):
    _entrar(client, contas["comum"])
    (id_outro, *_), = _do_dia(app, 2)
    assert client.get(f"/painel/janelas/{id_outro}/alterar").status_code == 404
    t = _token(client, f"/painel/janelas?data={DIA}")
    assert client.post(f"/painel/janelas/{id_outro}/excluir", data={"csrf_token": t}).status_code == 404
    html = _html(client.get(f"/painel/janelas?data={DIA}&barbeiro=2"))      # parâmetro ignorado
    _criar(client, f"/painel/janelas?data={DIA}&barbeiro=2", "14:00", "18:00")
    assert len(_do_dia(app, 2)) == 1 and len(_do_dia(app, 1)) == 2
    assert "09:30 – 11:30 · Aberta" in html


def test_administrador_escolhe_o_barbeiro(app, client, contas):
    _entrar(client, contas["admin"])
    html = _html(client.get(f"/painel/janelas?data={DIA}&barbeiro=2"))
    assert '<label class="rotulo" for="barbeiro">Barbeiro</label>' in html and "Barbeiro 3" in html
    _criar(client, f"/painel/janelas?data={DIA}&barbeiro=2", "14:00", "18:00")
    assert len(_do_dia(app, 2)) == 2
    (id_b3, *_), = _do_dia(app, 3)
    assert client.get(f"/painel/janelas/{id_b3}/alterar").status_code == 200


def test_excluir_so_por_post_e_com_csrf(app, client, contas):
    _entrar(client, contas["comum"])
    (id_janela, *_), = _do_dia(app, 1)
    assert client.get(f"/painel/janelas/{id_janela}/excluir").status_code == 405
    assert client.post(f"/painel/janelas/{id_janela}/excluir").status_code == 400
    assert client.post(f"/painel/janelas?data={DIA}", data={"inicio": "14:00", "fim": "18:00",
                                                             "tipo": "aberto"}).status_code == 400


def test_tipo_forjado_e_requisicao_invalida(client, contas):
    _entrar(client, contas["comum"])
    assert _criar(client, f"/painel/janelas?data={DIA}", "14:00", "18:00", tipo="livre").status_code == 400


def test_data_invalida_na_url_usa_hoje(client, contas):
    _entrar(client, contas["comum"])
    html = _html(client.get("/painel/janelas?data=abc"))
    assert f'value="{date.today().isoformat()}"' in html


@pytest.mark.parametrize("parametro", ["", "&barbeiro=abc", "&barbeiro=9999"])
def test_administrador_sem_barbeiro_valido_ve_as_proprias(client, contas, parametro):
    _entrar(client, contas["admin"])
    html = _html(client.get(f"/painel/janelas?data={DIA}{parametro}"))
    assert re.search(r'<option value="\d+" selected>Admin Exemplo</option>', html)
    assert "Nenhuma janela nesta data." in html


def test_hora_impossivel_mostra_erro(app, client, contas):
    _entrar(client, contas["comum"])
    assert "Informe o início." in _html(_criar(client, f"/painel/janelas?data={DIA}", "25:99", "12:00"))


def test_tipo_forjado_com_outro_erro_tambem_e_400(app, client, contas):
    _entrar(client, contas["comum"])
    assert _criar(client, f"/painel/janelas?data={DIA}", "", "12:00", tipo="livre").status_code == 400
    (id_janela, *_), = _do_dia(app, 1)
    url = f"/painel/janelas/{id_janela}/alterar"
    assert _criar(client, url, "", "12:00", tipo="livre").status_code == 400
    assert _criar(client, url, "09:30", "11:30", tipo="livre").status_code == 400
