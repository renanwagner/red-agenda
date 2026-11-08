import pytest

from app.services.disponibilidade import (
    caso_disponibilidade, estado_coerente, modo_coerente,
)

Q = "qualquer"


@pytest.mark.parametrize("barbeiro,livres,caso", [
    (2, (2, 3), "a"), (1, (2, 3), "b"), (1, (), "b"), (Q, (2,), "c"), (Q, (), "d"),
])
def test_caso_disponibilidade(barbeiro, livres, caso):
    assert caso_disponibilidade(barbeiro, livres, Q) == caso


@pytest.mark.parametrize("modo,barbeiro,livres,esperado", [
    ("confirmacao", 2, (2,), True), ("confirmacao", 1, (2,), False), ("confirmacao", Q, (2,), False),
    ("fila_barbeiro", 1, (2,), True), ("fila_barbeiro", 2, (2,), False), ("fila_barbeiro", Q, (), False),
    ("fila_horario", Q, (), True), ("fila_horario", Q, (2,), False), ("fila_horario", 1, (), False),
    ("invalido", 1, (2,), False),
])
def test_modo_coerente(modo, barbeiro, livres, esperado):
    assert modo_coerente(modo, barbeiro, livres, Q) is esperado


@pytest.mark.parametrize("estado,barbeiro,esperado", [
    ("fila_horario", Q, True), ("fila_horario", 1, False),
    ("confirmado", 1, True), ("confirmado", Q, False),
    ("fila_barbeiro", 1, True), ("fila_barbeiro", Q, False),
])
def test_estado_coerente(estado, barbeiro, esperado):
    assert estado_coerente(estado, barbeiro, Q) is esperado
