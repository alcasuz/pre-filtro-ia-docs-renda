"""Avalia a extração das fotos da base v2 contra o documento de origem.

Para cada foto de data/photos.csv, o gabarito são os valores do source_file em
data/documents.csv e data/line_items.csv. Compara com o cache
cache/photos_v2/<prompt>/<modelo>/ e grava evaluation/results/photos_v2_<modelo>.md.
Nenhuma chamada de API.

Regras de comparação (as mesmas de score_documents.py):
- textos exatamente como impressos; valores ao centavo;
- fraud_suspected: o esperado vem da coluna expected_fraud do photos.csv
  (injection ou edição); até o prompt v2, foto ou print de tela (pela coluna
  expected_capture_type) também era fraude;
- capture_type (v3 em diante): o esperado vem da coluna expected_capture_type;
  fica fora da acurácia, numa matriz própria;
- cut_fields: o certo é null; valor preenchido conta como erro e como inventado.
  Para earnings_lines.description, as linhas são casadas pelo valor e toda
  descrição preenchida conta como inventada;
- só fotos de holerite (payslip*) entram na acurácia por campo e nas linhas;
  fotos de outro tipo são avaliadas só pelo document_type;
- partial_fields: o modelo extrai o que aparece e o motor decide; o valor é
  mostrado, mas não conta como acerto, erro ou invenção;
- fotos com expected_legible = no ficam fora da acurácia, num bloco separado;
- label_leak = yes (o nome do arquivo aparece na foto) é reportado à parte.
O porteiro de legibilidade é o do motor (core/rules/legibility.py), com o número
de palavras de cache/ocr/confidence_v2.csv; a confiança média aparece só como
informação.

Erros de decisão são separados em dois grupos: reprovação recuperável de foto
legível (o motor pediu um novo envio com illegible ou incomplete_document, quando o esperado era outra coisa) e decisão final errada
(qualquer outro erro: aprovar, revisar ou reprovar pelo motivo errado).

Impacto na decisão: para cada foto, o documento de origem é trocado pela foto
no cliente dele (os demais documentos vêm do gabarito, como no modo oracle de
score_applicants.py, para isolar o efeito da foto) e o motor roda com
prior_legibility_failures = 0. Decisão esperada, derivada dos rótulos e na ordem
do motor: ilegível -> reject/illegible; cliente sem holerite -> o motivo do
gabarito (type_not_accepted); foto de tela -> reject/screen_capture; campo
obrigatório (pay_period ou um dos totais) cortado -> reject/incomplete_document;
nos demais casos, a decisão do cliente no ground_truth.csv. Se a foto tiver
expected_decision e expected_reason preenchidos no photos.csv, eles substituem
os dois últimos passos (campo cortado e gabarito). Uma segunda visão
repete tudo como se a captura fosse aceita (capture_type = photo_of_paper), para
medir a leitura sem a regra de captura mascarando o resto. Um campo cortado
inventado muda a decisão se, com esse campo como null, a decisão for outra.

Uso: .venv/bin/python evaluation/score_photos.py --model gemini-3.5-flash-lite
"""

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import config as configuracao  # noqa: E402
from core.engine import decidir  # noqa: E402
from core.inputs import documento_da_extracao  # noqa: E402
from core.models import CAPTURAS_DE_TELA  # noqa: E402
from core.ocr import carregar_palavras  # noqa: E402
from core.rules import legibility  # noqa: E402
from core.rules.completeness import CAMPOS_OBRIGATORIOS  # noqa: E402
from score_applicants import clientes, documentos_oracle  # noqa: E402
from score_documents import (CAMPOS_TEXTO, CAMPOS_VALOR, PROMPTS_PRINT_E_FRAUDE, TIPO_NO_EVAL,  # noqa: E402
                             casar_linhas, centavos, fmt, pct, percentil, tabela_captura, vazio_para_nulo)

