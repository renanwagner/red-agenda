"""Painel do barbeiro: entrar e sair (RF08, RNF01), janelas (RF07), agenda (RF06) e cancelamento (RF05)."""
from datetime import date, time
from functools import wraps

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user

from app.services import agenda_painel, autenticacao, cancelamento, catalogo, janelas
from app.web.formularios import EntrarForm, JanelaForm

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


# ---------- RF07: janelas de atendimento ----------

TIPOS_TEXTO = {"aberto": "Aberta", "bloqueado": "Bloqueada"}
MSG_JANELA = {
    "fim_antes": "O fim precisa ser depois do início.",
    "sobreposta": "Já existe uma janela deste tipo nesse período.",
    "agendamento_fora": "Não é possível salvar: um agendamento confirmado ficaria fora do horário de atendimento.",
}
MSG_EXCLUIR_COM_AGENDAMENTO = "Não é possível excluir: há agendamento confirmado nesta janela."


def _data_param():
    try:
        return date.fromisoformat(request.args.get("data", ""))
    except ValueError:
        return date.today()


def _barbeiro_alvo():
    """Barbeiro comum: sempre ele mesmo (parâmetro ignorado). Administrador: o escolhido, se ativo."""
    if not current_user.administrador:
        return current_user.id, []
    ativos = catalogo.barbeiros_ativos()
    try:
        escolhido = int(request.args.get("barbeiro", ""))
    except ValueError:
        escolhido = current_user.id
    if escolhido not in {b["id_barbeiro"] for b in ativos}:
        escolhido = current_user.id
    return escolhido, ativos


def _url_lista(data, id_barbeiro):
    extra = {"barbeiro": id_barbeiro} if current_user.administrador else {}
    return url_for("painel.janelas_lista", data=data.isoformat(), **extra)


def _tipo_ou_400(form):
    if form.tipo.data not in TIPOS_TEXTO:
        abort(400)
    return form.tipo.data


@bp.route("/janelas", methods=["GET", "POST"])
@login_required
def janelas_lista():
    data = _data_param()
    id_barbeiro, ativos = _barbeiro_alvo()
    form = JanelaForm()
    erro = None
    if request.method == "POST" and form.validate_on_submit():
        tipo = _tipo_ou_400(form)
        r = janelas.salvar(id_barbeiro, data, time.fromisoformat(form.inicio.data),
                           time.fromisoformat(form.fim.data), tipo)
        if r.ok:
            flash("Janela salva.", "sucesso")
            return redirect(_url_lista(data, id_barbeiro))
        erro = MSG_JANELA[r.erro]
    elif request.method == "POST" and form.tipo.data not in TIPOS_TEXTO:
        abort(400)
    return render_template(
        "painel_janelas.html", form=form, erro=erro, data=data, id_barbeiro=id_barbeiro, ativos=ativos,
        lista=janelas.listar(id_barbeiro, data), tipos=TIPOS_TEXTO,
        acao=_url_lista(data, id_barbeiro),
    )


def _janela_permitida(id_janela):
    """Janela que o usuário pode mexer (administrador: qualquer); senão 404."""
    j = janelas.obter(None if current_user.administrador else current_user.id, id_janela)
    if j is None:
        abort(404)
    return j


@bp.route("/janelas/<int:id_janela>/alterar", methods=["GET", "POST"])
@login_required
def janelas_alterar(id_janela):
    j = _janela_permitida(id_janela)
    form = JanelaForm(data={"inicio": j["hora_inicio"].strftime("%H:%M"),
                            "fim": j["hora_fim"].strftime("%H:%M"), "tipo": j["tipo"]})
    erro = None
    if form.validate_on_submit():
        tipo = _tipo_ou_400(form)
        r = janelas.salvar(None if current_user.administrador else current_user.id, j["data"],
                           time.fromisoformat(form.inicio.data), time.fromisoformat(form.fim.data),
                           tipo, id_janela=id_janela)
        if r.ok:
            flash("Janela salva.", "sucesso")
            return redirect(_url_lista(j["data"], j["barbeiro_id"]))
        erro = MSG_JANELA[r.erro]
    elif request.method == "POST" and form.tipo.data not in TIPOS_TEXTO:
        abort(400)
    return render_template("painel_janela_alterar.html", form=form, erro=erro, janela=j,
                           voltar=_url_lista(j["data"], j["barbeiro_id"]))


