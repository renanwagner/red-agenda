"""RF06: agenda do dia e da semana do barbeiro. Sem Flask nem SQL.

Regras (docs/02 e decisão de 08/11/2026):
- só agendamentos confirmados, do barbeiro pedido, em ordem de horário;
- semana = segunda a domingo da data escolhida; na semana, só os dias com agendamento.
A escolha do barbeiro (comum: ele mesmo; administrador: qualquer) é checada na rota.
"""
from datetime import datetime, time, timedelta

from app.repositories import agenda as repo


def semana_de(data):
    """(segunda, domingo) da semana que contém `data`."""
    segunda = data - timedelta(days=data.weekday())
    return segunda, segunda + timedelta(days=6)


def telefone_txt(digitos):
    """'51900000001' → '51 90000-0001'; '5132000000' → '51 3200-0000'; outro formato fica como está."""
    if len(digitos) not in (10, 11):
        return digitos
    return f"{digitos[:2]} {digitos[2:-4]}-{digitos[-4:]}"


def _itens(id_barbeiro, primeiro_dia, ultimo_dia):
    inicio = datetime.combine(primeiro_dia, time())
    fim = datetime.combine(ultimo_dia + timedelta(days=1), time())
    return [{"inicio": a["inicio"], "fim": a["fim"], "cliente": a["cliente"],
             "telefone": telefone_txt(a["telefone"]),
             "servico": {"nome": a["servico_nome"], "duracao_min": a["servico_duracao"]}}
            for a in repo.confirmados_do_periodo(id_barbeiro, inicio, fim)]


def do_dia(id_barbeiro, data):
    return _itens(id_barbeiro, data, data)


def da_semana(id_barbeiro, data):
    """[{"data", "itens"}] só dos dias da semana que têm agendamento confirmado."""
    dias = {}
    for item in _itens(id_barbeiro, *semana_de(data)):
        dias.setdefault(item["inicio"].date(), []).append(item)
    return [{"data": d, "itens": itens} for d, itens in dias.items()]
