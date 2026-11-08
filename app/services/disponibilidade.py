"""Regras de disponibilidade das Telas 2 e 3 (RF01, RF02). Sem Flask nem acesso a banco."""


def caso_disponibilidade(id_barbeiro, ids_livres_hora, qualquer):
    """Caso da Tela 2: a (livre), b (ocupado), c (qualquer com livres) ou d (qualquer sem livres)."""
    if id_barbeiro == qualquer:
        return "c" if ids_livres_hora else "d"
    return "a" if id_barbeiro in ids_livres_hora else "b"


def modo_coerente(modo, id_barbeiro, ids_livres_hora, qualquer):
    """Confere se o modo da Tela 3 combina com a disponibilidade do horário."""
    especifico = id_barbeiro != qualquer
    if modo == "confirmacao":
        return especifico and id_barbeiro in ids_livres_hora
    if modo == "fila_barbeiro":
        return especifico and id_barbeiro not in ids_livres_hora
    if modo == "fila_horario":
        return not especifico and not ids_livres_hora
    return False
