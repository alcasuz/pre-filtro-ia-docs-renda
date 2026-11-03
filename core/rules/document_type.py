"""R1 (tipo): só holerite é aceito na v1.

Avaliada por cliente: reprova com type_not_accepted só quando nenhum documento
legível é holerite. Um documento de outro tipo enviado junto com holerites (ex.:
um extrato a mais) é ignorado, e os holerites seguem para as demais regras.

A reprovação traz a mensagem ao cliente (details["message"]): uma frase para o
problema, citando o tipo enviado quando ele tem nome próprio, e uma para a correção.
Tipos sem nome próprio (other_document, unidentified e o other dos prompts até o
v3) viram "Este tipo de documento não é aceito."
"""

from ..models import PASS, REJECT, TIPOS_ACEITOS, ResultadoRegra

# (nome, gênero) de cada tipo com nome próprio, para a concordância de "aceito/aceita".
NOMES_DOS_TIPOS = {
    "bank_statement": ("extrato bancário", "m"),
    "tax_return": ("declaração de imposto de renda", "f"),
    "inss_benefit": ("comprovante do INSS", "m"),
}
CORRECAO = "Envie os holerites dos últimos 3 meses."


def mensagem(tipos):
    tipos = list(dict.fromkeys(tipos))
    nomeados = [NOMES_DOS_TIPOS[t] for t in tipos if t in NOMES_DOS_TIPOS]
    if len(nomeados) < len(tipos):
        problema = "Este tipo de documento não é aceito." if len(tipos) == 1 else \
            "Esses tipos de documento não são aceitos."
    elif len(nomeados) == 1:
        nome, genero = nomeados[0]
        problema = f"{nome[0].upper()}{nome[1:]} não é {'aceita' if genero == 'f' else 'aceito'}."
    else:
        nomes = " e ".join(nome for nome, _ in nomeados)
        problema = f"{nomes[0].upper()}{nomes[1:]} não são aceitos."
    return f"{problema} {CORRECAO}"


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
