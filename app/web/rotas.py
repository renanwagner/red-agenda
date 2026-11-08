"""Rotas do fluxo do cliente (protótipo, sem banco).

Fluxo: Tela 1 (escolha) → Tela 2 (disponibilidade) → Tela 3 (dados) → Tela 4 (resultado).
"""
from datetime import date

from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.web import dados_demo as demo
from app.web.formularios import DadosForm

bp = Blueprint("web", __name__)

MODOS = ("confirmacao", "fila_horario", "fila_barbeiro")
ESTADO_DO_MODO = {"confirmacao": "confirmado", "fila_horario": "fila_horario", "fila_barbeiro": "fila_barbeiro"}


# ---------- auxiliares de apresentação ----------

def _por_id(lista, chave, valor):
    try:
        valor = int(valor)
    except (TypeError, ValueError):
        return None
    return next((item for item in lista if item[chave] == valor), None)


def _servico(valor):
    return _por_id(demo.SERVICOS, "id_servico", valor)


def _barbeiro(valor):
    """Barbeiro específico, "qualquer" ou None se inválido."""
    if valor == demo.QUALQUER:
        return {"id_barbeiro": demo.QUALQUER, "nome": demo.NOME_QUALQUER}
    return _por_id(demo.BARBEIROS, "id_barbeiro", valor)


def _data(valor):
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        return None


def _hora(valor):
    return valor if valor in demo.HORARIOS else None


def data_br(d):
    return d.strftime("%d/%m/%Y")


def servico_txt(s):
    return f"{s['nome']} – {s['duracao_min']} min"


def _selecao(args):
    return {
        "servico": _servico(args.get("servico")),
        "data": _data(args.get("data")),
        "hora": _hora(args.get("hora")),
        "barbeiro": _barbeiro(args.get("barbeiro")),
    }


def _params(sel, **extra):
    """Parâmetros de URL que mantêm a escolha entre as telas."""
    p = {}
    if sel["servico"]:
        p["servico"] = sel["servico"]["id_servico"]
    if sel["data"]:
        p["data"] = sel["data"].isoformat()
    if sel["hora"]:
        p["hora"] = sel["hora"]
    if sel["barbeiro"]:
        p["barbeiro"] = sel["barbeiro"]["id_barbeiro"]
    p.update(extra)
    return p


def _completa(sel):
    return all(sel.values())


def _livres(hora):
    """Barbeiros livres no horário, segundo os dados de demonstração."""
    return [_barbeiro(i) for i in demo.DISPONIBILIDADE.get(hora, ())]


def _modo_coerente(sel, modo):
    # Protótipo: confere o modo contra a disponibilidade demo (vai para services/ depois)
    livres_ids = demo.DISPONIBILIDADE[sel["hora"]]
    especifico = sel["barbeiro"]["id_barbeiro"] != demo.QUALQUER
    if modo == "confirmacao":
        return especifico and sel["barbeiro"]["id_barbeiro"] in livres_ids
    if modo == "fila_barbeiro":
        return especifico and sel["barbeiro"]["id_barbeiro"] not in livres_ids
    if modo == "fila_horario":
        return not especifico and not livres_ids
    return False


@bp.app_context_processor
def _filtros():
    return {"data_br": data_br, "servico_txt": servico_txt}


# ---------- Tela 1: escolha ----------

@bp.get("/")
def escolha():
    args = request.args.to_dict()
    # Botões de opção enviam "escolher=campo:valor"; o restante vem dos campos ocultos
    campo, _, valor = args.pop("escolher", "").partition(":")
    if campo in ("servico", "hora", "barbeiro"):
        args[campo] = valor
    sel = _selecao(args)
    if not sel["data"]:
        sel["data"] = demo.DATA_PADRAO
    if not sel["barbeiro"]:
        sel["barbeiro"] = _barbeiro(demo.QUALQUER)
    return render_template(
        "tela1_escolha.html",
        servicos=demo.SERVICOS,
        horarios=demo.HORARIOS,
        barbeiros=[_barbeiro(demo.QUALQUER), *demo.BARBEIROS],
        sel=sel,
        completa=_completa(sel),
        foco_data=request.args.get("foco") == "data",
    )


# ---------- Tela 2: disponibilidade ----------

@bp.get("/disponibilidade")
def disponibilidade():
    sel = _selecao(request.args)
    if not _completa(sel):
        return redirect(url_for("web.escolha", **_params(sel)))
    livres = _livres(sel["hora"])
    barbeiro = sel["barbeiro"]
    if barbeiro["id_barbeiro"] == demo.QUALQUER:
        caso = "c" if livres else "d"
    else:
        caso = "a" if barbeiro in livres else "b"
    outros = [b for b in livres if b != barbeiro]
    return render_template(
        "tela2_disponibilidade.html",
        sel=sel,
        caso=caso,
        outros=outros,
        params=_params(sel),
    )


# ---------- Tela 3: dados do cliente ----------

def _sel_tela3():
    sel = _selecao(request.args)
    modo = request.args.get("modo")
    if not _completa(sel):
        return None, None, redirect(url_for("web.escolha", **_params(sel)))
    if modo not in MODOS or not _modo_coerente(sel, modo):
        return None, None, redirect(url_for("web.disponibilidade", **_params(sel)))
    return sel, modo, None


def _render_tela3(sel, modo, form):
    return render_template(
        "tela3_dados.html",
        sel=sel,
        modo=modo,
        form=form,
        exemplo=demo.CLIENTE_EXEMPLO,
        params=_params(sel),
        acao=url_for("web.dados", **_params(sel, modo=modo)),
    )


@bp.get("/dados")
def dados():
    sel, modo, desvio = _sel_tela3()
    if desvio:
        return desvio
    return _render_tela3(sel, modo, DadosForm(formdata=None))


@bp.post("/dados")
def enviar_dados():
    sel, modo, desvio = _sel_tela3()
    if desvio:
        return desvio
    form = DadosForm()
    if form.validate_on_submit():
        # Protótipo: não grava. Nome e telefone não vão para a URL.
        return redirect(url_for("web.resultado", estado=ESTADO_DO_MODO[modo], **_params(sel)))
    return _render_tela3(sel, modo, form)


# ---------- Tela 4: resultado ----------

@bp.get("/resultado/<estado>")
def resultado(estado):
    if estado not in ESTADO_DO_MODO.values():
        abort(404)
    sel = _selecao(request.args)
    if not _completa(sel):
        return redirect(url_for("web.escolha"))
    qualquer = sel["barbeiro"]["id_barbeiro"] == demo.QUALQUER
    if qualquer != (estado == "fila_horario"):
        return redirect(url_for("web.escolha"))
    return render_template("tela4_resultado.html", estado=estado, sel=sel)
