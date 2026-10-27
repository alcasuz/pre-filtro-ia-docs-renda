"""Gera as imagens da base de teste: um PNG por linha de data/documents.csv.

Lê data/documents.csv e data/line_items.csv e grava em data/images/, com o nome
da coluna file. Tudo o que aparece nas imagens é em português, como num
holerite real; nome e CPF só aparecem quando estão preenchidos no CSV. Os
totais são impressos como estão no CSV (é assim que a N15 sai com a conta
errada). Campos que não existem no CSV (matrícula, cargo, admissão etc.) são
inventados de forma estável por cliente e não fazem parte do gabarito.

Nenhuma API é chamada. Semente fixa: rodar duas vezes gera arquivos idênticos
na mesma máquina (as fontes são as do sistema).

Uso: .venv/bin/python generation/generate_images.py
"""

import csv
import random
import re
import textwrap
from collections import Counter, defaultdict
from datetime import date, timedelta
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from generate_data import CHAVE_POR_CODIGO, FAIXAS_IRRF, INCIDENCIA, SEMENTE, arredondar, centavos

PASTA_DADOS = Path(__file__).resolve().parent.parent / "data"
PASTA_IMAGENS = PASTA_DADOS / "images"
ARQUIVO_AMOSTRA = "_sample.png"
LARGURA = 1200
CORES_PALETA = 64

PRETO = (30, 30, 30)
CINZA = (105, 105, 105)
BRANCO = (255, 255, 255)


# ---------------------------------------------------------------------------
# Fontes e formatação
# ---------------------------------------------------------------------------

PASTA_FONTES = Path("/System/Library/Fonts/Supplemental")
FONTES = {
    "arial": ("Arial.ttf", "Arial Bold.ttf"),
    "verdana": ("Verdana.ttf", "Verdana Bold.ttf"),
    "tahoma": ("Tahoma.ttf", "Tahoma Bold.ttf"),
    "courier": ("Courier New.ttf", "Courier New Bold.ttf"),
}


@lru_cache(maxsize=None)
def fonte(familia, tamanho, negrito=False):
    return ImageFont.truetype(str(PASTA_FONTES / FONTES[familia][negrito]), tamanho)


MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def brl(valor_centavos):
    """Centavos -> '2.388,00'."""
    sinal = "-" if valor_centavos < 0 else ""
    c = abs(valor_centavos)
    return f"{sinal}{c // 100:,}".replace(",", ".") + f",{c % 100:02d}"


def numero(valor, casas=2):
    return f"{float(valor):.{casas}f}".replace(".", ",")


def competencia_texto(pay_period, estilo):
    ano, mes = int(pay_period[:4]), int(pay_period[5:7])
    if estilo == "extenso":
        return f"{MESES[mes - 1]}/{ano}"
    if estilo == "numerico":
        return f"{mes:02d}/{ano}"
    return f"{MESES[mes - 1][:3].upper()}/{ano}"


def quebrar(texto, fnt, largura):
    """Quebra o texto em linhas que cabem em largura (px) na fonte dada."""
    linhas, atual = [], ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if fnt.getlength(tentativa) <= largura:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def clarear(cor, fator):
    return tuple(int(c + (255 - c) * fator) for c in cor)


def recortar(img, altura):
    return img.crop((0, 0, img.width, altura))


