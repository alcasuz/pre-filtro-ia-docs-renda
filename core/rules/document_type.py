"""R1 (tipo): só holerite é aceito na v1.

Avaliada por cliente: reprova com type_not_accepted só quando nenhum documento
legível é holerite. Um documento de outro tipo enviado junto com holerites (ex.:
um extrato a mais) é ignorado, e os holerites seguem para as demais regras.
"""

from ..models import PASS, REJECT, TIPOS_ACEITOS, ResultadoRegra


def aceito(doc):
    return doc.document_type in TIPOS_ACEITOS


def avaliar(docs_legiveis):
    aceitos = [d.file for d in docs_legiveis if aceito(d)]
    ignorados = [d.file for d in docs_legiveis if not aceito(d)]
    if docs_legiveis and not aceitos:
        return ResultadoRegra(rule="document_type", status=REJECT, reason="type_not_accepted",
                              details={"accepted": aceitos, "ignored": ignorados})
    return ResultadoRegra(rule="document_type", status=PASS,
                          details={"accepted": aceitos, "ignored": ignorados})
