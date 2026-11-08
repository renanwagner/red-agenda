"""RF02: gravação do agendamento com revalidação de sobreposição na mesma transação."""
import threading
from datetime import date, datetime, time

import pytest
from flask import current_app
from sqlalchemy import func, select

from app.models import Agendamento, Barbeiro, Cliente, JanelaAtendimento, Servico
from app.services.agendamento import confirmar_agendamento, normalizar_telefone

DIA = date(2026, 11, 14)
TEL = "51 90000-0000"


@pytest.fixture
def cenario(banco):
    """Barbeiro 1 com janela 09:00–12:00; Corte (30 min) e Corte + barba (45 min)."""
    b = Barbeiro(nome="Barbeiro 1", email="b1@exemplo.com", senha_hash="h", papel="barbeiro")
    corte, corte_barba = Servico(nome="Corte", duracao_min=30), Servico(nome="Corte + barba", duracao_min=45)
    banco.session.add_all([b, corte, corte_barba])
    banco.session.flush()
    banco.session.add(JanelaAtendimento(barbeiro_id=b.id_barbeiro, data=DIA, hora_inicio=time(9),
                                        hora_fim=time(12), tipo="aberto"))
    # Ids lidos antes do commit: ler depois reabriria uma transação (e a trava) nesta thread
    ids = {"barbeiro": b.id_barbeiro, "corte": corte.id_servico, "corte_barba": corte_barba.id_servico}
    banco.session.commit()
    return ids


def _confirma(c, hora=time(10), servico="corte", telefone=TEL, nome="Cliente Exemplo", barbeiro=None):
    return confirmar_agendamento(c[servico], barbeiro or c["barbeiro"], DIA, hora, nome, telefone)


def _conta(db, modelo):
    return db.session.scalar(select(func.count()).select_from(modelo))


@pytest.mark.parametrize("entrada,saida", [("51 90000-0000", "51900000000"), ("(51) 3000-0000", "5130000000")])
def test_normalizar_telefone_guarda_so_digitos(entrada, saida):
    assert normalizar_telefone(entrada) == saida


def test_grava_confirmado_pelo_link_com_fim_pela_duracao(banco, cenario):
    r = _confirma(cenario, servico="corte_barba")
    assert r.confirmado
    a = banco.session.get(Agendamento, r.id_agendamento)
    assert (a.status, a.origem) == ("confirmado", "link")
    assert a.inicio == datetime(2026, 11, 14, 10) and a.fim == datetime(2026, 11, 14, 10, 45)
    cliente = banco.session.get(Cliente, a.cliente_id)
    assert (cliente.nome, cliente.telefone) == ("Cliente Exemplo", "51900000000")


def test_mesmo_telefone_reaproveita_o_cliente(banco, cenario):
    assert _confirma(cenario, hora=time(9)).confirmado
    assert _confirma(cenario, hora=time(11), telefone="(51) 90000-0000", nome="Outro nome").confirmado
    assert _conta(banco, Cliente) == 1
    assert _conta(banco, Agendamento) == 2


def test_horario_ocupado_e_recusado_sem_gravar(banco, cenario):
    assert _confirma(cenario, hora=time(10)).confirmado
    r = _confirma(cenario, hora=time(10, 15), telefone="51 90000-0001")   # sobrepõe 10:00–10:30
    assert not r.confirmado and r.id_agendamento is None
    assert _conta(banco, Agendamento) == 1
    assert _conta(banco, Cliente) == 1    # o cliente recusado não fica gravado


def test_encostado_no_anterior_e_aceito(cenario):
    assert _confirma(cenario, hora=time(10)).confirmado
    assert _confirma(cenario, hora=time(10, 30), telefone="51 90000-0001").confirmado


def test_fora_da_janela_e_recusado(banco, cenario):
    assert not _confirma(cenario, hora=time(11, 45)).confirmado    # 11:45 + 30 > 12:00
    assert not _confirma(cenario, hora=time(8, 30)).confirmado
    assert _conta(banco, Agendamento) == 0


def test_cancelado_libera_o_horario(banco, cenario):
    r = _confirma(cenario)
    banco.session.get(Agendamento, r.id_agendamento).status = "cancelado"
    banco.session.commit()
    assert _confirma(cenario, telefone="51 90000-0001").confirmado


def test_barbeiro_ou_servico_inativo_e_recusado(banco, cenario):
    banco.session.get(Servico, cenario["corte"]).ativo = False
    banco.session.commit()
    assert not _confirma(cenario).confirmado
    banco.session.get(Servico, cenario["corte"]).ativo = True
    banco.session.get(Barbeiro, cenario["barbeiro"]).ativo = False
    banco.session.commit()
    assert not _confirma(cenario).confirmado
    assert not _confirma(cenario, barbeiro=9999).confirmado
    assert _conta(banco, Agendamento) == 0


@pytest.mark.parametrize("n_requisicoes", [2, 5])
def test_requisicoes_simultaneas_um_confirmado_e_o_resto_recusado(banco, cenario, n_requisicoes):
    app = current_app._get_current_object()
    largada = threading.Barrier(n_requisicoes)
    resultados, erros = [], []

    def tentar(i):
        try:
            with app.app_context():
                largada.wait()
                resultados.append(_confirma(cenario, telefone=f"51 90000-000{i}").confirmado)
        except Exception as erro:  # noqa: BLE001 - o teste precisa ver qualquer falha da thread
            erros.append(erro)

    threads = [threading.Thread(target=tentar, args=(i,)) for i in range(n_requisicoes)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert not erros, erros
    assert sorted(resultados) == [False] * (n_requisicoes - 1) + [True]
    banco.session.expire_all()
    assert _conta(banco, Agendamento) == 1


def test_falha_no_meio_da_gravacao_desfaz_tudo(banco, cenario, monkeypatch):
    from app.repositories import agendamentos as repo

    def quebra(*_args):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(repo, "criar_agendamento", quebra)
    with pytest.raises(RuntimeError):
        _confirma(cenario)
    assert _conta(banco, Cliente) == 0 and _conta(banco, Agendamento) == 0


def test_telefone_criado_por_outro_pedido_ao_mesmo_tempo_e_reaproveitado(banco, monkeypatch):
    from app.repositories import agendamentos as repo

    banco.session.add(Cliente(nome="Cliente Exemplo", telefone="51900000000"))
    banco.session.commit()
    original = banco.session.scalar
    chamadas = []

    def primeira_busca_nao_ve(consulta):
        chamadas.append(1)
        return None if len(chamadas) == 1 else original(consulta)   # simula a corrida

    monkeypatch.setattr(banco.session, "scalar", primeira_busca_nao_ve)
    id_cliente = repo.obter_ou_criar_cliente("Outro nome", "51900000000")
    monkeypatch.undo()
    repo.confirmar_transacao()
    assert id_cliente is not None and _conta(banco, Cliente) == 1
