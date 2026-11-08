"""Criação da aplicação Flask (RED Agenda)."""
import os
from datetime import timedelta

from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()


def create_app(config=None):
    app = Flask(__name__, template_folder="web/templates", static_folder="web/static")

    # Segredos e modo vêm do ambiente (RNF01/RNF02)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        WTF_CSRF_TIME_LIMIT=None,  # sem limite de tempo no formulário público (RNF04)
    )
    if config:
        app.config.update(config)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Defina a variável de ambiente SECRET_KEY.")

    csrf.init_app(app)

    from app.web.rotas import bp

    app.register_blueprint(bp)

    @app.after_request
    def cabecalhos_seguranca(resposta):
        resposta.headers["Content-Security-Policy"] = "default-src 'self'"
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        return resposta

    # Erros genéricos, sem rastreio (RNF02)
    mensagens = {
        400: "Requisição inválida. Tente novamente.",
        403: "Acesso não permitido.",
        404: "Página não encontrada.",
        500: "Não foi possível confirmar agora. Tente novamente.",
    }

    def tratar_erro(erro):
        codigo = getattr(erro, "code", 500) or 500
        if codigo not in mensagens:
            codigo = 500
        return render_template("erro.html", mensagem=mensagens[codigo]), codigo

    for codigo in mensagens:
        app.register_error_handler(codigo, tratar_erro)

    return app
