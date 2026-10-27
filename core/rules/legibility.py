"""R7 (legibilidade): documento ilegível reprova, com orientação para reenviar.

O sinal é a confiança média das palavras no OCR (core/ocr.py): abaixo de
legibility_min_confidence, o documento é ilegível; no limite exato, é legível.
Sem confiança de OCR (o OCR não conseguiu ler) também é falha de legibilidade.

Fallback, no nível do pedido: falhas_anteriores é quantas reprovações por
ilegibilidade o pedido já teve (informado por quem chama o motor). Se esta é a
tentativa max_legibility_attempts ou além, a falha vai para revisão humana
(too_many_attempts) em vez de reprovar de novo, para quem não consegue gerar uma
imagem legível não ficar preso.
"""

from ..models import PASS, REJECT, REVIEW, ResultadoRegra


def avaliar(doc, config, falhas_anteriores=0):
    tentativa = falhas_anteriores + 1
    detalhes = {"ocr_confidence": doc.ocr_confidence, "min_confidence": config.legibility_min_confidence,
                "prior_legibility_failures": falhas_anteriores, "max_attempts": config.max_legibility_attempts}
    if doc.ocr_confidence is None:
        legivel, detalhes["criterion"] = False, "ocr_unavailable"
    else:
        legivel, detalhes["criterion"] = doc.ocr_confidence >= config.legibility_min_confidence, "ocr_confidence"

    if legivel:
        status, motivo = PASS, None
    elif tentativa >= config.max_legibility_attempts:
        status, motivo = REVIEW, "too_many_attempts"
    else:
        status, motivo = REJECT, "illegible"
    return ResultadoRegra(rule="legibility", file=doc.file, status=status, reason=motivo, details=detalhes)
