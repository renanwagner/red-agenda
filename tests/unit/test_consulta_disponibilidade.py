"""RF01 e RF03 a partir do banco: janelas, bloqueios, agendamentos e barbeiros ativos."""
from datetime import date, datetime, time

from sqlalchemy import select

from app.models import Agendamento, Barbeiro, Cliente, JanelaAtendimento, Servico
from app.services.consulta_disponibilidade import barbeiros_livres_no_horario, sugestoes_no_horario

DIA = date(2026, 11, 14)


def _cenario(db):
    """Barbeiros 1 e 2 ativos, 3 inativo; janela 09:00–10:00 para todos; Barbeiro 1 ocupado 09:00–09:30."""
    barbeiros = [Barbeiro(nome=f"Barbeiro {i}", email=f"b{i}@exemplo.com", senha_hash="h",
                          papel="barbeiro", ativo=(i != 3)) for i in (1, 2, 3)]
    corte, corte_barba = Servico(nome="Corte", duracao_min=30), Servico(nome="Corte + barba", duracao_min=45)
    cliente = Cliente(nome="Cliente Exemplo", telefone="51900000000")
    db.session.add_all([*barbeiros, corte, corte_barba, cliente])
    db.session.flush()
    for b in barbeiros:
        db.session.add(JanelaAtendimento(barbeiro_id=b.id_barbeiro, data=DIA,
                                         hora_inicio=time(9), hora_fim=time(10), tipo="aberto"))
    db.session.add(Agendamento(cliente_id=cliente.id_cliente, barbeiro_id=barbeiros[0].id_barbeiro,
                               servico_id=corte.id_servico, inicio=datetime(2026, 11, 14, 9),
                               fim=datetime(2026, 11, 14, 9, 30), status="confirmado", origem="link"))
    db.session.commit()
    return barbeiros, corte, corte_barba, cliente


def test_rf01_exemplo_do_documento_no_banco(banco):
    (b1, b2, _), corte, corte_barba, _ = _cenario(banco)
    # Só o Barbeiro 1: 09:30 com 45 min não cabe; com 30 min cabe
    assert b1.id_barbeiro not in barbeiros_livres_no_horario(corte_barba.id_servico, DIA, time(9, 30))
    assert b1.id_barbeiro in barbeiros_livres_no_horario(corte.id_servico, DIA, time(9, 30))


def test_inativo_nao_aparece_e_ocupado_fica_de_fora(banco):
    (b1, b2, b3), corte, _, _ = _cenario(banco)
    assert barbeiros_livres_no_horario(corte.id_servico, DIA, time(9)) == [b2.id_barbeiro]


def test_cancelado_nao_ocupa_horario(banco):
    (b1, b2, _), corte, _, _ = _cenario(banco)
    banco.session.scalar(select(Agendamento)).status = "cancelado"
    banco.session.commit()
    assert barbeiros_livres_no_horario(corte.id_servico, DIA, time(9)) == [b1.id_barbeiro, b2.id_barbeiro]


def test_bloqueio_e_outra_data_sao_respeitados(banco):
    (b1, b2, _), corte, _, _ = _cenario(banco)
    banco.session.add(JanelaAtendimento(barbeiro_id=b2.id_barbeiro, data=DIA,
                                        hora_inicio=time(9, 30), hora_fim=time(10), tipo="bloqueado"))
    banco.session.commit()
    assert barbeiros_livres_no_horario(corte.id_servico, DIA, time(9, 30)) == [b1.id_barbeiro]
    assert barbeiros_livres_no_horario(corte.id_servico, date(2026, 11, 15), time(9, 30)) == []


def test_servico_inexistente_ou_inativo_nao_tem_livres(banco):
    _, corte, _, _ = _cenario(banco)
    assert barbeiros_livres_no_horario(9999, DIA, time(9)) == []
    corte.ativo = False
    banco.session.commit()
    assert barbeiros_livres_no_horario(corte.id_servico, DIA, time(9)) == []


def test_rf03_sugere_b_quando_a_esta_ocupado(banco):
    (b1, b2, _), corte, _, _ = _cenario(banco)
    assert sugestoes_no_horario(b1.id_barbeiro, corte.id_servico, DIA, time(9)) == [b2.id_barbeiro]


def test_rf03_sem_ninguem_livre_lista_vazia(banco):
    (b1, _, _), corte, _, _ = _cenario(banco)
    assert sugestoes_no_horario(b1.id_barbeiro, corte.id_servico, DIA, time(10)) == []
