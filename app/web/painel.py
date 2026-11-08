"""Painel do barbeiro: entrar, sair e página inicial (RF08, RNF01)."""
from functools import wraps

from flask import Blueprint, abort, current_app, redirect, render_template, session, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user

from app.services import autenticacao
from app.web.formularios import EntrarForm

bp = Blueprint("painel", __name__, url_prefix="/painel")
login_manager = LoginManager()
login_manager.login_view = "painel.entrar"
login_manager.login_message = None      # sem mensagem padrão em inglês

MSG_INVALIDO = "E-mail ou senha incorretos. Confira e tente novamente."
MSG_BLOQUEIO = "Muitas tentativas. Tente novamente em 15 minutos."
CHAVE_TENTATIVAS = "red_tentativas"     # ControleTentativas desta aplicação (em memória)


class UsuarioPainel(UserMixin):
    def __init__(self, perfil):
        self.id = perfil["id_barbeiro"]
        self.nome = perfil["nome"]
        self.papel = perfil["papel"]

    @property
    def administrador(self):
        return self.papel == "administrador"


@login_manager.user_loader
def _carregar_usuario(id_barbeiro):
    perfil = autenticacao.barbeiro_da_sessao(id_barbeiro)
    return UsuarioPainel(perfil) if perfil else None   # inativado: a sessão deixa de valer


def iniciar(app):
    login_manager.init_app(app)
    app.extensions[CHAVE_TENTATIVAS] = autenticacao.ControleTentativas()
    app.register_blueprint(bp)


def exige_administrador(view):
    """Autorização no servidor (RNF01): só administrador; os demais recebem 403."""
    @wraps(view)
    def envolvida(*args, **kwargs):
        if not getattr(current_user, "administrador", False):
            abort(403)
        return view(*args, **kwargs)
    return envolvida


@bp.route("/entrar", methods=["GET", "POST"])
def entrar():
    form = EntrarForm()
    erro = None
    if form.validate_on_submit():
        r = autenticacao.autenticar(form.email.data, form.senha.data, current_app.extensions[CHAVE_TENTATIVAS])
        if r.status == "ok":
            session.clear()                 # sessão nova a cada login (contra fixação de sessão)
            session.permanent = True        # expira em PERMANENT_SESSION_LIFETIME (8 h)
            login_user(UsuarioPainel(r.barbeiro))
            return redirect(url_for("painel.inicio"))   # ignora "next": sem redirecionamento externo
        erro = MSG_BLOQUEIO if r.status == "bloqueado" else MSG_INVALIDO
    return render_template("painel_entrar.html", form=form, erro=erro)


@bp.post("/sair")
@login_required
def sair():
    logout_user()
    session.clear()
    return redirect(url_for("painel.entrar"))


@bp.get("")
@login_required
def inicio():
    return render_template("painel.html")
