"""Formulários com validação no servidor e CSRF (RNF02)."""
import re

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, ValidationError

MSG_TELEFONE = "Telefone incompleto. Informe DDD e número, como 51 90000-0000"
MSG_NOME = "Informe seu nome."


def _limpar(valor):
    return valor.strip() if isinstance(valor, str) else valor


def validar_telefone(_form, campo):
    # DDD + número: 10 ou 11 dígitos; aceita espaço, hífen e parênteses
    valor = campo.data or ""
    if not re.fullmatch(r"[\d\s()\-]+", valor):
        raise ValidationError(MSG_TELEFONE)
    digitos = re.sub(r"\D", "", valor)
    if len(digitos) not in (10, 11) or digitos[0] == "0":
        raise ValidationError(MSG_TELEFONE)


class DadosForm(FlaskForm):
    """Tela 3. Serviço, data, hora, barbeiro e modo vêm da URL e são validados na rota."""

    nome = StringField(
        "Nome",
        filters=[_limpar],
        validators=[DataRequired(message=MSG_NOME), Length(max=100, message=MSG_NOME)],
    )
    telefone = StringField(
        "Telefone (com DDD)",
        filters=[_limpar],
        validators=[DataRequired(message=MSG_TELEFONE), validar_telefone],
    )
