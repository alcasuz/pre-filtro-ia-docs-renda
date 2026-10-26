"""R3 (período): 3 holerites de meses consecutivos dentro da janela.

A janela são os window_months meses anteriores ao mês da analysis_date, sem
incluir o próprio mês. Se vierem mais meses, só os required_months mais recentes
contam; a janela e a sequência são conferidas sobre eles. Holerites de 13º não
formam mês (R3). Menos meses que o exigido reprova como outside_window (a R3 dá a
mesma mensagem para os dois casos).
"""

import re

from ..models import PASS, REJECT, ResultadoRegra


def mes_anterior(ano, mes, n=1):
    total = ano * 12 + (mes - 1) - n
    return total // 12, total % 12 + 1


def janela(analysis_date, window_months):
    return [f"{a}-{m:02d}" for a, m in
            (mes_anterior(analysis_date.year, analysis_date.month, n) for n in range(1, window_months + 1))]


def meses_validos(docs_aceitos):
    """Competências AAAA-MM dos holerites que formam mês (exclui o de 13º)."""
    return sorted({d.pay_period for d in docs_aceitos
                   if d.document_type != "payslip_13th"
                   and d.pay_period and re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", d.pay_period)})


def selecionar_meses(docs_aceitos, required_months):
    return meses_validos(docs_aceitos)[-required_months:]


def consecutivos(meses):
    indices = [int(m[:4]) * 12 + int(m[5:7]) for m in meses]
    return all(b - a == 1 for a, b in zip(indices, indices[1:]))


def avaliar(docs_aceitos, cliente, config):
    meses = selecionar_meses(docs_aceitos, config.required_months)
    aceitos = janela(cliente.analysis_date, config.window_months)
    detalhes = {"months_used": meses, "window": sorted(aceitos),
                "months_provided": meses_validos(docs_aceitos)}
    if len(meses) < config.required_months or not set(meses) <= set(aceitos):
        return ResultadoRegra(rule="time_window", status=REJECT, reason="outside_window", details=detalhes)
    if not consecutivos(meses):
        return ResultadoRegra(rule="time_window", status=REJECT, reason="non_consecutive_months",
                              details=detalhes)
    return ResultadoRegra(rule="time_window", status=PASS, details=detalhes)