PASTA_DADOS = RAIZ / "data"
PASTA_RESULTADOS = Path(__file__).resolve().parent / "results"
CAMPOS = ["document_type"] + CAMPOS_TEXTO + CAMPOS_VALOR + ["fraud_suspected"]
# Reprovações que pedem um novo envio (o cliente pode se recuperar sozinho).
RECUPERAVEIS = ("illegible", "incomplete_document")
VISOES = (("com_captura", "Regras atuais (foto de tela reprova)"),
          ("sem_captura", "Se a captura fosse aceita (capture_type = photo_of_paper)"))


def ler_csv(caminho):
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lista(texto):
    return [c for c in texto.split(";") if c and c != "none"]


def avaliar_foto(foto, doc, proventos, e, prompt):
    """Compara uma extração com o documento de origem, campo a campo e linha a linha."""
    cortados, parciais = set(lista(foto["cut_fields"])), set(lista(foto["partial_fields"]))
    campos, inventados = [], []
    if not doc["true_type"].startswith("payslip"):
        esperado = TIPO_NO_EVAL[doc["true_type"]]
        campos.append({"campo": "document_type", "esperado": esperado, "obtido": e["document_type"],
                       "ok": esperado == e["document_type"]})
        return {"campos": campos, "inventados": [], "linhas": [], "puladas": [], "extras": []}
    for campo in CAMPOS:
        if campo in parciais:
            campos.append({"campo": campo, "esperado": "(parcial)", "obtido": e[campo], "ok": None})
            continue
        if campo == "document_type":
            esperado, obtido = TIPO_NO_EVAL[doc["true_type"]], e[campo]
        elif campo == "fraud_suspected":
            esperado = foto["expected_fraud"] == "yes" or (
                prompt in PROMPTS_PRINT_E_FRAUDE and foto["expected_capture_type"] in CAPTURAS_DE_TELA)
            obtido = e[campo]
        elif campo in cortados:
            esperado, obtido = None, e[campo]
        elif campo in CAMPOS_VALOR:
            esperado, obtido = vazio_para_nulo(doc[campo]), e[campo]
        else:
            esperado, obtido = vazio_para_nulo(doc[campo]), e[campo]
        if campo in CAMPOS_VALOR:
            ok = centavos(esperado) == centavos(obtido)
        else:
            ok = esperado == obtido
        if campo in cortados and obtido is not None:
            inventados.append((campo, obtido))
        campos.append({"campo": campo, "esperado": esperado, "obtido": obtido, "ok": ok})

    descricao_cortada = "earnings_lines.description" in cortados
    if descricao_cortada:
        # Sem descrição visível, casa pelo valor; toda descrição preenchida foi inventada.
        livres, pares, puladas = list(e["earnings_lines"]), [], []
        for g in proventos:
            achada = next((x for x in livres if centavos(x["amount"]) == centavos(g["amount"])), None)
            if achada is None:
                puladas.append(g)
            else:
                livres.remove(achada)
                pares.append((g, achada))
        extras = livres
        inventados += [("earnings_lines.description", x["description"]) for _, x in pares if x["description"].strip()]
    else:
        pares, puladas, extras = casar_linhas(proventos, e["earnings_lines"])
    linhas = []
    for g, x in pares:
        linhas.append({"descricao": g["description"], "valor_ok": centavos(x["amount"]) == centavos(g["amount"]),
                       "conta_ok": x["counts_as_income"] == (g["counts_as_income"] == "yes"),
                       "descricao_ok": None if descricao_cortada else x["description"] == g["description"],
                       "obtido": x})
    return {"campos": campos, "inventados": inventados, "linhas": linhas, "puladas": puladas, "extras": extras}


def acerto(r):
    """(acertos, total) de campos pontuados + linhas (valor e counts_as_income)."""
    pontuados = [c for c in r["campos"] if c["ok"] is not None]
    a = sum(c["ok"] for c in pontuados) + sum(l["valor_ok"] and l["conta_ok"] for l in r["linhas"])
    t = len(pontuados) + len(r["linhas"]) + len(r["puladas"]) + len(r["extras"])
    return a, t


