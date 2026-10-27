"""Documento incompleto: holerite legível sem competência, sem algum dos três totais ou sem
nenhuma linha de provento reprova, com orientação para enviar a página inteira.

Nome e CPF ausentes não entram aqui: são da regra de titular (id_missing). Usa o
mesmo contador de tentativas da legibilidade (falhas_anteriores conta reprovações
por ilegível ou incompleto): a partir da tentativa max_legibility_attempts, a falha
vai para revisão humana (too_many_attempts).
"""

from ..models import PASS, ResultadoRegra
from .legibility import status_da_falha

CAMPOS_OBRIGATORIOS = ("pay_period", "total_earnings", "total_deductions", "net_pay")


def avaliar(doc, config, falhas_anteriores=0):
    faltando = [c for c in CAMPOS_OBRIGATORIOS if getattr(doc, c) in (None, "")]
    if not doc.earnings_lines:
        faltando.append("earnings_lines")
    detalhes = {"missing": faltando, "prior_legibility_failures": falhas_anteriores}
    if not faltando:
        return ResultadoRegra(rule="completeness", file=doc.file, status=PASS, details=detalhes)
    status, motivo = status_da_falha("incomplete_document", config, falhas_anteriores)
    return ResultadoRegra(rule="completeness", file=doc.file, status=status, reason=motivo, details=detalhes)
