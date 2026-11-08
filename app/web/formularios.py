"""Formulários com validação no servidor e CSRF (RNF02)."""
import re
from datetime import time

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Length, ValidationError

MSG_TELEFONE = "Telefone incompleto. Informe DDD e número, como 51 90000-0000"
MSG_NOME = "Informe seu nome."
MSG_EMAIL = "Informe o e-mail."
MSG_SENHA = "Informe a senha."


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


MSG_INICIO = "Informe o início."
MSG_FIM = "Informe o fim."


def _hora_valida(mensagem):
    def validar(_form, campo):
        if not re.fullmatch(r"\d{2}:\d{2}", campo.data or ""):
            raise ValidationError(mensagem)
        try:
            time.fromisoformat(campo.data)
        except ValueError:
            raise ValidationError(mensagem) from None
    return validar


class JanelaForm(FlaskForm):
    """RF07. Hora como texto HH:MM (campo type=time); fim > início é regra da camada de serviços."""

    inicio = StringField("Início", filters=[_limpar],
                         validators=[DataRequired(message=MSG_INICIO), _hora_valida(MSG_INICIO)])
    fim = StringField("Fim", filters=[_limpar], validators=[DataRequired(message=MSG_FIM), _hora_valida(MSG_FIM)])
    # Botões de opção desenhados no template; valor fora de "aberto"/"bloqueado" vira 400 na rota
    tipo = StringField("Tipo", default="aberto")


class EntrarForm(FlaskForm):
    """Login do painel (RF08). Só confere preenchimento; a verificação é na camada de regras."""

    email = StringField("E-mail", filters=[_limpar],
                        validators=[DataRequired(message=MSG_EMAIL), Length(max=120, message=MSG_EMAIL)])
    senha = PasswordField("Senha", validators=[DataRequired(message=MSG_SENHA)])
