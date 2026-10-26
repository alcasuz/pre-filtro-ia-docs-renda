"""R5 + R6 (renda): média das verbas fixas brutas dos meses usados >= multiplicador x parcela.

Renda do mês = soma das linhas classificadas como "conta" nos holerites mensal e de
férias daquela competência (o holerite de 13º não entra). Renda válida = média dos
meses usados (os mesmos da R3). A comparação é exata, em centavos: soma >=
multiplicador x parcela x número de meses, sem arredondar a média antes.
"""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from ..models import PASS, REJECT, ResultadoRegra


def renda_por_mes(docs_aceitos):
    por_mes = defaultdict(lambda: Decimal("0"))
    for doc in docs_aceitos:
        if doc.document_type == "payslip_13th" or not doc.pay_period:
            continue
        por_mes[doc.pay_period] += sum((l.amount for l in doc.earnings_lines if l.counts_as_income),
                                       Decimal("0"))
    return dict(por_mes)


def avaliar(docs_aceitos, meses_usados, cliente, config):
    por_mes = renda_por_mes(docs_aceitos)
    meses = [m for m in meses_usados if m in por_mes]
    if not meses:
        return ResultadoRegra(rule="income", status=REJECT, reason="insufficient_income",
                              details={"valid_income": None, "monthly_income": {}, "months": []})
    soma = sum((por_mes[m] for m in meses), Decimal("0"))
    minimo_mensal = config.income_multiplier * cliente.installment_amount
    renda_valida = (soma / len(meses)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    passa = soma >= minimo_mensal * len(meses)
    return ResultadoRegra(
        rule="income", status=PASS if passa else REJECT, reason=None if passa else "insufficient_income",
        details={"valid_income": renda_valida, "minimum_income": minimo_mensal,
                 "monthly_income": {m: por_mes[m] for m in meses}, "months": meses,
                 "ratio": (soma / len(meses) / cliente.installment_amount).quantize(Decimal("0.0001"))},
    )
