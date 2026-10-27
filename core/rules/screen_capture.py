"""R1 (captura): foto de tela ou print de tela reprova, com orientação para enviar o original.

O tipo de captura vem do LLM (capture_type). Extrações sem esse campo (prompts
anteriores ao v3) não são avaliadas e passam, com o motivo registrado nos detalhes.
"""

from ..models import CAPTURAS_DE_TELA, PASS, REJECT, ResultadoRegra


def avaliar(doc):
    if doc.capture_type is None:
        return ResultadoRegra(rule="screen_capture", file=doc.file, status=PASS,
                              details={"evaluated": False, "note": "capture_type ausente"})
    de_tela = doc.capture_type in CAPTURAS_DE_TELA
    return ResultadoRegra(rule="screen_capture", file=doc.file, status=REJECT if de_tela else PASS,
                          reason="screen_capture" if de_tela else None,
                          details={"evaluated": True, "capture_type": doc.capture_type})
