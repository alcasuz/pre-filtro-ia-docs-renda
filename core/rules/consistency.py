"""R4 (consistência): |vencimentos - descontos - líquido| <= tolerância; fora dela, revisão.

Se algum dos três totais não foi lido (null), a regra não é avaliada e passa, com
o motivo registrado nos detalhes.
"""

from ..models import PASS, REVIEW, ResultadoRegra


def avaliar(doc, config):
    totais = (doc.total_earnings, doc.total_deductions, doc.net_pay)
    if None in totais:
        return ResultadoRegra(rule="consistency", file=doc.file, status=PASS,
                              details={"evaluated": False, "note": "total ausente"})
    diferenca = abs(doc.total_earnings - doc.total_deductions - doc.net_pay)
    dentro = diferenca <= config.consistency_tolerance
    return ResultadoRegra(rule="consistency", file=doc.file,
                          status=PASS if dentro else REVIEW,
                          reason=None if dentro else "suspected_fraud",
                          details={"evaluated": True, "difference": diferenca,
                                   "tolerance": config.consistency_tolerance})
