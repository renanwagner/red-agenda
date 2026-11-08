"""Tela 4 definida pelo servidor: o estado vem do registro gravado, não da URL (etapa 5)."""
from app.repositories import resultados as repo


def resultado(tipo, id_registro, duplicada=False):
    """Resumo para a Tela 4, ou None se o registro não existe ou não está mais no estado mostrado.

    tipo "agendamento": só `confirmado`. Tipo "fila": só `aguardando`; barbeiro None = fila por horário.
    """
    if tipo == "agendamento":
        r = repo.resumo_agendamento(id_registro)
        if r is None or r["status"] != "confirmado":
            return None
        estado = "confirmado"
    elif tipo == "fila":
        r = repo.resumo_entrada(id_registro)
        if r is None or r["status"] != "aguardando":
            return None
        estado = "fila_barbeiro" if r["barbeiro"] else "fila_horario"
    else:
        return None
    return {
        "estado": estado,
        "duplicada": bool(duplicada) and tipo == "fila",
        "servico": r["servico"],
        "barbeiro": r["barbeiro"],
        "data": r["data"],
        "hora": r["hora"].strftime("%H:%M"),
    }
