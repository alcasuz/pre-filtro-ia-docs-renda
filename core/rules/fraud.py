"""R7 (sinais de edição ou prompt injection): a sinalização de fraude do LLM leva à revisão.

Print e foto de tela não são fraude: são avaliados pela regra screen_capture (R1).
"""

from ..models import PASS, REVIEW, ResultadoRegra


def avaliar(doc):
    if doc.fraud_suspected:
        return ResultadoRegra(rule="fraud", file=doc.file, status=REVIEW, reason="suspected_fraud",
                              details={"fraud_reason": doc.fraud_reason})
    return ResultadoRegra(rule="fraud", file=doc.file, status=PASS)
