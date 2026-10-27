"""Gera documentos fictícios que não são holerite, para testar a regra de tipo (R1).

Dois exemplos de cada tipo, com layouts diferentes entre si:
- comprovante de benefício do INSS (inss_benefit);
- extrato bancário de bancos inventados (bank_statement);
- resumo da declaração de imposto de renda (tax_return);
- fatura de cartão de crédito, boleto, documento de identidade, informe de
  rendimentos anual e RPA (other_document).

E dois clientes novos (test-scenarios.md):
- A17: 3 holerites válidos (renda 3,3x a parcela) + um documento de identidade a mais;
- N17: só um comprovante do INSS.
O documento de identidade do A17 e o comprovante do INSS do N17 são um dos dois
exemplos do tipo; os outros 14 documentos não pertencem a nenhum cliente
(applicant_id vazio) e só entram no eval por documento.

Cuidados: nomes, CPFs e CNPJs inventados (dígitos verificadores válidos, sem
repetir os da base); nenhum brasão, logotipo oficial ou nome de banco ou empresa
real (o código de banco do boleto é 999, que não existe); marca d'água
"DOCUMENTO FICTÍCIO" em todos os documentos que não são holerite; o documento de
identidade é um modelo genérico, sem nome de estado nem layout oficial. Os
holerites do A17 usam os layouts de generate_images.py, sem marca d'água, como os
outros holerites da base.

Acrescenta as linhas em data/applicants.csv, documents.csv, line_items.csv e
ground_truth.csv (A17 e N17 com expected_valid_income, expected_decision e
expected_reason vazios, para preenchimento manual; linhas que já existem ficam
como estão) e as imagens em data/images/.
Rodar de novo substitui só o que este script gerou; as demais linhas ficam
intactas. Semente fixa: mesmo resultado a cada execução na mesma máquina.

Uso: .venv/bin/python generation/generate_non_payslips.py
"""

import csv
import random
from fractions import Fraction

from PIL import Image, ImageDraw

import generate_data as dados
import generate_images as imagens
from generate_data import (COLUNAS_CADASTROS, COLUNAS_DOCUMENTOS, COLUNAS_RUBRICAS, DATA_ANALISE, RUBRICAS,
                           SEMENTE, mascara_cnpj, mascara_cpf, reais)
from generate_images import BRANCO, CINZA, LARGURA, PASTA_IMAGENS, PRETO, brl, clarear, fonte, recortar, salvar

PASTA_DADOS = dados.PASTA_DADOS
ARQUIVO_AMOSTRA = "_sample_non_payslips.png"
CLIENTES_NOVOS = ("A17", "N17")
PREFIXO_SEM_CLIENTE = "X_"
MULTIPLO_A17 = Fraction(33, 10)
EMPRESA_A17 = "Clínica Bem Cuidar Ltda"

# Instituições inventadas (nenhuma existe).
BANCOS = ["Banco Ipê Amarelo S.A.", "Cooperativa de Crédito Vale do Sabiá"]
CARTOES = ["Cartão Bem-te-vi", "Cartão Jacarandá Mais"]
EMPRESAS_FICTICIAS = ["Gráfica Beira-Rio Ltda", "Escola de Idiomas Ponte Nova Ltda", "Condomínio Jardim das Acácias",
                      "Oficina Mecânica Roda Viva Ltda", "Estúdio de Design Maré Alta Ltda",
                      "Distribuidora Serra Azul Ltda", "Consultoria Horizonte Claro Ltda"]
ORGAO_IDENTIDADE = "Instituto de Identificação Fictício"
ESPECIES_INSS = ["41 - Aposentadoria por idade", "21 - Pensão por morte previdenciária"]


# ---------------------------------------------------------------------------
# Desenho comum
# ---------------------------------------------------------------------------

