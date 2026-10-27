"""R1 (tipo): só holerite é aceito na v1.

Avaliada por cliente: reprova com type_not_accepted só quando nenhum documento
legível é holerite. Um documento de outro tipo enviado junto com holerites (ex.:
um extrato a mais) é ignorado, e os holerites seguem para as demais regras.

A reprovação traz a mensagem ao cliente citando o tipo enviado (details["message"]).
Tipos sem nome próprio (other_document, unidentified e o other dos prompts até o
v3) aparecem como "um documento que não é holerite".
"""

from ..models import PASS, REJECT, TIPOS_ACEITOS, ResultadoRegra

NOMES_DOS_TIPOS = {
    "bank_statement": "um extrato bancário",
    "tax_return": "uma declaração de imposto de renda",
    "inss_benefit": "um comprovante do INSS",
}
NOME_PADRAO = "um documento que não é holerite"
MENSAGEM = "Você enviou {tipo}. No momento aceitamos apenas holerite. Envie os holerites dos últimos 3 meses."


def mensagem(tipos):
    nomes = list(dict.fromkeys(NOMES_DOS_TIPOS.get(t, NOME_PADRAO) for t in tipos))
    return MENSAGEM.format(tipo=" e ".join(nomes))


def aceito(doc):
    return doc.document_type in TIPOS_ACEITOS


def avaliar(docs_legiveis):
    aceitos = [d.file for d in docs_legiveis if aceito(d)]
    ignorados = [d.file for d in docs_legiveis if not aceito(d)]
    if docs_legiveis and not aceitos:
        return ResultadoRegra(rule="document_type", status=REJECT, reason="type_not_accepted",
                              details={"accepted": aceitos, "ignored": ignorados,
                                       "message": mensagem(d.document_type for d in docs_legiveis)})
    return ResultadoRegra(rule="document_type", status=PASS,
                          details={"accepted": aceitos, "ignored": ignorados})
