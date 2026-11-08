"""Disponibilidade a partir do banco (RF01, RF03). Lê pelos repositórios e aplica as regras puras."""
from app.repositories import agenda as repo
from app.services.horarios import (
    AgendaDoDia, barbeiros_livres, horarios_de_atendimento, intervalo, sugestoes,
)


def _agendas(data):
    return {i: AgendaDoDia(**dados) for i, dados in repo.agendas_do_dia(data).items()}


def horarios_do_dia(data):
    """Tela 1: horários de atendimento na data, de 30 em 30 minutos."""
    return horarios_de_atendimento(_agendas(data))


def barbeiros_livres_no_horario(id_servico, data, hora):
    """Ids dos barbeiros ativos em que o serviço cabe inteiro a partir de `hora`."""
    duracao = repo.duracao_servico_ativo(id_servico)
    if duracao is None:
        return []
    return barbeiros_livres(*intervalo(data, hora, duracao), _agendas(data))


def sugestoes_no_horario(id_escolhido, id_servico, data, hora):
    """RF03: outros barbeiros livres no mesmo horário, para o mesmo serviço e data."""
    return sugestoes(id_escolhido, barbeiros_livres_no_horario(id_servico, data, hora))
