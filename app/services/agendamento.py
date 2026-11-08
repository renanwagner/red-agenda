"""RF02: registrar agendamento. Revalida a sobreposição na mesma transação da gravação."""
import re
from dataclasses import dataclass

from app.repositories import agenda as repo_agenda
from app.repositories import agendamentos as repo
from app.services.horarios import AgendaDoDia, barbeiro_livre, intervalo


@dataclass
class Resultado:
    confirmado: bool
    id_agendamento: int | None = None


RECUSADO = Resultado(confirmado=False)


def normalizar_telefone(telefone):
    """Guarda só os dígitos (DDD + número). O formato já foi validado no formulário."""
    return re.sub(r"\D", "", telefone)


def confirmar_agendamento(id_servico, id_barbeiro, data, hora, nome, telefone):
    """Grava o agendamento `confirmado`/`link` se o horário ainda estiver livre; senão, recusa sem gravar."""
    repo.nova_transacao()
    try:
        # Trava primeiro e só depois lê a agenda: duas gravações no mesmo barbeiro ficam em fila
        if not repo.travar_barbeiro_ativo(id_barbeiro):
            repo.desfazer_transacao()
            return RECUSADO
        duracao = repo_agenda.duracao_servico_ativo(id_servico)
        if duracao is None:
            repo.desfazer_transacao()
            return RECUSADO
        inicio, fim = intervalo(data, hora, duracao)
        agenda = AgendaDoDia(**repo_agenda.agendas_do_dia(data, id_barbeiro)[id_barbeiro])
        if not barbeiro_livre(inicio, fim, agenda):
            repo.desfazer_transacao()
            return RECUSADO
        id_cliente = repo.obter_ou_criar_cliente(nome, normalizar_telefone(telefone))
        id_agendamento = repo.criar_agendamento(id_cliente, id_barbeiro, id_servico, inicio, fim)
        repo.confirmar_transacao()
        return Resultado(confirmado=True, id_agendamento=id_agendamento)
    except Exception:
        repo.desfazer_transacao()
        raise