@bp.post("/janelas/<int:id_janela>/excluir")
@login_required
def janelas_excluir(id_janela):
    j = _janela_permitida(id_janela)
    r = janelas.excluir(None if current_user.administrador else current_user.id, id_janela)
    if r.ok:
        flash("Janela excluída.", "sucesso")
    else:
        flash(MSG_EXCLUIR_COM_AGENDAMENTO, "erro")
    return redirect(_url_lista(j["data"], j["barbeiro_id"]))


# ---------- RF06: agenda do dia e da semana ----------

DIAS_SEMANA = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo")


def dia_br(d):
    """date → 'sábado, 14/11/2026'."""
    return f"{DIAS_SEMANA[d.weekday()]}, {d.strftime('%d/%m/%Y')}"


@bp.get("/agenda")
@login_required
def agenda():
    data = _data_param()
    id_barbeiro, ativos = _barbeiro_alvo()      # barbeiro comum: só a própria agenda
    visao = "semana" if request.args.get("visao") == "semana" else "dia"
    if visao == "semana":
        dias = agenda_painel.da_semana(id_barbeiro, data)
    else:
        itens = agenda_painel.do_dia(id_barbeiro, data)
        dias = [{"data": data, "itens": itens}] if itens else []
    return render_template("painel_agenda.html", data=data, visao=visao, dias=dias,
                           id_barbeiro=id_barbeiro, ativos=ativos, dia_br=dia_br)


# ---------- RF05: cancelar e indicar o próximo da fila ----------

CHAVE_CANCELADO = "red_cancelado"   # na sessão assinada: só os ids {"agendamento", "espera"}
MSG_NAO_CANCELAVEL = "Este agendamento não pode mais ser cancelado."


def _dono():
    """Barbeiro comum: só os próprios agendamentos. Administrador: None (qualquer)."""
    return None if current_user.administrador else current_user.id


def _url_agenda(data, id_barbeiro):
    extra = {"barbeiro": id_barbeiro} if current_user.administrador else {}
    return url_for("painel.agenda", data=data.isoformat(), **extra)


@bp.route("/agendamentos/<int:id_agendamento>/cancelar", methods=["GET", "POST"])
@login_required
def cancelar(id_agendamento):
    ag = cancelamento.obter(id_agendamento, _dono())
    if ag is None:
        abort(404)                          # inexistente ou de outro barbeiro
    voltar = _url_agenda(ag["inicio"].date(), ag["barbeiro_id"])
    if request.method == "POST":            # CSRF conferido pelo CSRFProtect
        r = cancelamento.cancelar_e_chamar(id_agendamento, _dono())
        if r.ok:
            session[CHAVE_CANCELADO] = {"agendamento": id_agendamento, "espera": r.id_espera}
            return redirect(url_for("painel.cancelado"))
        if r.erro == "nao_encontrado":
            abort(404)
        flash(MSG_NAO_CANCELAVEL, "erro")
        return redirect(voltar)
    if ag["status"] != "confirmado":
        flash(MSG_NAO_CANCELAVEL, "erro")
        return redirect(voltar)
    return render_template("painel_cancelar.html", ag=ag, voltar=voltar, dia_br=dia_br)


@bp.get("/cancelado")
@login_required
def cancelado():
    estado = session.get(CHAVE_CANCELADO)
    ag = cancelamento.obter(estado["agendamento"], _dono()) if estado else None
    if ag is None:
        session.pop(CHAVE_CANCELADO, None)
        return redirect(url_for("painel.agenda"))
    chamado = cancelamento.resumo_chamado(estado["espera"]) if estado.get("espera") else None
    return render_template("painel_cancelado.html", chamado=chamado, dia_br=dia_br,
                           voltar=_url_agenda(ag["inicio"].date(), ag["barbeiro_id"]))


@bp.post("/cancelado/proximo")
@login_required
def cancelado_proximo():
    """Não conseguiu falar com o chamado: ele passa a `desistiu` e o painel indica o seguinte."""
    estado = session.get(CHAVE_CANCELADO)
    if not estado or not estado.get("espera"):
        return redirect(url_for("painel.cancelado"))
    r = cancelamento.chamar_proximo(estado["agendamento"], estado["espera"], _dono())
    if r.ok:
        session[CHAVE_CANCELADO] = {"agendamento": estado["agendamento"], "espera": r.id_espera}
    elif r.erro == "nao_encontrado":
        abort(404)
    return redirect(url_for("painel.cancelado"))
