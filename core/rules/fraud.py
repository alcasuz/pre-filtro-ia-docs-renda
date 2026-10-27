"""R7 (sinais de edição ou prompt injection): a sinalização de fraude do LLM leva à revisão.

Print e foto de tela não são fraude: são avaliados pela regra screen_capture (R1).

Só um holerite aceito leva à revisão. Um documento de outro tipo, que a regra de
tipo ignora ou reprova, passa, mas o sinal fica registrado nos detalhes
(flagged), para entrar em fraud_flag e fraud_reasons sem mudar a decisão.
"""

from ..models import PASS, REVIEW, ResultadoRegra


def avaliar(doc, aceito=True):
    if not doc.fraud_suspected:
        return ResultadoRegra(rule="fraud", file=doc.file, status=PASS)
    detalhes = {"fraud_reason": doc.fraud_reason, "flagged": True}
    if not aceito:
        return ResultadoRegra(rule="fraud", file=doc.file, status=PASS, details={**detalhes, "ignored_document": True})
    return ResultadoRegra(rule="fraud", file=doc.file, status=REVIEW, reason="suspected_fraud", details=detalhes)
