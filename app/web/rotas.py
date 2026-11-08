"""Rotas do fluxo do cliente.

Fluxo: Tela 1 (escolha) → Tela 2 (disponibilidade) → Tela 3 (dados) → Tela 4 (resultado).
Serviços, barbeiros, horários e disponibilidade vêm da camada de regras (que lê o banco).
"""
from datetime import date, time

from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.services import agendamento, catalogo
from app.services import consulta_disponibilidade as consulta
from app.services import disponibilidade as regras
from app.web import dados_demo as demo
from app.web.formularios import DadosForm

bp = Blueprint("web", __name__)

MODOS = ("confirmacao", "fila_horario", "fila_barbeiro")
ESTADO_DO_MODO = {"confirmacao": "confirmado", "fila_horario": "fila_horario", "fila_barbeiro": "fila_barbeiro"}
OPCAO_QUALQUER = {"id_barbeiro": demo.QUALQUER, "nome": demo.NOME_QUALQUER}


# ---------- auxiliares de apresentação ----------

def _por_id(lista, chave, valor):
    try:
        valor = int(valor)
    except (TypeError, ValueError):
        return None
    return next((item for item in lista if item[chave] == valor), None)


def _barbeiro(valor, barbeiros):
    """Barbeiro ativo, a opção "qualquer" ou None se inválido."""
    if valor == demo.QUALQUER:
        return OPCAO_QUALQUER
    return _por_id(barbeiros, "id_barbeiro", valor)


def _data(valor):
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        return None


def data_br(d):
    return d.strftime("%d/%m/%Y")


def servico_txt(s):
    return f"{s['nome']} – {s['duracao_min']} min"


def _selecao(args, data_padrao=None):
    """Escolha da URL validada no servidor: só serviço, barbeiro e horário que existem na data."""
    data = _data(args.get("data")) or data_padrao
    hora = args.get("hora")
    horarios = consulta.horarios_do_dia(data) if data else []
    return {
        "servico": _por_id(catalogo.servicos_ativos(), "id_servico", args.get("servico")),
        "data": data,
        "hora": hora if hora in horarios else None,
        "barbeiro": _barbeiro(args.get("barbeiro"), catalogo.barbeiros_ativos()),
    }, horarios


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


def _ids_livres(sel):
    """Ids dos barbeiros em que o serviço escolhido cabe no horário escolhido."""
    return consulta.barbeiros_livres_no_horario(
        sel["servico"]["id_servico"], sel["data"], time.fromisoformat(sel["hora"])
    )


def _modo_coerente(sel, modo):
    return regras.modo_coerente(modo, sel["barbeiro"]["id_barbeiro"], _ids_livres(sel), demo.QUALQUER)


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
    sel, horarios = _selecao(args, data_padrao=demo.DATA_PADRAO)
    if not sel["barbeiro"]:
        sel["barbeiro"] = OPCAO_QUALQUER
    return render_template(
        "tela1_escolha.html",
        servicos=catalogo.servicos_ativos(),
        horarios=horarios,
        barbeiros=[OPCAO_QUALQUER, *catalogo.barbeiros_ativos()],
        sel=sel,
        completa=_completa(sel),
        foco_data=request.args.get("foco") == "data",
    )


# ---------- Tela 2: disponibilidade ----------

@bp.get("/disponibilidade")
def disponibilidade():
    sel, _ = _selecao(request.args)
    if not _completa(sel):
        return redirect(url_for("web.escolha", **_params(sel)))
    ids_livres = _ids_livres(sel)
    barbeiro = sel["barbeiro"]
    caso = regras.caso_disponibilidade(barbeiro["id_barbeiro"], ids_livres, demo.QUALQUER)
    livres = [b for b in catalogo.barbeiros_ativos() if b["id_barbeiro"] in ids_livres]
    outros = [b for b in livres if b["id_barbeiro"] != barbeiro["id_barbeiro"]]
    return render_template(
        "tela2_disponibilidade.html",
        sel=sel,
        caso=caso,
        outros=outros,
        params=_params(sel),
    )


# ---------- Tela 3: dados do cliente ----------

def _sel_tela3():
    sel, _ = _selecao(request.args)
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
        if modo == "confirmacao":
            r = agendamento.confirmar_agendamento(
                sel["servico"]["id_servico"], sel["barbeiro"]["id_barbeiro"], sel["data"],
                time.fromisoformat(sel["hora"]), form.nome.data, form.telefone.data,
            )
            if not r.confirmado:
                # Horário tomado entre a Tela 2 e o envio: volta à Tela 2, que mostra as alternativas
                return redirect(url_for("web.disponibilidade", **_params(sel)))
        # Filas ainda não gravam (etapa 4). Nome e telefone não vão para a URL.
        return redirect(url_for("web.resultado", estado=ESTADO_DO_MODO[modo], **_params(sel)))
    return _render_tela3(sel, modo, form)


# ---------- Tela 4: resultado ----------

@bp.get("/resultado/<estado>")
def resultado(estado):
    if estado not in ESTADO_DO_MODO.values():
        abort(404)
    sel, _ = _selecao(request.args)
    if not _completa(sel):
        return redirect(url_for("web.escolha"))
    if not regras.estado_coerente(estado, sel["barbeiro"]["id_barbeiro"], demo.QUALQUER):
        return redirect(url_for("web.escolha"))
    return render_template("tela4_resultado.html", estado=estado, sel=sel)
