"""R7 (legibilidade): documento ilegível reprova, com orientação para reenviar.

O sinal definitivo virá do OCR (Documento.legible). Enquanto ele não existe, vale
o critério provisório: tipo other com todos os campos nulos e nenhuma linha é
tratado como ilegível, porque é o que o LLM devolve para uma imagem desfocada.
"""

from ..models import PASS, REJECT, ResultadoRegra

CAMPOS = ("pay_period", "name_on_doc", "cpf_on_doc", "total_earnings", "total_deductions", "net_pay")


def avaliar(doc):
    if doc.legible is not None:
        legivel, criterio = doc.legible, "ocr"
    else:
        vazio = all(getattr(doc, c) is None for c in CAMPOS) and not doc.earnings_lines
        legivel, criterio = not (doc.document_type == "other" and vazio), "provisorio_other_nulo"
    return ResultadoRegra(
        rule="legibility", file=doc.file,
        status=PASS if legivel else REJECT,
        reason=None if legivel else "illegible",
        details={"legible": legivel, "criterion": criterio},
    )