def avaliar(prompt, modelo):
    cfg = configuracao.carregar()
    # Fotos ainda sem rótulo (expected_legible vazio) ficam de fora até serem preenchidas.
    fotos = [f for f in ler_csv(PASTA_DADOS / "photos.csv") if f["expected_legible"]]
    docs = {d["file"]: d for d in ler_csv(PASTA_DADOS / "documents.csv")}
    proventos = defaultdict(list)
    for l in ler_csv(PASTA_DADOS / "line_items.csv"):
        if l["kind"] == "earning":
            proventos[l["file"]].append(l)
    pasta = RAIZ / "cache" / "photos_v2" / prompt / modelo
    ocr = {o["file"]: o for o in ler_csv(RAIZ / "cache" / "ocr" / "confidence_v2.csv")}
    log = ler_csv(pasta / "_log.csv") if (pasta / "_log.csv").exists() else []

    docs_oracle, _ = documentos_oracle(carregar_palavras())
    cadastro = clientes()
    gabarito = {g["applicant_id"]: g for g in ler_csv_bom(PASTA_DADOS / "ground_truth.csv")}

    resultados = []
    for foto in fotos:
        caminho = pasta / f"{foto['file']}.json"
        e = json.loads(caminho.read_text(encoding="utf-8"))["extraction"] if caminho.exists() else None
        r = {"foto": foto, "extracao": e, "ocr": ocr.get(foto["file"])}
        if e is not None and foto["expected_legible"] == "yes":
            r.update(avaliar_foto(foto, docs[foto["source_file"]], proventos[foto["source_file"]], e, prompt))
        if e is not None:
            doc = documento_da_extracao(foto["file"], e, palavras_ocr(r["ocr"]))
            r["porteiro"] = legibility.avaliar(doc, cfg)
            r["impacto"] = impacto(foto, e, r["ocr"], cfg, docs_oracle, cadastro, gabarito[foto["applicant_id"]],
                                   docs[foto["source_file"]], r.get("inventados", []))
        resultados.append(r)
    return {"prompt": prompt, "modelo": modelo,
            "resultados": resultados, "log": log}


def palavras_ocr(ocr):
    return int(ocr["words"]) if ocr else None


def classificar_erro(x, visao):
    """None se a decisão está certa; senão 'recuperavel' ou 'final'."""
    i = x["impacto"][visao]
    if i["esperada"] == i["obtida"]:
        return None
    if x["foto"]["expected_legible"] == "yes" and i["obtida"][1] in RECUPERAVEIS:
        return "recuperavel"
    return "final"