def redimensionar(img, largura):
    if img.width == largura:
        return img
    altura = round(img.height * largura / img.width)
    return img.resize((largura, altura), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------------------
# Empresas e dados do funcionário que não estão no CSV
# ---------------------------------------------------------------------------

EMPRESAS = {
    "Alimentos Quintal Verde Ltda": {
        "layout": "classico", "cor": (46, 110, 60),
        "endereco": "Rod. dos Ipês, km 12, Galpão 3 - Distrito Industrial - Campinas/SP",
        "cargos": ["Auxiliar de Produção", "Operador de Máquinas", "Analista de Qualidade",
                   "Assistente Administrativo"],
    },
    "Metalúrgica Serra Fria Ltda": {
        "layout": "erp", "cor": (38, 70, 120),
        "endereco": "Av. das Forjas, 1450 - Jardim Bandeirantes - Contagem/MG",
        "cargos": ["Soldador", "Torneiro Mecânico", "Operador de Prensa", "Técnico de Manutenção"],
    },
    "Rota Leste Transportes Ltda": {
        "layout": "matricial", "cor": (60, 60, 60),
        "endereco": "Rua Caminho do Porto, 88 - Vila Operária - Guarulhos/SP",
        "cargos": ["Motorista", "Ajudante de Carga", "Conferente", "Assistente de Logística"],
    },
    "Clínica Bem Cuidar Ltda": {
        "layout": "erp", "cor": (0, 120, 130),
        "endereco": "Rua das Acácias, 312, sala 4 - Centro - Londrina/PR",
        "cargos": ["Técnico de Enfermagem", "Recepcionista", "Enfermeiro", "Auxiliar de Farmácia"],
    },
    "Supermercados Pé de Feijão Ltda": {
        "layout": "matricial", "cor": (60, 60, 60),
        "endereco": "Av. Brasil Novo, 2020 - Parque das Flores - Feira de Santana/BA",
        "cargos": ["Operador de Caixa", "Repositor", "Açougueiro", "Fiscal de Loja"],
    },
    "Vigilância Torre Alta Ltda": {
        "layout": "classico", "cor": (120, 40, 40),
        "endereco": "Rua Sentinela, 77 - Bairro Alto - Curitiba/PR",
        "cargos": ["Vigilante", "Vigilante Líder", "Supervisor de Segurança"],
    },
}
DEPARTAMENTOS = ["Operações", "Administrativo", "Produção", "Atendimento", "Logística"]

MENSAGENS_COMUNS = [
    "Crédito efetuado em conta corrente.",
    "Mantenha seus dados cadastrais atualizados com o RH.",
    "Dúvidas sobre este recibo: procure o Departamento Pessoal.",
    "Campanha de vacinação contra a gripe: inscrições abertas no RH.",
    "O prazo para entrega de atestados médicos é de 48 horas.",
]


def dados_funcionario(applicant_id, empresa):
    """Matrícula, cargo etc. estáveis por cliente (iguais em todos os holerites dele)."""
    rng = random.Random(f"{SEMENTE}:funcionario:{applicant_id}")
    return {
        "matricula": str(rng.randint(1000, 98000)),
        "cargo": rng.choice(EMPRESAS[empresa]["cargos"]),
        "cbo": f"{rng.randint(1000, 9999)}-{rng.randint(10, 99)}",
        "departamento": rng.choice(DEPARTAMENTOS),
        "admissao": date(rng.randint(2014, 2024), rng.randint(1, 12), rng.randint(1, 28)),
        "agencia": str(rng.randint(1000, 9999)),
        "conta": f"{rng.randint(10000, 99999)}-{rng.randint(0, 9)}",
    }


# ---------------------------------------------------------------------------
# Conteúdo do holerite (comum aos três layouts)
# ---------------------------------------------------------------------------

CODIGOS_INCIDENCIA = {codigo for codigo, chave in CHAVE_POR_CODIGO.items() if chave in INCIDENCIA}
REFERENCIAS_FIXAS = {"0011": 30, "0012": 40, "0014": 3, "0510": 40, "0520": 6}


def dias_na_descricao(descricao):
    m = re.search(r"\((\d+) DIAS\)", descricao)
    return int(m.group(1)) if m else None


def aliquota_irrf(base):
    for teto, aliquota, _ in FAIXAS_IRRF:
        if teto is None or base <= teto:
            return aliquota


def referencia(linha, salario, base_inss, base_irrf):
    codigo, valor = linha["code"], centavos(linha["amount"])
    hora = Fraction(salario, 220)
    if codigo in ("0001", "0030"):
        return numero(dias_na_descricao(linha["description"]) or 30)
    if codigo == "0020":
        return numero(Fraction(valor) / (hora * Fraction(3, 2)))
    if codigo == "0010":
        return numero(Fraction(valor) / (hora * Fraction(2, 10)))
    if codigo in REFERENCIAS_FIXAS:
        return numero(REFERENCIAS_FIXAS[codigo])
    if codigo == "0501" and base_inss:
        return numero(Fraction(valor * 100, base_inss))
    if codigo == "0502":
        return numero(aliquota_irrf(base_irrf) * 100)
    return ""


def salarios_contratuais(documentos, linhas):
    """Salário contratual por cliente: o salário-base mais frequente dos meses cheios."""
    por_cliente = defaultdict(Counter)
    for doc in documentos:
        for l in linhas[doc["file"]]:
            if l["code"] == "0001" and dias_na_descricao(l["description"]) is None:
                por_cliente[doc["applicant_id"]][centavos(l["amount"])] += 1
    return {cid: contagem.most_common(1)[0][0] for cid, contagem in por_cliente.items()}


def montar_holerite(doc, linhas_doc, salario_cliente, rng):
    func = dados_funcionario(doc["applicant_id"], doc["employer"])
    tipo = doc["true_type"]

    salario = salario_cliente
    for l in linhas_doc:
        if l["code"] == "0001" and dias_na_descricao(l["description"]) is None:
            salario = centavos(l["amount"])

    ganhos = [l for l in linhas_doc if l["kind"] == "earning"]
    inss = sum(centavos(l["amount"]) for l in linhas_doc if l["code"] == "0501")
    if tipo == "payslip_13th":
        base_inss = 0
        base_fgts = sum(centavos(l["amount"]) for l in ganhos)
    else:
        base_inss = sum(centavos(l["amount"]) for l in ganhos if l["code"] in CODIGOS_INCIDENCIA)
        base_fgts = base_inss
    base_irrf = base_inss - inss if base_inss else 0

    itens = []
    for l in linhas_doc:
        valor = brl(centavos(l["amount"]))
        itens.append((
            l["code"], l["description"], referencia(l, salario, base_inss, base_irrf),
            valor if l["kind"] == "earning" else "",
            valor if l["kind"] == "deduction" else "",
        ))

    extras = []
    ano, mes = int(doc["pay_period"][:4]), int(doc["pay_period"][5:7])
    if tipo == "payslip_vacation":
        dias = next(dias_na_descricao(l["description"]) for l in linhas_doc if l["code"] == "0030")
        inicio_aquisitivo = func["admissao"].replace(year=ano - 1)
        fim_aquisitivo = inicio_aquisitivo.replace(year=ano) - timedelta(days=1)
        inicio_gozo = date(ano, mes, 30 - dias + 1)
        fim_gozo = date(ano, mes, 30)
        extras = [
            ("Período aquisitivo", f"{inicio_aquisitivo:%d/%m/%Y} a {fim_aquisitivo:%d/%m/%Y}"),
            ("Período de gozo", f"{inicio_gozo:%d/%m/%Y} a {fim_gozo:%d/%m/%Y}"),
            ("Dias de férias", str(dias)),
        ]
    elif tipo == "payslip_13th":
        extras = [("Parcela", "1ª parcela"), ("Data de pagamento", f"20/{mes:02d}/{ano}")]

    titulos = {
        "payslip": "Recibo de Pagamento de Salário",
        "payslip_vacation": "Recibo de Férias",
        "payslip_13th": "Recibo de 13º Salário - 1ª Parcela",
    }
    mensagens = rng.sample(MENSAGENS_COMUNS, rng.randint(1, 2))
    if doc["extra_text"]:
        mensagens.append(doc["extra_text"])

    return {
        "tipo": tipo,
        "titulo": titulos[tipo],
        "empresa": doc["employer"],
        "cnpj": doc["employer_cnpj"],
        "endereco": EMPRESAS[doc["employer"]]["endereco"],
        "cor": EMPRESAS[doc["employer"]]["cor"],
        "nome": doc["name_on_doc"],
        "cpf": doc["cpf_on_doc"],
        "matricula": func["matricula"],
        "cargo": func["cargo"],
        "cbo": func["cbo"],
        "departamento": func["departamento"],
        "admissao": f"{func['admissao']:%d/%m/%Y}",
        "banco": f"Ag. {func['agencia']} / C.C. {func['conta']}",
        "competencia": doc["pay_period"],
        "extras": extras,
        "itens": itens,
        "total_vencimentos": brl(centavos(doc["total_earnings"])),
        "total_descontos": brl(centavos(doc["total_deductions"])),
        "liquido": brl(centavos(doc["net_pay"])),
        "rodape": [
            ("Salário-base", brl(salario)),
            ("Base INSS", brl(base_inss)),
            ("Base FGTS", brl(base_fgts)),
            ("FGTS do mês", brl(arredondar(base_fgts * Fraction(8, 100)))),
            ("Base IRRF", brl(base_irrf)),
            ("Faixa IRRF", numero(aliquota_irrf(base_irrf) * 100) + "%"),
        ],
        "mensagens": mensagens,
    }


def campos_funcionario(h):
    """Campos do funcionário; nome e CPF só entram quando existem no CSV."""
    linha1 = [("Matrícula", h["matricula"], 1)]
    if h["nome"]:
        linha1.append(("Nome do funcionário", h["nome"], 3.2))
    if h["cpf"]:
        linha1.append(("CPF", h["cpf"], 1.5))
    linha2 = [("Cargo", h["cargo"], 2), ("CBO", h["cbo"], 1),
              ("Departamento", h["departamento"], 1.4), ("Admissão", h["admissao"], 1)]
    linhas = [linha1, linha2]
    if h["extras"]:
        linhas.append([(rotulo, valor, 1) for rotulo, valor in h["extras"]])
    return linhas


# ---------------------------------------------------------------------------
# Layout 1: formulário clássico (grade com bordas, Arial)
# ---------------------------------------------------------------------------

def celulas(d, x0, x1, y, campos, altura, cor):
    total = sum(peso for *_, peso in campos)
    x = x0
    for i, (rotulo, valor, peso) in enumerate(campos):
        xf = x1 if i == len(campos) - 1 else round(x + (x1 - x0) * peso / total)
        d.rectangle([x, y, xf, y + altura], outline=cor, width=1)
        d.text((x + 8, y + 6), rotulo, font=fonte("arial", 13), fill=CINZA)
        d.text((x + 8, y + 25), valor, font=fonte("arial", 17), fill=PRETO)
        x = xf
    return y + altura


def layout_classico(h):
    img = Image.new("RGB", (LARGURA, 2600), BRANCO)
    d = ImageDraw.Draw(img)
    m = 40
    x0, x1 = m, LARGURA - m
    cor = PRETO

    y = m
    d.rectangle([x0, y, x1, y + 120], outline=cor, width=2)
    d.text((x0 + 16, y + 14), h["empresa"].upper(), font=fonte("arial", 24, True), fill=h["cor"])
    d.text((x0 + 16, y + 52), f"CNPJ: {h['cnpj']}", font=fonte("arial", 16), fill=PRETO)
    d.text((x0 + 16, y + 80), h["endereco"], font=fonte("arial", 14), fill=CINZA)
    d.text((x1 - 16, y + 16), h["titulo"], font=fonte("arial", 20, True), fill=PRETO, anchor="ra")
    d.text((x1 - 16, y + 54), f"Competência: {competencia_texto(h['competencia'], 'extenso')}",
           font=fonte("arial", 17), fill=PRETO, anchor="ra")
    y += 120

    for campos in campos_funcionario(h):
        y = celulas(d, x0, x1, y, campos, 56, cor)

    colunas = [("Cód.", 80), ("Descrição", None), ("Referência", 130), ("Vencimentos", 170), ("Descontos", 170)]
    fixas = sum(w for _, w in colunas if w)
    larguras = [w or (x1 - x0 - fixas) for _, w in colunas]
    xs = [x0]
    for w in larguras:
        xs.append(xs[-1] + w)

    y += 10
    d.rectangle([x0, y, x1, y + 34], fill=(225, 225, 225), outline=cor)
    for i, (rotulo, _) in enumerate(colunas):
        if i < 2:
            d.text((xs[i] + 8, y + 8), rotulo, font=fonte("arial", 15, True), fill=PRETO)
        else:
            d.text((xs[i + 1] - 8, y + 8), rotulo, font=fonte("arial", 15, True), fill=PRETO, anchor="ra")
    y += 34
    altura_linha = 30
    n_linhas = max(len(h["itens"]), 10)
    topo = y
    for i in range(n_linhas):
        if i < len(h["itens"]):
            item = h["itens"][i]
            d.text((xs[0] + 8, y + 6), item[0], font=fonte("arial", 16), fill=PRETO)
            d.text((xs[1] + 8, y + 6), item[1], font=fonte("arial", 16), fill=PRETO)
            for col in (2, 3, 4):
                d.text((xs[col + 1] - 8, y + 6), item[col], font=fonte("arial", 16), fill=PRETO, anchor="ra")
        y += altura_linha
    d.rectangle([x0, topo, x1, y], outline=cor)
    for x in xs[1:-1]:
        d.line([x, topo - 34, x, y], fill=cor)

    d.rectangle([xs[3], y, xs[4], y + 54], outline=cor)
    d.rectangle([xs[4], y, xs[5], y + 54], outline=cor)
    d.text((xs[3] + 8, y + 5), "Total de Vencimentos", font=fonte("arial", 12), fill=CINZA)
    d.text((xs[4] + 8, y + 5), "Total de Descontos", font=fonte("arial", 12), fill=CINZA)
    d.text((xs[4] - 8, y + 26), h["total_vencimentos"], font=fonte("arial", 17, True), fill=PRETO, anchor="ra")
    d.text((xs[5] - 8, y + 26), h["total_descontos"], font=fonte("arial", 17, True), fill=PRETO, anchor="ra")
    d.text((x0 + 8, y + 8), "Crédito em conta: " + h["banco"], font=fonte("arial", 14), fill=CINZA)
    y += 54
    d.rectangle([xs[3], y, xs[5], y + 44], outline=cor, fill=(240, 240, 240))
    d.text((xs[3] + 8, y + 12), "Valor Líquido", font=fonte("arial", 17, True), fill=PRETO)
    d.text((xs[5] - 8, y + 11), h["liquido"], font=fonte("arial", 19, True), fill=PRETO, anchor="ra")
    y += 56

    y = celulas(d, x0, x1, y, [(r, v, 1) for r, v in h["rodape"]], 56, cor)

    y += 10
    fmsg = fonte("arial", 12)
    linhas_msg = [l for msg in h["mensagens"] for l in quebrar(msg, fmsg, x1 - x0 - 20)]
    altura_msg = 30 + 17 * len(linhas_msg)
    d.rectangle([x0, y, x1, y + altura_msg], outline=cor)
    d.text((x0 + 8, y + 6), "Mensagens", font=fonte("arial", 13, True), fill=CINZA)
    for i, linha in enumerate(linhas_msg):
        d.text((x0 + 10, y + 26 + 17 * i), linha, font=fmsg, fill=PRETO)
    y += altura_msg + 24

    d.text((x0, y), "Declaro ter recebido a importância líquida discriminada neste recibo.",
           font=fonte("arial", 14), fill=PRETO)
    y += 50
    d.line([x0, y, x0 + 220, y], fill=PRETO)
    d.line([x0 + 400, y, x1, y], fill=PRETO)
    d.text((x0, y + 6), "Data", font=fonte("arial", 13), fill=CINZA)
    d.text((x0 + 400, y + 6), "Assinatura do funcionário", font=fonte("arial", 13), fill=CINZA)
    return recortar(img, y + 30 + m)


# ---------------------------------------------------------------------------
# Layout 2: ERP moderno (faixa colorida, Verdana, linhas zebradas)
# ---------------------------------------------------------------------------

def layout_erp(h):
    img = Image.new("RGB", (LARGURA, 2600), BRANCO)
    d = ImageDraw.Draw(img)
    m = 44
    x0, x1 = m, LARGURA - m
    cor = h["cor"]

    d.rectangle([0, 0, LARGURA, 130], fill=cor)
    d.text((x0, 26), h["empresa"], font=fonte("verdana", 24, True), fill=BRANCO)
    d.text((x0, 66), f"CNPJ {h['cnpj']}", font=fonte("verdana", 15), fill=clarear(cor, 0.8))
    d.text((x0, 92), h["endereco"], font=fonte("verdana", 12), fill=clarear(cor, 0.7))
    titulo = "Demonstrativo de Pagamento" if h["tipo"] == "payslip" else h["titulo"]
    d.text((x1, 30), titulo, font=fonte("verdana", 18, True), fill=BRANCO, anchor="ra")
    d.text((x1, 66), f"Competência {competencia_texto(h['competencia'], 'numerico')}",
           font=fonte("verdana", 16), fill=BRANCO, anchor="ra")
    y = 160

    campos = [(r, v) for linha in campos_funcionario(h) for r, v, _ in linha] + [("Banco", h["banco"])]
    por_linha = 4
    largura_campo = (x1 - x0) / por_linha
    for i, (rotulo, valor) in enumerate(campos):
        cx = x0 + (i % por_linha) * largura_campo
        cy = y + (i // por_linha) * 58
        d.text((cx, cy), rotulo.upper(), font=fonte("verdana", 11), fill=CINZA)
        largura_valor = largura_campo * (2 if rotulo == "Nome do funcionário" else 1) - 12
        f_valor = fonte("verdana", 15, True)
        while f_valor.getlength(valor) > largura_valor and f_valor.size > 11:
            f_valor = fonte("verdana", f_valor.size - 1, True)
        d.text((cx, cy + 18), valor, font=f_valor, fill=PRETO)
    y += ((len(campos) - 1) // por_linha + 1) * 58 + 16

    colunas = [("Código", 90, "l"), ("Descrição", None, "l"), ("Ref.", 110, "r"),
               ("Proventos", 170, "r"), ("Descontos", 170, "r")]
    fixas = sum(w for _, w, _ in colunas if w)
    xs = [x0]
    for _, w, _ in colunas:
        xs.append(xs[-1] + (w or (x1 - x0 - fixas)))

    d.rectangle([x0, y, x1, y + 38], fill=clarear(cor, 0.82))
    for i, (rotulo, _, alinhamento) in enumerate(colunas):
        if alinhamento == "l":
            d.text((xs[i] + 10, y + 10), rotulo, font=fonte("verdana", 14, True), fill=cor)
        else:
            d.text((xs[i + 1] - 10, y + 10), rotulo, font=fonte("verdana", 14, True), fill=cor, anchor="ra")
    y += 38
    for n, item in enumerate(h["itens"]):
        if n % 2:
            d.rectangle([x0, y, x1, y + 32], fill=(246, 246, 246))
        for i, (_, _, alinhamento) in enumerate(colunas):
            texto = item[i]
            if alinhamento == "l":
                d.text((xs[i] + 10, y + 8), texto, font=fonte("verdana", 14), fill=PRETO)
            else:
                d.text((xs[i + 1] - 10, y + 8), texto, font=fonte("verdana", 14), fill=PRETO, anchor="ra")
        y += 32
    d.line([x0, y, x1, y], fill=clarear(cor, 0.5), width=2)
    y += 24

    blocos = [("Total de proventos", h["total_vencimentos"], False),
              ("Total de descontos", h["total_descontos"], False),
              ("Líquido a receber", h["liquido"], True)]
    largura_bloco = (x1 - x0 - 2 * 20) / 3
    for i, (rotulo, valor, destaque) in enumerate(blocos):
        bx = x0 + i * (largura_bloco + 20)
        fundo = cor if destaque else (244, 244, 244)
        texto = BRANCO if destaque else PRETO
        d.rounded_rectangle([bx, y, bx + largura_bloco, y + 84], radius=12, fill=fundo)
        d.text((bx + 18, y + 14), rotulo, font=fonte("verdana", 13), fill=texto if destaque else CINZA)
        d.text((bx + 18, y + 40), f"R$ {valor}", font=fonte("verdana", 22, True), fill=texto)
    y += 110

    d.text((x0, y), "BASES E ENCARGOS", font=fonte("verdana", 12, True), fill=CINZA)
    y += 24
    for i, (rotulo, valor) in enumerate(h["rodape"]):
        cx = x0 + (i % 3) * (x1 - x0) / 3
        cy = y + (i // 3) * 30
        d.text((cx, cy), f"{rotulo}: {valor}", font=fonte("verdana", 14), fill=PRETO)
    y += 72

    fmsg = fonte("verdana", 11)
    linhas_msg = [l for msg in h["mensagens"] for l in quebrar(msg, fmsg, x1 - x0 - 40)]
    altura_msg = 34 + 17 * len(linhas_msg)
    d.rectangle([x0, y, x1, y + altura_msg], fill=(250, 250, 250))
    d.rectangle([x0, y, x0 + 5, y + altura_msg], fill=cor)
    d.text((x0 + 20, y + 8), "Mensagens", font=fonte("verdana", 12, True), fill=cor)
    for i, linha in enumerate(linhas_msg):
        d.text((x0 + 20, y + 28 + 17 * i), linha, font=fmsg, fill=PRETO)
    y += altura_msg + 30

    d.text((x0, y), "Documento gerado eletronicamente pelo sistema FolhaFácil · Página 1 de 1",
           font=fonte("verdana", 11), fill=CINZA)
    return recortar(img, y + 20 + m)


# ---------------------------------------------------------------------------
# Layout 3: impressão matricial (Courier New, tracejados, formulário contínuo)
# ---------------------------------------------------------------------------

def layout_matricial(h):
    tamanho = 17
    fnt = fonte("courier", tamanho)
    m = 50
    colunas = int((LARGURA - 2 * m) / fnt.getlength("M"))
    sep, dup = "-" * colunas, "=" * colunas

    def lados(a, b):
        espaco = max(1, colunas - len(a) - len(b))
        return (a + " " * espaco + b)[:colunas]

    w_cod, w_ref, w_val = 6, 9, 15
    w_desc = colunas - w_cod - w_ref - 2 * w_val

    linhas = [(dup, False, tamanho)]
    linhas.append((lados(h["empresa"].upper(), h["titulo"].upper()), True, tamanho))
    linhas.append((lados(f"CNPJ: {h['cnpj']}",
                         f"COMPETÊNCIA: {competencia_texto(h['competencia'], 'abreviado')}"), False, tamanho))
    linhas.append((h["endereco"].upper()[:colunas], False, tamanho))
    linhas.append((sep, False, tamanho))
    for campos in campos_funcionario(h):
        texto = "   ".join(f"{rotulo.upper()}: {valor}" for rotulo, valor, _ in campos)
        for parte in textwrap.wrap(texto, colunas):
            linhas.append((parte, False, tamanho))
    linhas.append((sep, False, tamanho))
    linhas.append((f"{'CÓD':<{w_cod}}{'DESCRIÇÃO':<{w_desc}}{'REF.':>{w_ref}}"
                   f"{'VENCIMENTOS':>{w_val}}{'DESCONTOS':>{w_val}}", True, tamanho))
    linhas.append((sep, False, tamanho))
    for cod, desc, ref, venc, descv in h["itens"]:
        linhas.append((f"{cod:<{w_cod}}{desc[:w_desc - 1]:<{w_desc}}{ref:>{w_ref}}"
                       f"{venc:>{w_val}}{descv:>{w_val}}", False, tamanho))
    linhas.append((sep, False, tamanho))
    linhas.append((f"{'TOTAIS':>{w_cod + w_desc + w_ref}}{h['total_vencimentos']:>{w_val}}"
                   f"{h['total_descontos']:>{w_val}}", True, tamanho))
    linhas.append((f"{'LÍQUIDO A RECEBER ==>':>{colunas - w_val}}{h['liquido']:>{w_val}}", True, tamanho))
    linhas.append((f"CRÉDITO EM CONTA: {h['banco'].upper()}", False, tamanho))
    linhas.append((sep, False, tamanho))
    largura_rodape = colunas // len(h["rodape"])
    linhas.append(("".join(f"{r.upper():<{largura_rodape}}" for r, _ in h["rodape"]), False, tamanho))
    linhas.append(("".join(f"{v:<{largura_rodape}}" for _, v in h["rodape"]), False, tamanho))
    linhas.append((sep, False, tamanho))
    linhas.append(("MENSAGENS:", True, tamanho))
    pequeno = 13
    colunas_msg = int((LARGURA - 2 * m) / fonte("courier", pequeno).getlength("M"))
    for msg in h["mensagens"]:
        for parte in textwrap.wrap(msg, colunas_msg):
            linhas.append((parte, False, pequeno))
    linhas.append((dup, False, tamanho))
    linhas.append(("DECLARO TER RECEBIDO A IMPORTÂNCIA LÍQUIDA DISCRIMINADA NESTE RECIBO.", False, tamanho))
    linhas.append(("", False, tamanho))
    linhas.append(("____/____/________        ________________________________________", False, tamanho))
    linhas.append(("DATA                      ASSINATURA DO FUNCIONÁRIO", False, tamanho))

    alturas = [t + 9 for _, _, t in linhas]
    altura = 2 * m + sum(alturas)
    img = Image.new("RGB", (LARGURA, altura), (252, 252, 248))
    d = ImageDraw.Draw(img)
    faixa = 52
    for yb in range(0, altura, 2 * faixa):
        d.rectangle([0, yb, LARGURA, yb + faixa], fill=(231, 243, 231))
    for yb in range(30, altura, 60):
        d.ellipse([10, yb, 24, yb + 14], fill=(205, 205, 205))
        d.ellipse([LARGURA - 24, yb, LARGURA - 10, yb + 14], fill=(205, 205, 205))
    y = m
    for (texto, negrito, t), a in zip(linhas, alturas):
        d.text((m, y), texto, font=fonte("courier", t, negrito), fill=(45, 45, 60))
        y += a
    return img


LAYOUTS = {"classico": layout_classico, "erp": layout_erp, "matricial": layout_matricial}


# ---------------------------------------------------------------------------
# Documentos que não são holerite: N01 (conta de luz) e N02 (extrato)
# ---------------------------------------------------------------------------

def conta_de_luz(doc, rng):
    """Documento que não é de renda. Distribuidora inventada; sem nome nem CPF, como no CSV."""
    img = Image.new("RGB", (LARGURA, 2000), BRANCO)
    d = ImageDraw.Draw(img)
    m = 44
    x0, x1 = m, LARGURA - m
    laranja = (225, 120, 0)

    d.rectangle([0, 0, LARGURA, 120], fill=laranja)
    d.text((x0, 28), "COMPANHIA ELÉTRICA VALE DO SOL", font=fonte("tahoma", 28, True), fill=BRANCO)
    d.text((x0, 72), "Conta de energia elétrica · 2ª via", font=fonte("tahoma", 17), fill=BRANCO)
    y = 150

    consumo = rng.randint(140, 320)
    tarifa = Fraction(rng.randint(78, 92), 100)
    itens = [
        ("Consumo ativo (kWh)", f"{consumo}", numero(tarifa, 4), arredondar(consumo * tarifa * 100)),
        ("Adicional bandeira amarela", f"{consumo}", numero(Fraction(1885, 100000), 4),
         arredondar(consumo * Fraction(1885, 1000))),
        ("Contribuição de iluminação pública", "", "", rng.randint(1800, 3200)),
    ]
    total = sum(v for *_, v in itens)
    caixas = [("Unidade consumidora", str(rng.randint(10 ** 8, 10 ** 9 - 1))),
              ("Mês de referência", competencia_texto("2026-09", "abreviado")),
              ("Vencimento", "15/10/2026"), ("Total a pagar", f"R$ {brl(total)}")]
    largura_caixa = (x1 - x0 - 3 * 16) / 4
    for i, (rotulo, valor) in enumerate(caixas):
        bx = x0 + i * (largura_caixa + 16)
        d.rounded_rectangle([bx, y, bx + largura_caixa, y + 80], radius=10, outline=laranja, width=2)
        d.text((bx + 14, y + 12), rotulo, font=fonte("tahoma", 14), fill=CINZA)
        d.text((bx + 14, y + 38), valor, font=fonte("tahoma", 21, True), fill=PRETO)
    y += 110

    leitura_anterior = rng.randint(20000, 60000)
    d.text((x0, y), f"Leitura anterior: {leitura_anterior}   ·   Leitura atual: {leitura_anterior + consumo}"
                    f"   ·   Dias de faturamento: 30", font=fonte("tahoma", 16), fill=PRETO)
    y += 44

    d.rectangle([x0, y, x1, y + 34], fill=clarear(laranja, 0.8))
    for texto, x, anc in (("Descrição", x0 + 10, "la"), ("Quant.", x1 - 420, "ra"),
                          ("Tarifa (R$)", x1 - 240, "ra"), ("Valor (R$)", x1 - 10, "ra")):
        d.text((x, y + 8), texto, font=fonte("tahoma", 15, True), fill=PRETO, anchor=anc)
    y += 40
    for desc, quant, tar, valor in itens:
        d.text((x0 + 10, y), desc, font=fonte("tahoma", 15), fill=PRETO)
        d.text((x1 - 420, y), quant, font=fonte("tahoma", 15), fill=PRETO, anchor="ra")
        d.text((x1 - 240, y), tar, font=fonte("tahoma", 15), fill=PRETO, anchor="ra")
        d.text((x1 - 10, y), brl(valor), font=fonte("tahoma", 15), fill=PRETO, anchor="ra")
        y += 32
    d.line([x0, y, x1, y], fill=laranja, width=2)
    d.text((x1 - 10, y + 10), f"Total: R$ {brl(total)}", font=fonte("tahoma", 18, True), fill=PRETO, anchor="ra")
    y += 60

    d.text((x0, y), "Histórico de consumo (kWh)", font=fonte("tahoma", 16, True), fill=PRETO)
    y += 34
    altura_grafico = 160
    historico = [rng.randint(120, 340) for _ in range(11)] + [consumo]
    largura_barra = (x1 - x0) / 12
    meses = ["OUT", "NOV", "DEZ", "JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET"]
    for i, (valor, rotulo) in enumerate(zip(historico, meses)):
        bx = x0 + i * largura_barra + 12
        topo = y + altura_grafico - valor * altura_grafico / 360
        d.rectangle([bx, topo, bx + largura_barra - 24, y + altura_grafico], fill=clarear(laranja, 0.35))
        d.text((bx + (largura_barra - 24) / 2, y + altura_grafico + 6), rotulo,
               font=fonte("tahoma", 12), fill=CINZA, anchor="ma")
    y += altura_grafico + 50

    d.text((x0, y), "Pague nos canais de atendimento ou em qualquer agência autorizada.",
           font=fonte("tahoma", 14), fill=CINZA)
    y += 40
    x = x0
    while x < x1 - 4:
        w = rng.choice((2, 2, 3, 4))
        if rng.random() < 0.6:
            d.rectangle([x, y, x + w - 1, y + 70], fill=PRETO)
        x += w
    y += 80
    linha_digitavel = " ".join("".join(str(rng.randrange(10)) for _ in range(12)) for _ in range(4))
    d.text((x0, y), linha_digitavel, font=fonte("courier", 18), fill=PRETO)
    return recortar(img, y + 40 + m)


def extrato(doc, rng):
    """Extrato de conta corrente de um banco inventado (tipo não aceito na v1)."""
    img = Image.new("RGB", (LARGURA, 2400), BRANCO)
    d = ImageDraw.Draw(img)
    m = 44
    x0, x1 = m, LARGURA - m
    azul = (20, 50, 100)

    d.rectangle([0, 0, LARGURA, 110], fill=azul)
    d.text((x0, 24), "BANCO MARÉ ALTA", font=fonte("arial", 30, True), fill=BRANCO)
    d.text((x0, 66), "Extrato de conta corrente", font=fonte("arial", 17), fill=clarear(azul, 0.75))
    d.text((x1, 40), "Emitido em 01/10/2026 08:12", font=fonte("arial", 14), fill=clarear(azul, 0.75), anchor="ra")
    y = 136

    campos = []
    if doc["name_on_doc"]:
        campos.append(("Titular", doc["name_on_doc"]))
    if doc["cpf_on_doc"]:
        campos.append(("CPF", doc["cpf_on_doc"]))
    campos += [("Agência", str(rng.randint(1000, 9999))),
               ("Conta corrente", f"{rng.randint(10000, 99999)}-{rng.randint(0, 9)}"),
               ("Período", "01/09/2026 a 30/09/2026")]
    for i, (rotulo, valor) in enumerate(campos):
        cx = x0 + (i % 3) * (x1 - x0) / 3
        cy = y + (i // 3) * 54
        d.text((cx, cy), rotulo, font=fonte("arial", 13), fill=CINZA)
        d.text((cx, cy + 18), valor, font=fonte("arial", 17, True), fill=PRETO)
    y += ((len(campos) - 1) // 3 + 1) * 54 + 14

    pessoas = ["MARIANA T. CORREIA", "LOJA CASA DO PÃO", "R. FERNANDES", "J. P. AZEVEDO"]
    lancamentos = [
        (2, "PIX RECEBIDO - " + rng.choice(pessoas), rng.randint(5000, 40000)),
        (5, "PAGTO BOLETO - CONDOMÍNIO RESIDENCIAL", -rng.randint(40000, 90000)),
        (5, "COMPRA CARTÃO DÉBITO - MERCADINHO DA PRAÇA", -rng.randint(3000, 25000)),
        (8, "TED RECEBIDA - PAGAMENTO", rng.randint(150000, 450000)),
        (9, "PIX ENVIADO - " + rng.choice(pessoas), -rng.randint(5000, 30000)),
        (12, "DÉBITO AUTOMÁTICO - TELEFONIA MÓVEL", -rng.randint(4000, 12000)),
        (14, "COMPRA CARTÃO DÉBITO - FARMÁCIA SAÚDE JÁ", -rng.randint(2000, 15000)),
        (17, "PIX RECEBIDO - " + rng.choice(pessoas), rng.randint(2000, 20000)),
        (20, "SAQUE TERMINAL 24H", -rng.randint(10000, 40000)),
        (22, "PAGTO BOLETO - ESCOLA PEQUENO SABER", -rng.randint(30000, 80000)),
        (25, "COMPRA CARTÃO DÉBITO - POSTO ESTRELA", -rng.randint(8000, 25000)),
        (28, "RENDIMENTO POUPANÇA", rng.randint(100, 2000)),
        (30, "TARIFA PACOTE DE SERVIÇOS", -rng.randint(2500, 4500)),
    ]
    saldo = rng.randint(20000, 150000)

    colunas = [("Data", x0 + 10, "la"), ("Histórico", x0 + 130, "la"),
               ("Valor (R$)", x1 - 200, "ra"), ("Saldo (R$)", x1 - 10, "ra")]
    d.rectangle([x0, y, x1, y + 36], fill=clarear(azul, 0.85))
    for texto, x, anc in colunas:
        d.text((x, y + 9), texto, font=fonte("arial", 15, True), fill=azul, anchor=anc)
    y += 42
    d.text((x0 + 10, y), "01/09", font=fonte("arial", 15), fill=PRETO)
    d.text((x0 + 130, y), "SALDO ANTERIOR", font=fonte("arial", 15, True), fill=PRETO)
    d.text((x1 - 10, y), brl(saldo), font=fonte("arial", 15), fill=PRETO, anchor="ra")
    y += 32
    for n, (dia, historico, valor) in enumerate(lancamentos):
        saldo += valor
        if n % 2 == 0:
            d.rectangle([x0, y - 6, x1, y + 24], fill=(247, 248, 251))
        d.text((x0 + 10, y), f"{dia:02d}/09", font=fonte("arial", 15), fill=PRETO)
        d.text((x0 + 130, y), historico, font=fonte("arial", 15), fill=PRETO)
        d.text((x1 - 200, y), brl(valor), font=fonte("arial", 15),
               fill=(170, 30, 30) if valor < 0 else (20, 110, 40), anchor="ra")
        d.text((x1 - 10, y), brl(saldo), font=fonte("arial", 15), fill=PRETO, anchor="ra")
        y += 32
    d.line([x0, y, x1, y], fill=azul, width=2)
    d.text((x1 - 10, y + 12), f"Saldo final em 30/09/2026: R$ {brl(saldo)}",
           font=fonte("arial", 18, True), fill=PRETO, anchor="ra")
    y += 70
    d.text((x0, y), "Os lançamentos estão sujeitos a confirmação. Central de atendimento: 0800 000 0000.",
           font=fonte("arial", 13), fill=CINZA)
    return recortar(img, y + 20 + m)


# ---------------------------------------------------------------------------
# Degradações
# ---------------------------------------------------------------------------

def entortar(img, rng):
    """Foto levemente torta sobre uma mesa: 3 a 6 graus, ainda legível."""
    angulo = rng.uniform(3, 6) * rng.choice((-1, 1))
    mesa = (122, 116, 108)
    margem = 70
    base = Image.new("RGB", (img.width + 2 * margem, img.height + 2 * margem), mesa)
    sombra = Image.new("L", base.size, 0)
    ImageDraw.Draw(sombra).rectangle(
        [margem + 10, margem + 14, margem + img.width + 10, margem + img.height + 14], fill=140)
    base.paste((60, 56, 50), mask=sombra.filter(ImageFilter.GaussianBlur(14)))
    base.paste(img, (margem, margem))
    girada = base.rotate(angulo, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=mesa)
    return redimensionar(girada, LARGURA)


def desfocar(img):
    """Desfoque forte: o texto fica ilegível de verdade."""
    return img.filter(ImageFilter.GaussianBlur(9))


def icones_status(d, x_direita, y, cor):
    """Sinal, wi-fi e bateria, desenhados da direita para a esquerda."""
    x = x_direita
    d.rounded_rectangle([x - 50, y, x - 6, y + 22], radius=6, outline=cor, width=2)
    d.rectangle([x - 4, y + 7, x, y + 15], fill=cor)
    d.rounded_rectangle([x - 46, y + 4, x - 46 + 31, y + 18], radius=3, fill=cor)
    d.text((x - 60, y + 1), "78%", font=fonte("arial", 20, True), fill=cor, anchor="ra")
    x -= 120
    centro = (x, y + 22)
    for r in (22, 15, 8):
        d.arc([centro[0] - r, centro[1] - r, centro[0] + r, centro[1] + r], 225, 315, fill=cor, width=4)
    d.ellipse([centro[0] - 3, centro[1] - 3, centro[0] + 3, centro[1] + 3], fill=cor)
    x -= 70
    for i in range(4):
        altura = 7 + 5 * i
        d.rectangle([x + i * 9, y + 22 - altura, x + i * 9 + 5, y + 22], fill=cor)


def moldura_celular(img, rng):
    """Print de tela: moldura de celular, barra de status, cabeçalho de app."""
    fundo, borda, margem = (232, 232, 236), 26, 36
    largura_tela = LARGURA - 2 * margem - 2 * borda
    conteudo = redimensionar(img, largura_tela - 32)
    barra, cabecalho, rodape = 70, 120, 56
    altura_tela = barra + cabecalho + conteudo.height + 32 + rodape

    tela = Image.new("RGB", (largura_tela, altura_tela), (242, 242, 247))
    d = ImageDraw.Draw(tela)
    hora = f"{rng.randint(8, 21)}:{rng.randint(0, 59):02d}"
    d.text((44, 22), hora, font=fonte("arial", 22, True), fill=PRETO)
    d.rounded_rectangle([largura_tela / 2 - 90, 14, largura_tela / 2 + 90, 52], radius=19, fill=PRETO)
    icones_status(d, largura_tela - 30, 24, PRETO)

    azul = (0, 92, 175)
    d.rectangle([0, barra, largura_tela, barra + cabecalho], fill=azul)
    d.text((28, barra + 24), "‹", font=fonte("arial", 46), fill=BRANCO)
    d.text((70, barra + 26), "Meus holerites", font=fonte("arial", 28, True), fill=BRANCO)
    d.text((70, barra + 68), "Portal do Colaborador", font=fonte("arial", 18), fill=clarear(azul, 0.7))
    for i in range(3):  # menu "⋮" desenhado (a Arial não tem esse caractere)
        cy = barra + 44 + i * 14
        d.ellipse([largura_tela - 42, cy, largura_tela - 34, cy + 8], fill=BRANCO)

    tela.paste(conteudo, (16, barra + cabecalho + 16))
    d.rounded_rectangle([largura_tela / 2 - 80, altura_tela - 26, largura_tela / 2 + 80, altura_tela - 18],
                        radius=4, fill=PRETO)

    mascara = Image.new("L", tela.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle([0, 0, tela.width - 1, tela.height - 1], radius=56, fill=255)
    final = Image.new("RGB", (LARGURA, altura_tela + 2 * margem + 2 * borda), fundo)
    ImageDraw.Draw(final).rounded_rectangle(
        [margem, margem, LARGURA - margem, final.height - margem], radius=80, fill=(25, 25, 28))
    final.paste(tela, (margem + borda, margem + borda), mascara)
    return final


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------

def ler(nome_arquivo):
    with open(PASTA_DADOS / nome_arquivo, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def salvar(img, caminho):
    """Paleta reduzida + optimize: arquivo pequeno (os tokens dependem das dimensões, não dos bytes)."""
    img.convert("RGB").quantize(colors=CORES_PALETA, dither=Image.Dither.NONE).save(caminho, optimize=True)


def renderizar(doc, linhas_doc, salario_cliente):
    rng = random.Random(f"{SEMENTE}:{doc['file']}")
    if doc["true_type"] in ("other", "other_document"):
        img = conta_de_luz(doc, rng)
    elif doc["true_type"] == "bank_statement":
        img = extrato(doc, rng)
    else:
        h = montar_holerite(doc, linhas_doc, salario_cliente, rng)
        img = LAYOUTS[EMPRESAS[doc["employer"]]["layout"]](h)

    if doc["degradation"] == "skewed":
        img = entortar(img, rng)
    elif doc["degradation"] == "blurred":
        img = desfocar(img)
    elif doc["degradation"] == "screenshot":
        img = moldura_celular(img, rng)
    return img


AMOSTRA = ["A01", "A02", "A03", "A16", "N02", "N12", "N13", "N16"]


def escolher_para_amostra(docs_cliente):
    """O documento mais representativo do cenário: o degradado ou o com texto extra."""
    for doc in docs_cliente:
        if doc["degradation"] != "none" or doc["extra_text"]:
            return doc
    return docs_cliente[0]


def gerar_mosaico(documentos):
    por_cliente = defaultdict(list)
    for doc in documentos:
        por_cliente[doc["applicant_id"]].append(doc)
    caixa_l, caixa_a, espaco, rotulo = 400, 560, 20, 34
    colunas = 4
    linhas = (len(AMOSTRA) + colunas - 1) // colunas
    mosaico = Image.new("RGB", (colunas * caixa_l + (colunas + 1) * espaco,
                                linhas * (caixa_a + rotulo) + (linhas + 1) * espaco), (220, 220, 220))
    d = ImageDraw.Draw(mosaico)
    for i, cid in enumerate(AMOSTRA):
        doc = escolher_para_amostra(por_cliente[cid])
        miniatura = Image.open(PASTA_IMAGENS / doc["file"]).convert("RGB")
        miniatura.thumbnail((caixa_l, caixa_a), Image.Resampling.LANCZOS)
        x = espaco + (i % colunas) * (caixa_l + espaco)
        y = espaco + (i // colunas) * (caixa_a + rotulo + espaco)
        d.text((x, y), f"{cid} · {doc['file']}", font=fonte("arial", 18, True), fill=PRETO)
        mosaico.paste(miniatura, (x, y + rotulo))
    salvar(mosaico, PASTA_IMAGENS / ARQUIVO_AMOSTRA)


def main():
    documentos = ler("documents.csv")
    linhas = defaultdict(list)
    for linha in ler("line_items.csv"):
        linhas[linha["file"]].append(linha)
    salarios = salarios_contratuais(documentos, linhas)

    PASTA_IMAGENS.mkdir(parents=True, exist_ok=True)
    esperados = {doc["file"] for doc in documentos} | {ARQUIVO_AMOSTRA}
    antigos = [p for p in PASTA_IMAGENS.glob("*.png") if p.name not in esperados]
    for caminho in antigos:
        caminho.unlink()

    for doc in documentos:
        img = renderizar(doc, linhas[doc["file"]], salarios.get(doc["applicant_id"]))
        salvar(img, PASTA_IMAGENS / doc["file"])
    gerar_mosaico(documentos)

    pngs = sorted(PASTA_IMAGENS.glob("*.png"))
    total = sum(p.stat().st_size for p in pngs)
    print(f"{len(documentos)} imagens de documentos + {ARQUIVO_AMOSTRA} em {PASTA_IMAGENS}")
    print(f"Tamanho total da pasta: {total / 1024 / 1024:.1f} MB")
    if antigos:
        print(f"Removidas {len(antigos)} imagens que não estão mais em documents.csv")


if __name__ == "__main__":
    main()
