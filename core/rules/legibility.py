"""R7 (legibilidade): documento ilegível reprova, com orientação para reenviar.

Um documento é ilegível se:
1. o OCR não reconhece nenhuma palavra E o LLM não extrai nenhum campo (todos
   null e nenhuma linha de provento) E o LLM não identifica o documento
   (document_type = unidentified): motivo illegible. Sem OCR (None) conta como
   zero palavras. Um documento identificado de outro tipo, mesmo sem campos (ex.:
   uma conta de luz girada), segue para a regra de tipo (R1). A confiança média
   do OCR não é usada: em fotos reais ela barrava documentos que o LLM lia bem
   (ex.: imagem de cabeça para baixo);
2. o CPF lido tem dígitos verificadores inválidos (R2): sinal de leitura errada,
   não de outro titular; motivo illegible.

Fallback, no nível do pedido: falhas_anteriores é quantas reprovações por
ilegibilidade (qualquer critério acima) ou documento incompleto o pedido já teve,
informado por quem chama o motor. Se esta é a tentativa max_legibility_attempts
ou além, a falha vai para revisão humana (too_many_attempts) em vez de reprovar de
novo, para quem não consegue gerar uma imagem legível não ficar preso.
"""

from ..models import PASS, REJECT, REVIEW, ResultadoRegra
from .identification import cpf_valido, normalizar_cpf

CAMPOS_LIDOS = ("pay_period", "name_on_doc", "cpf_on_doc", "total_earnings", "total_deductions", "net_pay")


def status_da_falha(motivo, config, falhas_anteriores):
    """Reprova com o motivo ou, a partir da tentativa max_legibility_attempts, vai para revisão.

    O contador é compartilhado com a regra de documento incompleto.
    """
    if falhas_anteriores + 1 >= config.max_legibility_attempts:
        return REVIEW, "too_many_attempts"
    return REJECT, motivo


def extraiu_algo(doc):
    return bool(doc.earnings_lines) or any(getattr(doc, c) not in (None, "") for c in CAMPOS_LIDOS)


def avaliar(doc, config, falhas_anteriores=0):
    detalhes = {"ocr_words": doc.ocr_words, "prior_legibility_failures": falhas_anteriores,
                "max_attempts": config.max_legibility_attempts}
    cpf = normalizar_cpf(doc.cpf_on_doc)
    if not doc.ocr_words and not extraiu_algo(doc) and doc.document_type == "unidentified":
        motivo, detalhes["criterion"] = "illegible", "ocr_and_llm_empty"
    elif cpf and not cpf_valido(cpf):
        motivo, detalhes["criterion"] = "illegible", "cpf_check_digits"
    else:
        return ResultadoRegra(rule="legibility", file=doc.file, status=PASS, details=detalhes)
    status, motivo = status_da_falha(motivo, config, falhas_anteriores)
    return ResultadoRegra(rule="legibility", file=doc.file, status=status, reason=motivo, details=detalhes)