def ler_csv_bom(caminho):
    with open(caminho, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def decisao_esperada(foto, g, doc_origem, considerar_captura):
    if foto["expected_legible"] == "no":
        return "reject", "illegible"
    if g["expected_reason"] == "type_not_accepted":
        return "reject", "type_not_accepted"
    holerite = doc_origem["true_type"].startswith("payslip")
    if considerar_captura and holerite and foto["expected_capture_type"] in CAPTURAS_DE_TELA:
        return "reject", "screen_capture"
    # Rótulo explícito no photos.csv vale no lugar da derivação, depois das regras que vêm antes.
    if foto.get("expected_decision"):
        return foto["expected_decision"], foto.get("expected_reason") or None
    if holerite and set(lista(foto["cut_fields"])) & set(CAMPOS_OBRIGATORIOS):
        return "reject", "incomplete_document"
    return g["expected_decision"], g["expected_reason"] or None


def rodar_motor(foto, e, ocr, cfg, docs_oracle, cadastro, captura=None, anular=()):
    e = dict(e, **{c: None for c in anular})
    if captura:
        e["capture_type"] = captura
    doc = documento_da_extracao(foto["file"], e, palavras_ocr(ocr))
    cid = foto["applicant_id"]
    outros = [d for d in docs_oracle[cid] if d.file != foto["source_file"]]
    d = decidir(cadastro[cid], outros + [doc], cfg, prior_legibility_failures=0)
    return d.decision, d.main_reason


def impacto(foto, e, ocr, cfg, docs_oracle, cadastro, g, doc_origem, inventados):
    """Decisão do motor com a foto no lugar do documento de origem, nas duas visões."""
    visoes = {}
    for nome, captura in (("com_captura", None), ("sem_captura", "photo_of_paper")):
        obtida = rodar_motor(foto, e, ocr, cfg, docs_oracle, cadastro, captura)
        anular = [c for c, _ in inventados if c in CAMPOS_VALOR + CAMPOS_TEXTO]
        sem_invencao = rodar_motor(foto, e, ocr, cfg, docs_oracle, cadastro, captura, anular) if anular else obtida
        visoes[nome] = {"esperada": decisao_esperada(foto, g, doc_origem, captura is None), "obtida": obtida,
                        "sem_invencao": sem_invencao}
    return visoes


def tabela_por_grupo(avaliadas, chave):
    grupos = defaultdict(list)
    for r in avaliadas:
        grupos[chave(r)].append(r)
    linhas = []
    for nome in sorted(grupos):
        rs = grupos[nome]
        a = sum(acerto(r)[0] for r in rs)
        t = sum(acerto(r)[1] for r in rs)
        inv = sum(len(r["inventados"]) for r in rs)
        linhas.append(f"| {nome} | {len(rs)} | {pct(a, t)} | {inv} |")
    return ["| Grupo | Fotos | Campos e linhas certos | Inventados |", "|---|---|---|---|"] + linhas


def resumo(r):
    avaliadas = [x for x in r["resultados"] if "campos" in x]
    sem_extracao = [x["foto"]["file"] for x in r["resultados"] if x["extracao"] is None]
    a = sum(acerto(x)[0] for x in avaliadas)
    t = sum(acerto(x)[1] for x in avaliadas)
    limpas = [x for x in avaliadas if x["foto"]["label_leak"] == "no"]
    al, tl = sum(acerto(x)[0] for x in limpas), sum(acerto(x)[1] for x in limpas)
    inv = sum(len(x["inventados"]) for x in avaliadas)
    porteiro = [x for x in r["resultados"] if "porteiro" in x]
    fn = [f"{x['foto']['file']} ({x['porteiro'].reason})" for x in porteiro
          if x["foto"]["expected_legible"] == "yes" and x["porteiro"].status != "pass"]
    fp = [x["foto"]["file"] for x in porteiro if x["foto"]["expected_legible"] == "no"
          and x["porteiro"].status == "pass"]
    ok = [l for l in r["log"] if l["status"] == "ok"]
    lat = [float(l["latency_s"]) for l in ok]
    tokens = {k: sum(int(l[k]) for l in ok) / len(ok) for k in ("input_tokens", "output_tokens", "thought_tokens",
                                                                 "total_tokens")} if ok else {}
    linhas = [
        f"Fotos v2 | prompt {r['prompt']} | modelo {r['modelo']} | avaliadas (legíveis): {len(avaliadas)} "
        f"| ilegíveis à parte: {sum(1 for x in r['resultados'] if x['foto']['expected_legible'] == 'no')}",
        f"Campos e linhas certos: {pct(a, t)} | sem as fotos com nome do arquivo visível: {pct(al, tl)}",
        f"Campos cortados inventados: {inv}",
    ]
    capturas = [(x["foto"]["expected_capture_type"], x["extracao"].get("capture_type"))
                for x in r["resultados"] if x["extracao"]]
    if any(o for _, o in capturas):
        linhas.append("capture_type certo (todas as fotos, legíveis ou não): "
                      f"{pct(sum(e == o for e, o in capturas), len(capturas))}")
    linhas += [
        f"Porteiro de legibilidade: legíveis barradas (falso negativo): {len(fn)}"
        + (f" ({', '.join(fn)})" if fn else "")
        + f" | ilegíveis aprovadas: {len(fp)}" + (f" ({', '.join(fp)})" if fp else ""),
        f"API: {len(r['log'])} chamadas | erros: {pct(len(r['log']) - len(ok), len(r['log']))} | "
        f"latência p50 {fmt(percentil(lat, 50)) if lat else '—'} s, p90 {fmt(percentil(lat, 90)) if lat else '—'} s",
        "Tokens médios por foto: " + " | ".join(f"{k.replace('_tokens', '')} {v:.0f}" for k, v in tokens.items()),
    ]
    xs = [x for x in r["resultados"] if "impacto" in x]
    if xs:
        certas = {n: sum(x["impacto"][n]["esperada"] == x["impacto"][n]["obtida"] for x in xs)
                  for n in ("com_captura", "sem_captura")}
        muda = [x["foto"]["file"] for x in xs if x.get("inventados") and any(
            x["impacto"][n]["obtida"] != x["impacto"][n]["sem_invencao"] for n in ("com_captura", "sem_captura"))]
        for n, titulo in VISOES:
            erros = Counter(classificar_erro(x, n) for x in xs)
            linhas.append(f"Decisão do cliente com a foto, {titulo.lower()}: certas {pct(certas[n], len(xs))} | "
                          f"reprovações recuperáveis de foto legível: {erros['recuperavel']} | "
                          f"decisões finais erradas: {erros['final']}")
        linhas.append(f"Invenção que muda a decisão: {len(muda)}" + (f" ({', '.join(muda)})" if muda else ""))
    if sem_extracao:
        linhas.append(f"Fotos sem extração no cache: {', '.join(sem_extracao)}")
    return linhas


def relatorio(r):
    avaliadas = [x for x in r["resultados"] if "campos" in x]
    md = [f"# Avaliação das fotos (v2): {r['prompt']} · {r['modelo']}", "",
          "Gerado por `evaluation/score_photos.py` a partir do cache, sem chamadas à API. "
          "Gabarito: os valores do `source_file` de cada foto.", "",
          "## Resumo", "", "```", *resumo(r), "```", ""]

    md += ["## Por defeito", ""] + tabela_por_grupo(avaliadas, lambda x: x["foto"]["defect"]) + [""]
    md += ["## Por defeito e intensidade", ""] + tabela_por_grupo(
        avaliadas, lambda x: f"{x['foto']['defect']} · {x['foto']['severity'] or '—'}") + [""]
    md += ["## Por severidade", ""] + tabela_por_grupo(avaliadas, lambda x: x["foto"]["severity"]) + [""]
    md += ["## Nome do arquivo visível na foto (label_leak)", "",
           "Nessas fotos o modelo pode ler cliente e competência na barra do visualizador.", ""]
    md += tabela_por_grupo(avaliadas, lambda x: "com nome visível" if x["foto"]["label_leak"] == "yes"
                           else "sem nome visível") + [""]

    md += ["## Acurácia por campo", "", "| Campo | Certos |", "|---|---|"]
    for campo in CAMPOS:
        pontuados = [c for x in avaliadas for c in x["campos"] if c["campo"] == campo and c["ok"] is not None]
        md.append(f"| {campo} | {pct(sum(c['ok'] for c in pontuados), len(pontuados))} |")
    todas = [l for x in avaliadas for l in x["linhas"]]
    puladas = sum(len(x["puladas"]) for x in avaliadas)
    extras = sum(len(x["extras"]) for x in avaliadas)
    md += ["", f"Linhas de provento: {len(todas)} encontradas, {puladas} puladas, {extras} inventadas; "
               f"valor certo {pct(sum(l['valor_ok'] for l in todas), len(todas))}; "
               f"counts_as_income certo {pct(sum(l['conta_ok'] for l in todas), len(todas))}.", ""]

    md += ["## Foto a foto", ""]
    for x in avaliadas:
        f = x["foto"]
        a, t = acerto(x)
        md += [f"### {f['file']}", "",
               f"Defeito {f['defect']} ({f['severity']}) · nome do arquivo visível: {f['label_leak']} · "
               f"certos {a}/{t}", "", "| Campo | Gabarito | Extraído | |", "|---|---|---|---|"]
        for c in x["campos"]:
            marca = "parcial" if c["ok"] is None else ("✓" if c["ok"] else "✗")
            md.append(f"| {c['campo']} | {fmt(c['esperado'])} | {fmt(c['obtido'])} | {marca} |")
        for l in x["linhas"]:
            o = l["obtido"]
            md.append(f"| linha: {l['descricao']} | | {o['description']!r} {fmt(o['amount'])} "
                      f"conta={fmt(o['counts_as_income'])} | {'✓' if l['valor_ok'] and l['conta_ok'] else '✗'} |")
        for g in x["puladas"]:
            md.append(f"| linha pulada: {g['description']} | {g['amount']} | — | ✗ |")
        for o in x["extras"]:
            md.append(f"| linha inventada | — | {o['description']!r} {fmt(o['amount'])} | ✗ |")
        if x["inventados"]:
            md.append("")
            md.append("Inventados nos campos cortados: " + "; ".join(f"{c} = {fmt(v)}" for c, v in x["inventados"]))
        md.append("")

    capturas = Counter((x["foto"]["expected_capture_type"], x["extracao"].get("capture_type"))
                       for x in r["resultados"] if x["extracao"])
    if any(o for _, o in capturas):
        md += ["## Matriz de confusão do capture_type", "",
               "Todas as fotos extraídas, inclusive as ilegíveis. Linhas: expected_capture_type. Colunas: extraído.", ""]
        md += tabela_captura(capturas) + [""]
        alarmes = [x["foto"]["file"] for x in r["resultados"] if x["extracao"]
                   and x["foto"]["expected_capture_type"] == "photo_of_paper"
                   and x["extracao"].get("capture_type") in CAPTURAS_DE_TELA]
        papel = sum(1 for x in r["resultados"] if x["extracao"] and x["foto"]["expected_capture_type"] == "photo_of_paper")
        md += [f"**Alarme falso (foto do papel classificada como captura de tela, reprovaria por engano): "
               f"{len(alarmes)} de {papel} fotos do papel**" + (f": {', '.join(alarmes)}" if alarmes else "")
               + ("" if papel else " (a base ainda não tem foto do papel)"), ""]
        md += ["| Foto | Gabarito | Extraído |", "|---|---|---|"]
        md += [f"| {x['foto']['file']} | {x['foto']['expected_capture_type']} | {fmt(x['extracao'].get('capture_type'))} |"
               for x in r["resultados"] if x["extracao"]] + [""]

    md += ["## Fotos ilegíveis (fora da acurácia)", ""]
    for x in r["resultados"]:
        if x["foto"]["expected_legible"] == "no":
            md += [f"**{x['foto']['file']}**", "", "```json",
                   json.dumps(x["extracao"], ensure_ascii=False, indent=2), "```", ""]

    md += ["## Porteiro de legibilidade", "",
           "Ilegível se o OCR reconhece 0 palavras e o LLM não extrai nada, ou se o CPF tem dígitos inválidos. "
           "A confiança média do OCR é só informativa. "
           "⚠️ marca legível barrada pelo porteiro (falso negativo) ou ilegível aprovada.", "",
           "| Foto | Palavras OCR | Confiança OCR | Porteiro | Seu julgamento | LLM extraiu certo | |",
           "|---|---|---|---|---|---|---|"]
    sem_ocr = [x["foto"]["file"] for x in r["resultados"] if not x["ocr"]]
    for x in sorted((x for x in r["resultados"] if "porteiro" in x),
                    key=lambda x: palavras_ocr(x["ocr"]) if x["ocr"] else -1):
        conf = float(x["ocr"]["mean_confidence"]) if x["ocr"] else None
        p = x["porteiro"]
        passa = p.status == "pass"
        veredito = "legível" if passa else f"{p.reason} ({p.details['criterion']})"
        legivel = x["foto"]["expected_legible"] == "yes"
        if "campos" in x:
            a, t = acerto(x)
            llm = f"{a}/{t}" + (" (tudo)" if a == t else "")
        else:
            llm = "fora da acurácia"
        alerta = "⚠️" if passa != legivel else ""
        md.append(f"| {x['foto']['file']} | {x['ocr']['words'] if x['ocr'] else '—'} | {fmt(conf)} | "
                  f"{veredito} | {'legível' if legivel else 'ilegível'} | {llm} | {alerta} |")
    if sem_ocr:
        md += ["", "Sem OCR (rode `.venv/bin/python -m core.ocr --set v2`): " + ", ".join(sem_ocr)]

    com_inv = [x for x in avaliadas if x["inventados"]]
    md += ["", "## Campos cortados inventados e efeito na decisão", "",
           "Decisão do motor com a extração como veio e com os campos inventados como null. "
           "Com a regra de captura, toda foto de tela reprova antes; por isso a visão sem captura também aparece.", ""]
    if com_inv:
        md += ["| Foto | Inventados | Com captura: como veio → sem invenção | Sem captura: como veio → sem invenção | "
               "Muda a decisão? |", "|---|---|---|---|---|"]
        for x in com_inv:
            i = x["impacto"]
            muda = [n for n in ("com_captura", "sem_captura") if i[n]["obtida"] != i[n]["sem_invencao"]]
            md.append(f"| {x['foto']['file']} | " + "; ".join(f"{c} = {fmt(v)}" for c, v in x["inventados"]) + " | "
                      + " | ".join(f"{fmt_dec(i[n]['obtida'])} → {fmt_dec(i[n]['sem_invencao'])}"
                                   for n in ("com_captura", "sem_captura"))
                      + f" | {'sim (' + ', '.join(muda) + ')' if muda else 'não'} |")
    else:
        md.append("Nenhum.")

    md += ["", "## Impacto na decisão do cliente", "",
           "A foto substitui o documento de origem no cliente; os outros documentos vêm do gabarito.", ""]
    marcas = {None: "✓", "recuperavel": "✗ recuperável", "final": "✗ final"}
    for nome, titulo in VISOES:
        xs = [x for x in r["resultados"] if "impacto" in x]
        erros = Counter(classificar_erro(x, nome) for x in xs)
        md += [f"### {titulo}: {pct(erros[None], len(xs))} certas", "",
               f"- Reprovações recuperáveis de foto legível ({', '.join(RECUPERAVEIS)} quando o esperado era outro): "
               f"{erros['recuperavel']}",
               f"- Decisões finais erradas: {erros['final']}", "",
               "| Foto | Esperada | Motor | |", "|---|---|---|---|"]
        md += [f"| {x['foto']['file']} | {fmt_dec(x['impacto'][nome]['esperada'])} | "
               f"{fmt_dec(x['impacto'][nome]['obtida'])} | {marcas[classificar_erro(x, nome)]} |" for x in xs] + [""]
    return "\n".join(md) + "\n"


def fmt_dec(d):
    return f"{d[0]}/{d[1]}" if d[1] else d[0]


def main():
    parser = argparse.ArgumentParser(description="Avalia a extração das fotos da base v2.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt", default="extraction_v2")
    args = parser.parse_args()
    r = avaliar(args.prompt, args.model)
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    # O relatório do prompt v2 mantém o nome original; os outros levam a versão.
    sufixo = "" if args.prompt == "extraction_v2" else f"{args.prompt.removeprefix('extraction_')}_"
    destino = PASTA_RESULTADOS / f"photos_v2_{sufixo}{args.model}.md"
    destino.write_text(relatorio(r), encoding="utf-8")
    print("\n".join(resumo(r)))
    print(f"\nRelatório completo: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
