"""Disponibilidade a partir do banco (RF01, RF03). Lê pelos repositórios e aplica as regras puras."""
from app.repositories import agenda as repo
from app.services.horarios import AgendaDoDia, barbeiros_livres, intervalo, sugestoes


def barbeiros_livres_no_horario(id_servico, data, hora):
    """Ids dos barbeiros ativos em que o serviço cabe inteiro a partir de `hora`."""
    duracao = repo.duracao_servico_ativo(id_servico)
    if duracao is None:
        return []
    agendas = {i: AgendaDoDia(**dados) for i, dados in repo.agendas_do_dia(data).items()}
    return barbeiros_livres(*intervalo(data, hora, duracao), agendas)


def sugestoes_no_horario(id_escolhido, id_servico, data, hora):
    """RF03: outros barbeiros livres no mesmo horário, para o mesmo serviço e data."""
    return sugestoes(id_escolhido, barbeiros_livres_no_horario(id_servico, data, hora))
