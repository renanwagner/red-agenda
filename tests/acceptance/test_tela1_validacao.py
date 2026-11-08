"""Ajustes da rodada 1 de validação na Tela 1: âncora para a próxima seção e horário "só fila de espera"."""
import re

SO_FILA = "só fila de espera"


def _html(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.get_data(as_text=True)


def _botao(html, valor):
    """Tag de abertura do botão de opção com o valor dado (ex.: 'hora:11:00')."""
    m = re.search(rf'<button[^>]*value="{re.escape(valor)}"[^>]*>', html, re.S)
    assert m, valor
    return m.group(0)


def test_cada_escolha_leva_a_proxima_secao(client):
    html = _html(client, "/?servico=2&data=2026-11-14")
    for alvo in ('id="horario"', 'id="barbeiro"', 'id="ver"'):
        assert alvo in html, alvo
    assert 'formaction="/#horario"' in _botao(html, "servico:1")
    assert 'formaction="/#barbeiro"' in _botao(html, "hora:10:00")
    assert 'formaction="/#ver"' in _botao(html, "barbeiro:qualquer")


def test_horario_sem_barbeiro_livre_mostra_so_fila(client):
    # Demonstração, Corte + barba em 14/11/2026: 11:00 → nenhum livre; 10:00 → Barbeiros 2 e 3
    html = _html(client, "/?servico=2&data=2026-11-14")
    assert re.search(rf'value="hora:11:00"[^>]*>\s*11:00 – {SO_FILA}</button>', html)
    assert re.search(r'value="hora:10:00"[^>]*>\s*10:00</button>', html)
    assert html.count(SO_FILA) == 1


def test_sem_servico_nao_ha_aviso_de_fila(client):
    assert SO_FILA not in _html(client, "/?data=2026-11-14")


def test_horario_so_fila_continua_selecionavel(client):
    html = _html(client, "/?servico=2&data=2026-11-14&barbeiro=qualquer&escolher=hora:11:00")
    assert "Selecionado: 11:00" in html
    assert re.search(rf'value="hora:11:00"[^>]*aria-pressed="true"[^>]*>.*?11:00 – {SO_FILA}</button>', html, re.S)
    assert not re.search(r"<button[^>]*disabled[^>]*>Ver disponibilidade", html)


def test_barbeiro_especifico_ocupado_com_outro_livre_nao_e_so_fila(client):
    # 10:00: Barbeiro 1 ocupado, mas 2 e 3 livres → a Tela 2 sugere os outros (RF03), não é "só fila"
    html = _html(client, "/?servico=2&data=2026-11-14&barbeiro=1")
    assert re.search(r'value="hora:10:00"[^>]*>\s*10:00</button>', html)
