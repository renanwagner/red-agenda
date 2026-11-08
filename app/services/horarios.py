"""Regras de horário livre (RF01, RF03). Funções puras: recebem intervalos, sem Flask nem SQL.

Intervalos são pares (início, fim) de datetime, fechados no início e abertos no fim.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

PASSO_MIN = 30  # intervalo entre os horários oferecidos na Tela 1


@dataclass
class AgendaDoDia:
    """Agenda de um barbeiro em um dia."""
    abertas: list = field(default_factory=list)      # janelas tipo "aberto"
    bloqueadas: list = field(default_factory=list)   # janelas tipo "bloqueado"
    ocupados: list = field(default_factory=list)     # agendamentos confirmados


def intervalo(data, hora, duracao_min):
    """Início e fim do serviço: fim = início + duração."""
    inicio = datetime.combine(data, hora)
    return inicio, inicio + timedelta(minutes=duracao_min)


def _sobrepoe(a, b):
    return a[0] < b[1] and b[0] < a[1]


def _unir(intervalos):
    """Une janelas contíguas ou sobrepostas (09:00–10:00 + 10:00–11:00 = 09:00–11:00)."""
    unidos = []
    for ini, fim in sorted(intervalos):
        if unidos and ini <= unidos[-1][1]:
            unidos[-1] = (unidos[-1][0], max(unidos[-1][1], fim))
        else:
            unidos.append((ini, fim))
    return unidos


def barbeiro_livre(inicio, fim, agenda):
    """O serviço cabe inteiro numa janela aberta, sem bloqueio nem agendamento confirmado no caminho."""
    dentro = any(ini <= inicio and fim <= f for ini, f in _unir(agenda.abertas))
    if not dentro:
        return False
    alvo = (inicio, fim)
    return not any(_sobrepoe(alvo, x) for x in (*agenda.bloqueadas, *agenda.ocupados))


def barbeiros_livres(inicio, fim, agendas):
    """Ids dos barbeiros livres no intervalo, em ordem. `agendas`: {id_barbeiro: AgendaDoDia}."""
    return sorted(i for i, agenda in agendas.items() if barbeiro_livre(inicio, fim, agenda))


def horarios_de_atendimento(agendas, passo_min=PASSO_MIN):
    """Tela 1: inícios "HH:MM" de `passo_min` em `passo_min` (alinhados ao relógio) dentro de alguma
    janela aberta e fora de bloqueio. Agendamento não tira o horário: ocupado vira fila (caso d)."""
    passo = timedelta(minutes=passo_min)
    inicios = set()
    for agenda in agendas.values():
        for ini, fim in _unir(agenda.abertas):
            meia_noite = ini.replace(hour=0, minute=0, second=0, microsecond=0)
            passos = -(-(ini - meia_noite) // passo)  # arredonda para cima
            t = meia_noite + passos * passo
            while t < fim:
                if not any(b0 <= t < b1 for b0, b1 in agenda.bloqueadas):
                    inicios.add(t)
                t += passo
    return [t.strftime("%H:%M") for t in sorted(inicios)]


def sugestoes(id_escolhido, livres):
    """RF03: os outros barbeiros livres no mesmo horário (escolha do cliente, sem troca automática)."""
    return [i for i in livres if i != id_escolhido]