def marca_dagua(img):
    """'DOCUMENTO FICTÍCIO' em diagonal, cinza translúcido, repetido ao longo da página."""
    camada = Image.new("RGBA", img.size, (0, 0, 0, 0))
    texto = "DOCUMENTO FICTÍCIO"
    fnt = fonte("arial", 64, True)
    caixa = ImageDraw.Draw(camada).textbbox((0, 0), texto, font=fnt)
    w, h = caixa[2] - caixa[0] + 40, caixa[3] - caixa[1] + 40
    carimbo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(carimbo).text((20, 10), texto, font=fnt, fill=(200, 40, 40, 70))
    carimbo = carimbo.rotate(25, expand=True)
    for y in range(80, img.height, 520):
        x = 120 if (y // 520) % 2 == 0 else 420
        camada.alpha_composite(carimbo, (min(x, max(0, img.width - carimbo.width)), y))
    return Image.alpha_composite(img.convert("RGBA"), camada).convert("RGB")


def pagina(altura=2000):
    img = Image.new("RGB", (LARGURA, altura), BRANCO)
    return img, ImageDraw.Draw(img)


def rotulo_valor(d, x, y, rotulo, valor, familia="arial", tam=17, cor_rotulo=CINZA):
    d.text((x, y), rotulo, font=fonte(familia, tam - 4), fill=cor_rotulo)
    d.text((x, y + tam + 2), valor, font=fonte(familia, tam, True), fill=PRETO)


def linha_pontilhada(d, x0, x1, y, rotulo, valor, familia="courier", tam=17):
    fnt = fonte(familia, tam)
    largura_char = d.textlength(".", font=fnt)
    livre = x1 - x0 - d.textlength(rotulo, font=fnt) - d.textlength(valor, font=fnt) - 12
    pontos = "." * max(2, int(livre / largura_char))
    d.text((x0, y), f"{rotulo} {pontos} {valor}", font=fnt, fill=PRETO)


def tabela(d, x0, x1, y, colunas, linhas, familia="arial", tam=15, cor=(60, 60, 60), zebra=None):
    """colunas: [(título, posição x relativa 0-1, âncora)]; linhas: listas de textos."""
    d.rectangle([x0, y, x1, y + 32], fill=cor)
    for titulo, pos, anc in colunas:
        d.text((x0 + 10 + pos * (x1 - x0 - 20), y + 8), titulo, font=fonte(familia, tam, True), fill=BRANCO,
               anchor=anc)
    y += 38
    for i, linha in enumerate(linhas):
        if zebra and i % 2:
            d.rectangle([x0, y - 4, x1, y + 24], fill=zebra)
        for (_, pos, anc), texto in zip(colunas, linha):
            d.text((x0 + 10 + pos * (x1 - x0 - 20), y), texto, font=fonte(familia, tam), fill=PRETO, anchor=anc)
        y += 30
    return y


def codigo_barras(d, x0, x1, y, altura, rng):
    x = x0
    while x < x1 - 4:
        w = rng.choice((2, 2, 3, 4))
        if rng.random() < 0.6:
            d.rectangle([x, y, x + w - 1, y + altura], fill=PRETO)
        x += w


def digitos(rng, n):
    return "".join(str(rng.randrange(10)) for _ in range(n))


def data_br(dia, mes, ano):
    return f"{dia:02d}/{mes:02d}/{ano}"


def mes_ano(periodo):
    return f"{periodo[5:7]}/{periodo[:4]}"


# ---------------------------------------------------------------------------
# Tipos de documento (variante 0 e 1 com layouts diferentes)
# ---------------------------------------------------------------------------

def inss_benefit(p, rng):
    img, d = pagina(1700)
    m, x0, x1 = 50, 50, LARGURA - 50
    bruto = rng.randint(150000, 420000)
    consignado = arredondar_pct(bruto, rng.randint(10, 30))
    irrf = rng.choice((0, 0, rng.randint(2000, 9000)))
    liquido = bruto - consignado - irrf
    nb = f"{digitos(rng, 3)}.{digitos(rng, 3)}.{digitos(rng, 3)}-{digitos(rng, 1)}"
    especie = ESPECIES_INSS[p["variante"]]
    itens = [("101", "VALOR TOTAL DO BENEFÍCIO", bruto, ""), ("216", "CONSIGNAÇÃO EMPRÉSTIMO BANCÁRIO", "", consignado)]
    if irrf:
        itens.append(("201", "IMPOSTO DE RENDA RETIDO NA FONTE", "", irrf))
    if p["variante"] == 0:
        azul = (25, 75, 140)
        d.rectangle([0, 0, LARGURA, 110], fill=azul)
        d.text((x0, 24), "INSS · Extrato de Pagamento de Benefício", font=fonte("verdana", 28, True), fill=BRANCO)
        d.text((x0, 70), "Comprovante mensal emitido pelo portal do segurado", font=fonte("verdana", 16), fill=BRANCO)
        y = 140
        campos = [("Nome do beneficiário", p["nome"]), ("CPF", p["cpf_doc"]), ("Número do benefício (NB)", nb),
                  ("Espécie", especie), ("Competência", mes_ano(p["periodo"])),
                  ("Banco pagador", f"{BANCOS[0]} · Ag. {digitos(rng, 4)}")]
        for i, (r, v) in enumerate(campos):
            rotulo_valor(d, x0 + (i % 2) * 560, y + (i // 2) * 70, r, v, familia="verdana", tam=18)
        y += 230
        y = tabela(d, x0, x1, y, [("Rubrica", 0, "la"), ("Descrição", 0.1, "la"), ("Créditos (R$)", 0.8, "ra"),
                                  ("Débitos (R$)", 1, "ra")],
                   [[c, desc, brl(cr) if cr else "", brl(db) if db else ""] for c, desc, cr, db in itens],
                   familia="verdana", cor=azul, zebra=clarear(azul, 0.9))
        d.line([x0, y + 6, x1, y + 6], fill=azul, width=2)
        d.text((x1, y + 20), f"Valor líquido: R$ {brl(liquido)}", font=fonte("verdana", 22, True), fill=PRETO,
               anchor="ra")
        y += 80
    else:
        y = m
        d.text((x0, y), "INSTITUTO NACIONAL DO SEGURO SOCIAL - INSS", font=fonte("courier", 22, True), fill=PRETO)
        d.text((x0, y + 34), "HISTÓRICO DE CRÉDITOS - DEMONSTRATIVO DE PAGAMENTO", font=fonte("courier", 18),
               fill=PRETO)
        y += 80
        d.text((x0, y), "=" * 78, font=fonte("courier", 16), fill=PRETO)
        y += 30
        for r, v in [("BENEFICIÁRIO", p["nome"].upper()), ("CPF", p["cpf_doc"]), ("NB", nb), ("ESPÉCIE", especie.upper()),
                     ("COMPETÊNCIA", mes_ano(p["periodo"])), ("PERÍODO DE VALIDADE", "01/09/2026 A 30/09/2026"),
                     ("ÓRGÃO PAGADOR", f"{digitos(rng, 6)} - {BANCOS[1].upper()}")]:
            d.text((x0, y), f"{r:<22}: {v}", font=fonte("courier", 17), fill=PRETO)
            y += 30
        d.text((x0, y), "-" * 78, font=fonte("courier", 16), fill=PRETO)
        y += 30
        for c, desc, cr, db in itens:
            valor = brl(cr) if cr else f"-{brl(db)}"
            d.text((x0, y), f"{c}  {desc:<44}{valor:>16}", font=fonte("courier", 17), fill=PRETO)
            y += 30
        d.text((x0, y), "-" * 78, font=fonte("courier", 16), fill=PRETO)
        y += 30
        d.text((x0, y), f"{'':5} {'VALOR LÍQUIDO':<44}{brl(liquido):>16}", font=fonte("courier", 17, True), fill=PRETO)
        y += 60
    d.text((x0, y), "Este documento não substitui o extrato oficial. Dúvidas: central de atendimento do segurado.",
           font=fonte("arial", 14), fill=CINZA)
    return recortar(img, y + 40 + m)


def bank_statement(p, rng):
    img, d = pagina(2000)
    m, x0, x1 = 44, 44, LARGURA - 44
    banco = BANCOS[p["variante"]]
    saldo = rng.randint(400000, 900000)
    movimentos = []
    for dia in sorted(rng.sample(range(1, 29), 9)):
        tipo = rng.choice(["PIX RECEBIDO", "PIX ENVIADO", "PAGAMENTO DE BOLETO", "COMPRA CARTÃO DÉBITO", "TED RECEBIDA",
                           "TARIFA PACOTE SERVIÇOS"])
        valor = rng.randint(1500, 90000)
        if tipo in ("PIX RECEBIDO", "TED RECEBIDA"):
            saldo += valor
            movimentos.append((dia, tipo, valor, saldo))
        else:
            saldo -= valor
            movimentos.append((dia, tipo, -valor, saldo))
    mes = int(p["periodo"][5:7])
    agencia, conta = digitos(rng, 4), f"{digitos(rng, 5)}-{digitos(rng, 1)}"
    if p["variante"] == 0:
        verde = (20, 110, 80)
        d.rectangle([0, 0, LARGURA, 100], fill=verde)
        d.text((x0, 30), banco, font=fonte("tahoma", 30, True), fill=BRANCO)
        d.text((x1, 40), "Extrato de conta corrente", font=fonte("tahoma", 18), fill=BRANCO, anchor="ra")
        y = 130
        for i, (r, v) in enumerate([("Cliente", p["nome"]), ("CPF", p["cpf_doc"]), ("Agência / Conta", f"{agencia} / {conta}"),
                                    ("Período", f"01/{mes:02d}/2026 a 30/{mes:02d}/2026")]):
            rotulo_valor(d, x0 + (i % 2) * 560, y + (i // 2) * 64, r, v, familia="tahoma")
        y += 150
        y = tabela(d, x0, x1, y, [("Data", 0, "la"), ("Lançamento", 0.12, "la"), ("Valor (R$)", 0.78, "ra"),
                                  ("Saldo (R$)", 1, "ra")],
                   [[data_br(dia, mes, 2026), t, brl(v), brl(s)] for dia, t, v, s in movimentos],
                   familia="tahoma", cor=verde, zebra=clarear(verde, 0.9))
    else:
        roxo = (90, 50, 120)
        d.text((x0, m), banco.upper(), font=fonte("verdana", 24, True), fill=roxo)
        d.text((x0, m + 40), f"Extrato mensal · {mes_ano(p['periodo'])}", font=fonte("verdana", 18), fill=PRETO)
        d.text((x1, m + 6), f"Ag. {agencia}  C/C {conta}", font=fonte("verdana", 16), fill=PRETO, anchor="ra")
        d.text((x1, m + 40), f"{p['nome'].upper()} · CPF {p['cpf_doc']}", font=fonte("verdana", 16), fill=PRETO,
               anchor="ra")
        y = m + 100
        d.line([x0, y, x1, y], fill=roxo, width=3)
        y += 20
        for dia, t, v, s in movimentos:
            d.rounded_rectangle([x0, y, x1, y + 64], radius=12, outline=clarear(roxo, 0.6), width=2)
            d.text((x0 + 16, y + 10), f"{dia:02d}/{mes:02d}", font=fonte("verdana", 15, True), fill=roxo)
            d.text((x0 + 110, y + 10), t, font=fonte("verdana", 16), fill=PRETO)
            d.text((x0 + 110, y + 36), f"Saldo após o lançamento: R$ {brl(s)}", font=fonte("verdana", 13), fill=CINZA)
            d.text((x1 - 16, y + 20), ("+ " if v > 0 else "- ") + f"R$ {brl(abs(v))}",
                   font=fonte("verdana", 18, True), fill=(20, 120, 60) if v > 0 else (170, 40, 40), anchor="ra")
            y += 76
    d.text((x0, y + 20), f"Saldo final do período: R$ {brl(saldo)}", font=fonte("arial", 20, True), fill=PRETO)
    return recortar(img, y + 70 + m)


def tax_return(p, rng):
    img, d = pagina(1800)
    m, x0, x1 = 50, 50, LARGURA - 50
    tributaveis = rng.randint(4000000, 9000000)
    deducoes = rng.randint(300000, 1500000)
    base = tributaveis - deducoes
    devido = arredondar_pct(base, rng.randint(8, 16))
    retido = devido + rng.choice((-1, 1)) * rng.randint(20000, 150000)
    saldo = retido - devido
    linhas = [("Rendimentos tributáveis", tributaveis), ("Deduções", deducoes), ("Base de cálculo do imposto", base),
              ("Imposto devido", devido), ("Imposto retido na fonte", retido),
              ("Imposto a restituir" if saldo > 0 else "Saldo de imposto a pagar", abs(saldo))]
    recibo = f"{digitos(rng, 2)}.{digitos(rng, 2)}.{digitos(rng, 2)}.{digitos(rng, 2)}.{digitos(rng, 2)}-{digitos(rng, 2)}"
    if p["variante"] == 0:
        cinza = (70, 70, 90)
        d.text((x0, m), "DECLARAÇÃO DE AJUSTE ANUAL", font=fonte("arial", 30, True), fill=PRETO)
        d.text((x0, m + 44), "Imposto sobre a renda - pessoa física · Resumo da declaração", font=fonte("arial", 18),
               fill=CINZA)
        d.text((x1, m + 6), "Exercício 2026", font=fonte("arial", 18, True), fill=PRETO, anchor="ra")
        d.text((x1, m + 34), "Ano-calendário 2025", font=fonte("arial", 18), fill=PRETO, anchor="ra")
        y = m + 100
        d.rectangle([x0, y, x1, y + 110], outline=cinza, width=2)
        rotulo_valor(d, x0 + 16, y + 14, "Nome do declarante", p["nome"].upper())
        rotulo_valor(d, x0 + 640, y + 14, "CPF", p["cpf_doc"])
        rotulo_valor(d, x0 + 16, y + 62, "Tipo de declaração", "Declaração de ajuste anual original · Modelo completo",
                     tam=15)
        y += 140
        for titulo, valor in linhas:
            d.rectangle([x0, y, x1, y + 50], outline=clarear(cinza, 0.5), width=1)
            d.text((x0 + 16, y + 14), titulo, font=fonte("arial", 18), fill=PRETO)
            d.text((x1 - 16, y + 14), f"R$ {brl(valor)}", font=fonte("arial", 18, True), fill=PRETO, anchor="ra")
            y += 56
        y += 20
        d.text((x0, y), f"Número do recibo: {recibo}", font=fonte("arial", 16), fill=PRETO)
        y += 40
    else:
        y = m
        d.text((x0, y), "IMPOSTO DE RENDA PESSOA FÍSICA - EXERCÍCIO 2026 - ANO-CALENDÁRIO 2025",
               font=fonte("courier", 18, True), fill=PRETO)
        d.text((x0, y + 30), "RESUMO DA DECLARAÇÃO - MODELO SIMPLIFICADO", font=fonte("courier", 18), fill=PRETO)
        y += 80
        for r, v in [("NOME", p["nome"].upper()), ("CPF", p["cpf_doc"]), ("NATUREZA DA OCUPAÇÃO", "EMPREGADO DE EMPRESA PRIVADA")]:
            d.text((x0, y), f"{r}: {v}", font=fonte("courier", 17), fill=PRETO)
            y += 30
        y += 20
        for titulo, valor in [("RENDIMENTOS TRIBUTÁVEIS", tributaveis),
                              ("DESCONTO SIMPLIFICADO", min(arredondar_pct(tributaveis, 20), 1683600)),
                              ("RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS", rng.randint(100000, 800000)),
                              ("RENDIMENTOS SUJEITOS À TRIBUTAÇÃO EXCLUSIVA", rng.randint(300000, 900000))] + linhas[3:]:
            linha_pontilhada(d, x0, x1, y, titulo.upper(), brl(valor))
            y += 32
        y += 20
        d.text((x0, y), f"RECIBO DE ENTREGA Nº {recibo}", font=fonte("courier", 17), fill=PRETO)
        y += 40
    return recortar(img, y + 40 + m)


def credit_card_bill(p, rng):
    img, d = pagina(1900)
    m, x0, x1 = 44, 44, LARGURA - 44
    cartao = CARTOES[p["variante"]]
    lojas = ["Padaria Pão de Mel", "Posto Estrela Guia", "Farmácia Bem Viver", "Livraria Sete Mares",
             "Mercado Folha Verde", "Restaurante Sabor da Serra", "Loja Ponto Certo", "Assinatura Streaming Lumi"]
    compras = [(rng.randint(1, 28), rng.choice(lojas), rng.randint(1500, 45000)) for _ in range(8)]
    total = sum(v for *_, v in compras)
    minimo = arredondar_pct(total, 15)
    mes = int(p["periodo"][5:7])
    final = digitos(rng, 4)
    if p["variante"] == 0:
        laranja = (210, 90, 30)
        d.rounded_rectangle([x0, m, x1, m + 150], radius=20, fill=laranja)
        d.text((x0 + 30, m + 24), cartao, font=fonte("verdana", 30, True), fill=BRANCO)
        d.text((x0 + 30, m + 74), f"Fatura de {mes_ano(p['periodo'])} · final {final}", font=fonte("verdana", 18),
               fill=BRANCO)
        d.text((x1 - 30, m + 30), "Total da fatura", font=fonte("verdana", 16), fill=BRANCO, anchor="ra")
        d.text((x1 - 30, m + 60), f"R$ {brl(total)}", font=fonte("verdana", 32, True), fill=BRANCO, anchor="ra")
        y = m + 180
        for i, (r, v) in enumerate([("Titular", p["nome"].upper()), ("CPF", p["cpf_doc"]),
                                    ("Vencimento", data_br(10, mes % 12 + 1, 2026)), ("Pagamento mínimo", f"R$ {brl(minimo)}")]):
            rotulo_valor(d, x0 + (i % 2) * 560, y + (i // 2) * 64, r, v, familia="verdana")
        y += 150
        y = tabela(d, x0, x1, y, [("Data", 0, "la"), ("Estabelecimento", 0.12, "la"), ("Valor (R$)", 1, "ra")],
                   [[f"{dia:02d}/{mes:02d}", loja, brl(v)] for dia, loja, v in sorted(compras)],
                   familia="verdana", cor=laranja, zebra=clarear(laranja, 0.9))
    else:
        azul = (30, 60, 110)
        d.text((x0, m), cartao.upper(), font=fonte("tahoma", 26, True), fill=azul)
        d.text((x0, m + 40), "Resumo da fatura", font=fonte("tahoma", 18), fill=PRETO)
        y = m + 90
        caixas = [("Total", f"R$ {brl(total)}"), ("Mínimo", f"R$ {brl(minimo)}"),
                  ("Vencimento", data_br(5, mes % 12 + 1, 2026)), ("Fechamento", data_br(28, mes, 2026))]
        largura = (x1 - x0 - 3 * 16) / 4
        for i, (r, v) in enumerate(caixas):
            bx = x0 + i * (largura + 16)
            d.rectangle([bx, y, bx + largura, y + 80], outline=azul, width=2)
            rotulo_valor(d, bx + 14, y + 12, r, v, familia="tahoma", tam=20)
        y += 110
        d.text((x0, y), f"Titular: {p['nome'].upper()}   ·   CPF {p['cpf_doc']}   ·   Cartão final {final}",
               font=fonte("tahoma", 16), fill=PRETO)
        y += 44
        for dia, loja, v in sorted(compras):
            linha_pontilhada(d, x0, x1, y, f"{dia:02d}/{mes:02d}  {loja}", brl(v), familia="courier", tam=16)
            y += 30
    d.text((x0, y + 20), "Pague até o vencimento para evitar juros e multa.", font=fonte("arial", 15), fill=CINZA)
    return recortar(img, y + 70 + m)


def boleto(p, rng):
    img, d = pagina(1300)
    m, x0, x1 = 44, 44, LARGURA - 44
    valor = rng.randint(8000, 150000)
    venc = data_br(rng.randint(5, 25), 10, 2026)
    linha_digitavel = (f"99990.{digitos(rng, 5)} {digitos(rng, 5)}.{digitos(rng, 6)} "
                       f"{digitos(rng, 5)}.{digitos(rng, 6)} {digitos(rng, 1)} {digitos(rng, 14)}")
    campos = [("Beneficiário", f"{p['empresa']} · CNPJ {p['cnpj_doc']}"), ("Pagador", f"{p['nome'].upper()} · CPF {p['cpf_doc']}"),
              ("Vencimento", venc), ("Valor do documento", f"R$ {brl(valor)}"),
              ("Nosso número", digitos(rng, 11)), ("Data do documento", data_br(rng.randint(1, 28), 9, 2026))]
    if p["variante"] == 0:
        d.text((x0, m), "999-9", font=fonte("arial", 30, True), fill=PRETO)
        d.line([x0 + 110, m, x0 + 110, m + 40], fill=PRETO, width=3)
        d.text((x0 + 130, m + 6), linha_digitavel, font=fonte("arial", 20, True), fill=PRETO)
        y = m + 56
        d.rectangle([x0, y, x1, y + 3 * 70], outline=PRETO, width=2)
        for i, (r, v) in enumerate(campos):
            cx = x0 + (i % 2) * (x1 - x0) / 2
            cy = y + (i // 2) * 70
            d.rectangle([cx, cy, cx + (x1 - x0) / 2, cy + 70], outline=PRETO, width=1)
            rotulo_valor(d, cx + 10, cy + 8, r, v, tam=16)
        y += 3 * 70 + 20
        d.text((x0, y), "Instruções: não receber após 30 dias do vencimento. Multa de 2% após o vencimento.",
               font=fonte("arial", 15), fill=PRETO)
        y += 40
        codigo_barras(d, x0, x0 + 760, y, 80, rng)
        y += 100
    else:
        verde = (40, 100, 70)
        for via in ("RECIBO DO PAGADOR", "FICHA DE COMPENSAÇÃO"):
            d.rectangle([x0, m, x1, m + 40], fill=verde)
            d.text((x0 + 12, m + 8), f"Carnê de pagamento · {via}", font=fonte("tahoma", 18, True), fill=BRANCO)
            d.text((x1 - 12, m + 8), "Banco 999", font=fonte("tahoma", 18, True), fill=BRANCO, anchor="ra")
            y = m + 56
            for i, (r, v) in enumerate(campos):
                rotulo_valor(d, x0 + 10 + (i % 3) * 370, y + (i // 3) * 60, r, v, familia="tahoma", tam=15)
            y += 140
            d.text((x0 + 10, y), linha_digitavel, font=fonte("courier", 17, True), fill=PRETO)
            y += 40
            if via == "FICHA DE COMPENSAÇÃO":
                codigo_barras(d, x0 + 10, x0 + 700, y, 70, rng)
                y += 90
            else:
                for x in range(x0, x1, 18):
                    d.line([x, y + 10, x + 9, y + 10], fill=CINZA, width=2)
                y += 40
            m = y
        y = m
    return recortar(img, y + 40)


def identity_card(p, rng):
    """Documento de identidade genérico: sem nome de estado, brasão ou layout oficial."""
    img, d = pagina(1100)
    m = 60
    nascimento = data_br(rng.randint(1, 28), rng.randint(1, 12), rng.randint(1965, 2002))
    emissao = data_br(rng.randint(1, 28), rng.randint(1, 12), rng.randint(2012, 2024))
    registro = f"{digitos(rng, 2)}.{digitos(rng, 3)}.{digitos(rng, 3)}-{digitos(rng, 1)}"
    filiacao = [dados.gerar_nome().upper(), dados.gerar_nome().upper()]
    naturalidade = rng.choice(["Vila Esperança", "Campo Alegre do Norte", "Porto das Garças"])
    campos = [("Nome", p["nome"].upper()), ("Registro geral", registro), ("CPF", p["cpf_doc"]),
              ("Data de nascimento", nascimento), ("Naturalidade", naturalidade), ("Filiação", filiacao[0]),
              ("", filiacao[1]), ("Data de expedição", emissao), ("Órgão emissor", ORGAO_IDENTIDADE)]
    titulo = "CARTEIRA DE IDENTIDADE · MODELO FICTÍCIO PARA TESTES"
    if p["variante"] == 0:
        cor = (70, 90, 120)
        x0, y0, x1, y1 = m, m, LARGURA - m, m + 640
        d.rounded_rectangle([x0, y0, x1, y1], radius=24, outline=cor, width=4, fill=(245, 246, 250))
        d.text((x0 + 30, y0 + 24), titulo, font=fonte("arial", 22, True), fill=cor)
        d.rectangle([x0 + 30, y0 + 80, x0 + 260, y0 + 380], outline=cor, width=2, fill=(225, 228, 235))
        d.text((x0 + 145, y0 + 230), "FOTO", font=fonte("arial", 22, True), fill=CINZA, anchor="mm")
        y = y0 + 80
        for r, v in campos:
            if r:
                rotulo_valor(d, x0 + 300, y, r, v, tam=17)
                y += 58
            else:  # segundo nome da filiação, logo abaixo do primeiro
                d.text((x0 + 300, y - 15), v, font=fonte("arial", 17, True), fill=PRETO)
                y += 43
        d.text((x0 + 30, y1 - 50), "Assinatura do titular: ______________________________", font=fonte("arial", 16),
               fill=PRETO)
        y = y1
    else:
        cor = (110, 70, 50)
        x0, x1 = m, LARGURA - m
        for lado in ("FRENTE", "VERSO"):
            y0 = m if lado == "FRENTE" else m + 380
            d.rectangle([x0, y0, x1, y0 + 340], outline=cor, width=3)
            d.text((x0 + 20, y0 + 14), f"{titulo} · {lado}", font=fonte("verdana", 17, True), fill=cor)
            if lado == "FRENTE":
                d.ellipse([x0 + 40, y0 + 70, x0 + 220, y0 + 290], outline=cor, width=2)
                d.text((x0 + 130, y0 + 180), "FOTO", font=fonte("verdana", 18, True), fill=CINZA, anchor="mm")
                y = y0 + 70
                for r, v in campos[:4]:
                    rotulo_valor(d, x0 + 260, y, r, v, familia="verdana", tam=16)
                    y += 54
            else:
                y = y0 + 60
                for r, v in campos[4:]:
                    d.text((x0 + 30, y), f"{r + ':' if r else '':<20} {v}", font=fonte("courier", 17), fill=PRETO)
                    y += 40
                d.text((x0 + 30, y + 10), "Polegar direito: [      ]", font=fonte("courier", 17), fill=PRETO)
        y = m + 380 + 340
    return recortar(img, y + m)


def income_report(p, rng):
    img, d = pagina(1900)
    m, x0, x1 = 44, 44, LARGURA - 44
    salarios = rng.randint(3000000, 9000000)
    inss = arredondar_pct(salarios, 9)
    irrf = arredondar_pct(salarios, rng.randint(3, 9))
    decimo = salarios // 12
    secoes = [
        ("1. Fonte pagadora", [("Nome empresarial", p["empresa"]), ("CNPJ", p["cnpj_doc"])]),
        ("2. Pessoa física beneficiária", [("Nome completo", p["nome"].upper()), ("CPF", p["cpf_doc"]),
                                            ("Natureza do rendimento", "Rendimento do trabalho assalariado")]),
        ("3. Rendimentos tributáveis, deduções e imposto retido", [
            ("Total dos rendimentos (inclusive férias)", brl(salarios)),
            ("Contribuição previdenciária oficial", brl(inss)),
            ("Imposto sobre a renda retido na fonte", brl(irrf))]),
        ("4. Rendimentos isentos e não tributáveis", [("Parcela isenta de aposentadoria", "0,00"),
                                                      ("Outros", brl(rng.randint(0, 200000)))]),
        ("5. Rendimentos sujeitos à tributação exclusiva", [("Décimo terceiro salário", brl(decimo)),
                                                             ("IRRF sobre o 13º salário",
                                                              brl(arredondar_pct(decimo, 5)))]),
    ]
    if p["variante"] == 0:
        cor = (50, 50, 50)
        d.text((x0, m), "COMPROVANTE DE RENDIMENTOS PAGOS E DE IMPOSTO SOBRE A RENDA RETIDO NA FONTE",
               font=fonte("arial", 18, True), fill=PRETO)
        d.text((x0, m + 30), "Ano-calendário 2025 · Informe de rendimentos anual do empregador",
               font=fonte("arial", 16), fill=CINZA)
        y = m + 76
        for titulo, campos in secoes:
            d.rectangle([x0, y, x1, y + 30], fill=clarear(cor, 0.85))
            d.text((x0 + 10, y + 6), titulo, font=fonte("arial", 16, True), fill=PRETO)
            y += 36
            for r, v in campos:
                d.text((x0 + 16, y), r, font=fonte("arial", 16), fill=PRETO)
                d.text((x1 - 16, y), v, font=fonte("arial", 16, True), fill=PRETO, anchor="ra")
                y += 28
            y += 10
    else:
        y = m
        d.text((x0, y), "INFORME DE RENDIMENTOS - ANO-CALENDÁRIO 2025", font=fonte("courier", 20, True), fill=PRETO)
        y += 40
        for titulo, campos in secoes:
            d.text((x0, y), titulo.upper(), font=fonte("courier", 17, True), fill=PRETO)
            y += 30
            for r, v in campos:
                linha_pontilhada(d, x0 + 20, x1, y, r, v, tam=16)
                y += 28
            y += 12
    d.text((x0, y + 10), f"Responsável pelas informações: {dados.gerar_nome()} · Data: 27/02/2026",
           font=fonte("arial", 15), fill=CINZA)
    return recortar(img, y + 60 + m)


def rpa(p, rng):
    img, d = pagina(1500)
    m, x0, x1 = 50, 50, LARGURA - 50
    bruto = rng.randint(80000, 600000)
    inss = arredondar_pct(bruto, 11)
    iss = arredondar_pct(bruto, 5)
    irrf = rng.choice((0, arredondar_pct(bruto - inss, 7)))
    liquido = bruto - inss - iss - irrf
    servico = rng.choice(["Revisão de textos institucionais", "Manutenção de jardim", "Aulas de reforço escolar",
                          "Instalação elétrica residencial"])
    itens = [("Valor do serviço", bruto), ("(-) INSS (11%)", inss), ("(-) ISS (5%)", iss), ("(-) IRRF", irrf),
             ("Valor líquido pago", liquido)]
    data = data_br(rng.randint(1, 28), int(p["periodo"][5:7]), 2026)
    if p["variante"] == 0:
        cor = (40, 90, 120)
        d.rectangle([x0, m, x1, m + 70], fill=cor)
        d.text((x0 + 20, m + 18), "RPA · RECIBO DE PAGAMENTO A AUTÔNOMO", font=fonte("tahoma", 26, True), fill=BRANCO)
        y = m + 100
        for i, (r, v) in enumerate([("Contratante", p["empresa"]), ("CNPJ", p["cnpj_doc"]),
                                    ("Prestador de serviço", p["nome"].upper()), ("CPF", p["cpf_doc"]),
                                    ("Serviço prestado", servico), ("Competência", mes_ano(p["periodo"]))]):
            rotulo_valor(d, x0 + (i % 2) * 600, y + (i // 2) * 64, r, v, familia="tahoma")
        y += 210
        y = tabela(d, x0, x1, y, [("Discriminação", 0, "la"), ("Valor (R$)", 1, "ra")],
                   [[r, brl(v)] for r, v in itens], familia="tahoma", cor=cor, zebra=clarear(cor, 0.9))
    else:
        y = m
        d.text((LARGURA // 2, y), "RECIBO DE PAGAMENTO A AUTÔNOMO", font=fonte("arial", 26, True), fill=PRETO,
               anchor="ma")
        y += 60
        texto = (f"Recebi de {p['empresa']}, CNPJ {p['cnpj_doc']}, a importância líquida de R$ {brl(liquido)}, "
                 f"referente a {servico.lower()} prestado(a) em {mes_ano(p['periodo'])}, conforme discriminação abaixo.")
        for linha in imagens.quebrar(texto, fonte("arial", 19), x1 - x0):
            d.text((x0, y), linha, font=fonte("arial", 19), fill=PRETO)
            y += 30
        y += 20
        for r, v in itens:
            linha_pontilhada(d, x0, x1, y, r, brl(v), familia="arial", tam=18)
            y += 34
        y += 20
        d.text((x0, y), f"Prestador: {p['nome'].upper()} · CPF {p['cpf_doc']} · Data: {data}", font=fonte("arial", 17),
               fill=PRETO)
        y += 40
    d.text((x0, y + 30), "Assinatura do prestador: ______________________________", font=fonte("arial", 17),
           fill=PRETO)
    return recortar(img, y + 90 + m)


def arredondar_pct(valor, pct):
    return dados.arredondar(Fraction(valor * pct, 100))


# tipo de desenho -> (true_type, função, campos do gabarito preenchidos)
TIPOS = {
    "inss": ("inss_benefit", inss_benefit, {"periodo"}),
    "extrato": ("bank_statement", bank_statement, {"periodo"}),
    "irpf": ("tax_return", tax_return, set()),
    "fatura_cartao": ("other_document", credit_card_bill, {"periodo"}),
    "boleto": ("other_document", boleto, {"empresa"}),
    "identidade": ("other_document", identity_card, set()),
    "informe_rendimentos": ("other_document", income_report, {"empresa"}),
    "rpa": ("other_document", rpa, {"periodo", "empresa"}),
}
PERIODOS = ["2026-09", "2026-08"]


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------

def ler(nome):
    with open(PASTA_DADOS / nome, newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        return leitor.fieldnames, list(leitor)


def gravar(nome, colunas, linhas, terminador="\n"):
    with open(PASTA_DADOS / nome, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=colunas, lineterminator=terminador)
        escritor.writeheader()
        escritor.writerows(linhas)


def deste_script(linha):
    return linha.get("applicant_id") in CLIENTES_NOVOS or linha.get("file", "").startswith(
        PREFIXO_SEM_CLIENTE) or linha.get("file", "").startswith(tuple(f"{c}_" for c in CLIENTES_NOVOS))


def preparar_unicidade(cadastros, documentos):
    """Evita repetir nomes, CPFs e CNPJs da base (gerar_nome/gerar_cpf/gerar_cnpj consultam estes conjuntos)."""
    for c in cadastros:
        dados._nomes_usados.add(c["name"])
        dados._identificadores_usados.add(c["cpf"])
    for d in documentos:
        for campo in ("cpf_on_doc", "employer_cnpj"):
            if d[campo]:
                dados._identificadores_usados.add(dados.so_digitos(d[campo]))


def documento_csv(arquivo, cid, tipo, periodo="", nome="", cpf="", empresa="", cnpj=""):
    linha = {c: "" for c in COLUNAS_DOCUMENTOS}
    linha.update(file=arquivo, applicant_id=cid, true_type=tipo, pay_period=periodo, name_on_doc=nome,
                 cpf_on_doc=cpf, employer=empresa, employer_cnpj=cnpj, degradation="none")
    return linha


def holerites_a17(cli):
    """Holerites do A17 com os geradores da base (renda fixa = 3,3x a parcela), como linhas de CSV."""
    docs, rubricas = [], []
    for doc in dados.holerites_padrao(cli, MULTIPLO_A17):
        linha = {c: doc[c] for c in COLUNAS_DOCUMENTOS if c in doc}
        venc = sum(v for k, v, _ in doc["linhas"] if RUBRICAS[k][2] == "earning")
        desc = sum(v for k, v, _ in doc["linhas"] if RUBRICAS[k][2] == "deduction")
        linha.update(total_earnings=reais(venc), total_deductions=reais(desc), net_pay=reais(venc - desc))
        docs.append(linha)
        for chave, valor, descricao in doc["linhas"]:
            codigo, descricao_padrao, kind, conta = RUBRICAS[chave]
            rubricas.append({"file": doc["file"], "code": codigo, "description": descricao or descricao_padrao,
                             "kind": kind, "amount": reais(valor), "counts_as_income": conta})
    return docs, rubricas


def gerar():
    _, cadastros = ler("applicants.csv")
    _, documentos = ler("documents.csv")
    _, rubricas = ler("line_items.csv")
    cadastros = [c for c in cadastros if not deste_script(c)]
    documentos = [d for d in documentos if not deste_script(d)]
    rubricas = [r for r in rubricas if not deste_script(r)]

    dados.rng = random.Random(f"{SEMENTE}:nao_holerites")
    rng = dados.rng
    preparar_unicidade(cadastros, documentos)
    empresa_a17 = next((d["employer"], dados.so_digitos(d["employer_cnpj"])) for d in documentos
                       if d["employer"] == EMPRESA_A17)

    clientes = {}
    for cid in CLIENTES_NOVOS:
        nome, cpf = dados.gerar_nome(), dados.gerar_cpf()
        clientes[cid] = {"id": cid, "name": nome, "cpf": cpf, "parcela": rng.randint(400, 1500) * 100,
                         "employer": empresa_a17, "nome_doc": nome.upper(), "cpf_doc": mascara_cpf(cpf)}
        cadastros.append({"applicant_id": cid, "name": nome, "cpf": cpf,
                          "installment_amount": reais(clientes[cid]["parcela"]), "analysis_date": DATA_ANALISE})

    novos_holerites, novas_rubricas = holerites_a17(clientes["A17"])
    documentos += novos_holerites
    rubricas += novas_rubricas

    # Pessoas e empresas dos documentos de exemplo; o 1º exemplo de identidade é do A17 e o 1º do INSS, do N17.
    a_desenhar = []
    empresas = list(EMPRESAS_FICTICIAS)
    rng.shuffle(empresas)
    for chave, (tipo, _, campos) in TIPOS.items():
        for variante in (0, 1):
            dono = {("identidade", 0): "A17", ("inss", 0): "N17"}.get((chave, variante))
            if dono:
                nome, cpf, cid = clientes[dono]["name"], clientes[dono]["cpf"], dono
                arquivo = f"{dono}_{chave}{'_' + PERIODOS[variante] if 'periodo' in campos else ''}.png"
            else:
                nome, cpf, cid = dados.gerar_nome(), dados.gerar_cpf(), ""
                arquivo = f"{PREFIXO_SEM_CLIENTE}{chave}_{variante + 1}.png"
            periodo = PERIODOS[variante] if "periodo" in campos else ""
            empresa, cnpj = (empresas.pop(), dados.gerar_cnpj()) if "empresa" in campos else ("", "")
            p = {"variante": variante, "nome": nome, "cpf_doc": mascara_cpf(cpf), "periodo": periodo or PERIODOS[0],
                 "empresa": empresa, "cnpj_doc": mascara_cnpj(cnpj) if cnpj else ""}
            # Boleto: a empresa é a beneficiária, não um empregador.
            empregador = (empresa, mascara_cnpj(cnpj)) if chave in ("informe_rendimentos", "rpa") else ("", "")
            documentos.append(documento_csv(arquivo, cid, tipo, periodo, nome.upper(), mascara_cpf(cpf), *empregador))
            a_desenhar.append((arquivo, chave, p))

    gravar("applicants.csv", COLUNAS_CADASTROS, cadastros)
    gravar("documents.csv", COLUNAS_DOCUMENTOS, documentos)
    gravar("line_items.csv", COLUNAS_RUBRICAS, rubricas)
    atualizar_gabarito(clientes)
    return clientes, novos_holerites, novas_rubricas, a_desenhar


def atualizar_gabarito(clientes):
    """Linhas do A17 e do N17 em ground_truth.csv, sem decisão, motivo e renda: preenchimento manual.

    Uma linha que já existe não é tocada, para não apagar o que foi preenchido à mão.
    """
    colunas, linhas = ler("ground_truth.csv")
    existentes = {l["applicant_id"] for l in linhas}
    cenarios = {
        "A17": ("3 valid pay stubs (income above 3x) + an extra identity card", "R1"),
        "N17": ("Only an INSS benefit statement", "R1"),
    }
    for cid in CLIENTES_NOVOS:
        if cid in existentes:
            continue
        cenario, regra = cenarios[cid]
        linhas.append({c: "" for c in colunas} | {"applicant_id": cid, "scenario": cenario, "rule_tested": regra,
                                                  "installment_amount": reais(clientes[cid]["parcela"]).rstrip("0")
                                                  .rstrip(".")})
    gravar("ground_truth.csv", colunas, linhas, terminador="\r\n")


# ---------------------------------------------------------------------------
# Imagens
# ---------------------------------------------------------------------------

def desenhar(novos_holerites, novas_rubricas, a_desenhar):
    linhas = {}
    for r in novas_rubricas:
        linhas.setdefault(r["file"], []).append(r)
    salarios = imagens.salarios_contratuais(novos_holerites, linhas)
    arquivos = []
    for doc in novos_holerites:
        img = imagens.renderizar(doc, linhas[doc["file"]], salarios.get(doc["applicant_id"]))
        salvar(img, PASTA_IMAGENS / doc["file"])
        arquivos.append(doc["file"])
    for arquivo, chave, p in a_desenhar:
        rng = random.Random(f"{SEMENTE}:{arquivo}")
        img = marca_dagua(TIPOS[chave][1](p, rng))
        salvar(img, PASTA_IMAGENS / arquivo)
        arquivos.append(arquivo)
    return arquivos


def mosaico(arquivos):
    caixa_l, caixa_a, espaco, rotulo, colunas = 360, 480, 18, 30, 5
    linhas = (len(arquivos) + colunas - 1) // colunas
    img = Image.new("RGB", (colunas * caixa_l + (colunas + 1) * espaco,
                            linhas * (caixa_a + rotulo) + (linhas + 1) * espaco), (220, 220, 220))
    d = ImageDraw.Draw(img)
    for i, arquivo in enumerate(arquivos):
        miniatura = Image.open(PASTA_IMAGENS / arquivo).convert("RGB")
        miniatura.thumbnail((caixa_l, caixa_a), Image.Resampling.LANCZOS)
        x = espaco + (i % colunas) * (caixa_l + espaco)
        y = espaco + (i // colunas) * (caixa_a + rotulo + espaco)
        d.text((x, y), arquivo, font=fonte("arial", 15, True), fill=PRETO)
        img.paste(miniatura, (x, y + rotulo))
    salvar(img, PASTA_IMAGENS / ARQUIVO_AMOSTRA)


def main():
    clientes, novos_holerites, novas_rubricas, a_desenhar = gerar()
    arquivos = desenhar(novos_holerites, novas_rubricas, a_desenhar)
    mosaico(arquivos)
    print(f"Clientes: {', '.join(clientes)} | documentos: {len(arquivos)} "
          f"({len(novos_holerites)} holerites do A17 + {len(a_desenhar)} que não são holerite)")
    print(f"Mosaico: {(PASTA_IMAGENS / ARQUIVO_AMOSTRA).relative_to(PASTA_DADOS.parent)}")


if __name__ == "__main__":
    main()
