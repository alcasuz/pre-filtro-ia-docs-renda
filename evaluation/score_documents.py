"""Avalia as extrações em cache contra o gabarito, documento a documento.

Compara cache/<versão>/<modelo>/*.json com data/documents.csv e data/line_items.csv,
sem chamar API nenhuma, e grava o relatório em
evaluation/results/documents_<sufixo>_<modelo>.md
(ex.: extraction_v2 + gemini-3.8-flash -> documents_v2_gemini-3.8-flash.md).

Regras de comparação:
- textos: iguais exatamente como impressos (sem normalizar), porque o prompt
  pede a cópia literal; campo vazio no gabarito equivale a null;
- valores: iguais ao centavo (R$ 0,01);
- document_type: até o prompt v3, bank_statement e other_document contam como
  "other" (o único tipo não aceito que o LLM devolvia); do v4 em diante, cada tipo
  é comparado com ele mesmo;
- fraud_suspected: o esperado é true quando extra_text está preenchido; até o
  prompt v2, também quando degradation = screenshot (no v3, print não é fraude);
- capture_type (prompt v3 em diante): o esperado vem da degradation
  (screenshot -> screenshot; skewed e blurred, fotos simuladas -> photo_of_paper;
  none -> original_file); fica fora da acurácia por campo, numa matriz própria;
- só holerites (payslip*) entram na acurácia por campo, nas linhas, na fraude e
  no capture_type; documentos de outro tipo são avaliados só pelo document_type;
- documentos com degradation = blurred ficam fora de todas as métricas de
  extração e aparecem num bloco separado; a ilegibilidade é decidida pelo OCR
  (R7), não pelo LLM.
Latência, taxa de erro e tokens vêm de cache/<versão>/<modelo>/_log.csv.

Uso: .venv/bin/python evaluation/score_documents.py [--prompt extraction_v2] [--model gemini-3.8-flash]
"""

import argparse
import csv
import json
import math
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "data"
PASTA_RESULTADOS = Path(__file__).resolve().parent / "results"

TIPOS_ATE_V3 = ["payslip", "payslip_vacation", "payslip_13th", "other"]
TIPOS_V4 = ["payslip", "payslip_vacation", "payslip_13th", "bank_statement", "tax_return", "inss_benefit",
            "other_document", "unidentified"]
PROMPTS_TIPO_OTHER = {"extraction_v1", "extraction_v2", "extraction_v3"}


def tipos(versao):
    return TIPOS_ATE_V3 if versao in PROMPTS_TIPO_OTHER else TIPOS_V4


def tipo_esperado(true_type, versao):
    """Tipo que o LLM deveria devolver para o true_type do gabarito, na versão do prompt."""
    if versao in PROMPTS_TIPO_OTHER and not true_type.startswith("payslip"):
        return "other"
    return true_type
CAMPOS_TEXTO = ["pay_period", "name_on_doc", "cpf_on_doc"]
CAMPOS_VALOR = ["total_earnings", "total_deductions", "net_pay"]
TIPOS_CAPTURA = ["original_file", "photo_of_paper", "photo_of_screen", "screenshot"]
CAPTURA_POR_DEGRADACAO = {"screenshot": "screenshot", "skewed": "photo_of_paper", "blurred": "photo_of_paper"}
# Até o v2, o prompt pedia fraud_suspected também para print de tela.
PROMPTS_PRINT_E_FRAUDE = {"extraction_v1", "extraction_v2"}


def captura_esperada(doc):
    return CAPTURA_POR_DEGRADACAO.get(doc["degradation"], "original_file")


def fraude_esperada(doc, versao):
    return bool(doc["extra_text"]) or (versao in PROMPTS_PRINT_E_FRAUDE and doc["degradation"] == "screenshot")


def tabela_captura(matriz):
    """Matriz de confusão do capture_type em markdown; matriz é um Counter de (esperado, obtido)."""
    obtidos = TIPOS_CAPTURA + sorted({o for _, o in matriz} - set(TIPOS_CAPTURA))
    md = ["| ground truth \\ extracted | " + " | ".join(map(str, obtidos)) + " |", "|---" * (len(obtidos) + 1) + "|"]
    for esperado in TIPOS_CAPTURA:
        if any(e == esperado for e, _ in matriz):
            md.append(f"| {esperado} | " + " | ".join(str(matriz[(esperado, o)]) for o in obtidos) + " |")
    return md


def ler_csv(caminho):
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def centavos(valor):
    """Número ou texto -> centavos inteiros; None se vazio."""
    if valor is None or valor == "":
        return None
    return round(float(valor) * 100)


def vazio_para_nulo(texto):
    return texto if texto != "" else None


def normalizar(texto):
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))
    return " ".join(sem_acento.upper().split())


def percentil(valores, p):
    """Percentil pelo método do posto mais próximo (nearest rank)."""
    ordenados = sorted(valores)
    posto = max(1, math.ceil(p / 100 * len(ordenados)))
    return ordenados[posto - 1]


def pct(acertos, total):
    return f"{acertos}/{total} ({100 * acertos / total:.1f}%)" if total else "—"


def fmt(valor):
    if valor is None:
        return "null"
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, float):
        return f"{valor:.2f}"
    return str(valor)


def casar_linhas(gabarito, extraidas):
    """Casa as linhas de provento: primeiro pela descrição normalizada, depois pelo valor.

    Devolve (pares, puladas, inventadas).
    """
    livres = list(extraidas)
    pares, puladas = [], []
    pendentes = []
    for g in gabarito:
        alvo = normalizar(g["description"])
        achada = next((e for e in livres if normalizar(e["description"]) == alvo), None)
        if achada is not None:
            livres.remove(achada)
            pares.append((g, achada))
        else:
            pendentes.append(g)
    for g in pendentes:
        achada = next((e for e in livres if centavos(e["amount"]) == centavos(g["amount"])), None)
        if achada is not None:
            livres.remove(achada)
            pares.append((g, achada))
        else:
            puladas.append(g)
    return pares, puladas, livres


def avaliar(versao, modelo):
    documentos = ler_csv(PASTA_DADOS / "documents.csv")
    proventos = defaultdict(list)
    for linha in ler_csv(PASTA_DADOS / "line_items.csv"):
        if linha["kind"] == "earning":
            proventos[linha["file"]].append(linha)

    pasta_cache = RAIZ / "cache" / versao / modelo
    extracoes = {}
    for doc in documentos:
        caminho = pasta_cache / f"{doc['file']}.json"
        if caminho.exists():
            extracoes[doc["file"]] = json.loads(caminho.read_text(encoding="utf-8"))["extraction"]

    avaliados = [d for d in documentos if d["file"] in extracoes and d["degradation"] != "blurred"]
    desfocados = [d for d in documentos if d["file"] in extracoes and d["degradation"] == "blurred"]
    sem_extracao = [d["file"] for d in documentos if d["file"] not in extracoes]

    holerites = [d for d in avaliados if d["true_type"].startswith("payslip")]
    r = {"versao": versao, "modelo": modelo, "total_docs": len(documentos), "avaliados": len(avaliados),
         "holerites": len(holerites),
         "desfocados": desfocados, "sem_extracao": sem_extracao, "extracoes": extracoes}

    # Acurácia por campo e campos inventados
    acertos, erros, inventados = Counter(), defaultdict(list), defaultdict(list)
    matriz = Counter()
    for doc in avaliados:
        e = extracoes[doc["file"]]
        esperado_tipo = tipo_esperado(doc["true_type"], versao)
        matriz[(esperado_tipo, e["document_type"])] += 1
        if e["document_type"] == esperado_tipo:
            acertos["document_type"] += 1
        else:
            erros["document_type"].append((doc["file"], esperado_tipo, e["document_type"]))
        if doc not in holerites:
            continue  # outro tipo: avaliado só pelo document_type
        for campo in CAMPOS_TEXTO + CAMPOS_VALOR:
            if campo in CAMPOS_VALOR:
                esperado, obtido = centavos(doc[campo]), centavos(e[campo])
                mostrar = (vazio_para_nulo(doc[campo]), e[campo])
            else:
                esperado, obtido = vazio_para_nulo(doc[campo]), e[campo]
                mostrar = (esperado, obtido)
            if esperado == obtido:
                acertos[campo] += 1
            else:
                erros[campo].append((doc["file"], *mostrar))
            if esperado is None and obtido is not None:
                inventados[campo].append((doc["file"], obtido))
    r.update(acertos=acertos, erros=erros, inventados=inventados, matriz=matriz)

    # Linhas de provento (só documentos do tipo holerite)
    total_gab = casadas = conta_ok = valor_ok = descricao_exata = 0
    puladas, inventadas, conta_erradas, valor_errado = [], [], [], []
    for doc in holerites:
        e = extracoes[doc["file"]]
        pares, pul, inv = casar_linhas(proventos[doc["file"]], e["earnings_lines"])
        total_gab += len(proventos[doc["file"]])
        casadas += len(pares)
        puladas += [(doc["file"], g["description"], g["amount"]) for g in pul]
        inventadas += [(doc["file"], x["description"], x["amount"]) for x in inv]
        for g, x in pares:
            esperado = g["counts_as_income"] == "yes"
            if x["counts_as_income"] == esperado:
                conta_ok += 1
            else:
                conta_erradas.append((doc["file"], g["description"], esperado, x["counts_as_income"]))
            if centavos(x["amount"]) == centavos(g["amount"]):
                valor_ok += 1
            else:
                valor_errado.append((doc["file"], g["description"], g["amount"], x["amount"]))
            descricao_exata += x["description"] == g["description"]
    r["linhas"] = {"total_gab": total_gab, "casadas": casadas, "conta_ok": conta_ok,
                   "valor_ok": valor_ok, "descricao_exata": descricao_exata, "puladas": puladas,
                   "inventadas": inventadas, "conta_erradas": conta_erradas, "valor_errado": valor_errado}

    # Fraude
    fraude = {"acertos": 0, "alarmes_falsos": [], "nao_detectadas": [], "detectadas": [], "total": 0}
    for doc in holerites:
        e = extracoes[doc["file"]]
        esperado = fraude_esperada(doc, versao)
        fraude["total"] += 1
        if e["fraud_suspected"] == esperado:
            fraude["acertos"] += 1
            if esperado:
                fraude["detectadas"].append((doc["file"], e["fraud_reason"]))
        elif e["fraud_suspected"]:
            fraude["alarmes_falsos"].append((doc["file"], e["fraud_reason"]))
        else:
            fraude["nao_detectadas"].append(doc["file"])
    r["fraude"] = fraude

    # Tipo de captura (prompt v3 em diante)
    captura = Counter((captura_esperada(doc), extracoes[doc["file"]].get("capture_type")) for doc in holerites)
    r["captura"] = captura if any(o is not None for _, o in captura) else None
    r["erros_captura"] = [(doc["file"], captura_esperada(doc), extracoes[doc["file"]].get("capture_type"))
                          for doc in holerites if captura_esperada(doc) != extracoes[doc["file"]].get("capture_type")]

    # Latência, erros e tokens (log da API)
    log_path = pasta_cache / "_log.csv"
    log = ler_csv(log_path) if log_path.exists() else []
    ok = [l for l in log if l["status"] == "ok"]
    latencias = [float(l["latency_s"]) for l in ok]
    r["api"] = {
        "chamadas": len(log),
        "status": Counter(l["status"] for l in log),
        "p50": percentil(latencias, 50) if latencias else None,
        "p90": percentil(latencias, 90) if latencias else None,
        "tokens": {campo: sum(int(l[campo]) for l in ok) / len(ok) if ok else None
                   for campo in ("input_tokens", "output_tokens", "thought_tokens", "total_tokens")},
    }
    return r


def linhas_resumo(r):
    a = r["api"]
    erros_api = a["chamadas"] - a["status"]["ok"]
    linhas = [
        f"Prompt: {r['versao']} | model: {r['modelo']} | documents extracted: {len(r['extracoes'])}/{r['total_docs']}"
        f" | scored (blurred excluded): {r['avaliados']}, of which pay stubs: {r['holerites']}",
        "",
        "Accuracy per field:",
    ]
    for campo in ["document_type"] + CAMPOS_TEXTO + CAMPOS_VALOR:
        base = r["avaliados"] if campo == "document_type" else r["holerites"]
        linhas.append(f"  {campo:18} {pct(r['acertos'][campo], base)}")
    l = r["linhas"]
    linhas += [
        "",
        f"Earnings lines: {l['casadas']}/{l['total_gab']} found | "
        f"counts_as_income right: {pct(l['conta_ok'], l['casadas'])} | amount right: {pct(l['valor_ok'], l['casadas'])}",
        f"  skipped by the model: {len(l['puladas'])} | invented: {len(l['inventadas'])}",
        f"Invented fields (filled where the ground truth is empty): "
        f"{sum(len(v) for v in r['inventados'].values())}",
        f"Fraud: {pct(r['fraude']['acertos'], r['fraude']['total'])} right | "
        f"detected: {len(r['fraude']['detectadas'])} | false alarms: {len(r['fraude']['alarmes_falsos'])} | "
        f"missed: {len(r['fraude']['nao_detectadas'])}",
    ]
    if r["captura"]:
        certos = sum(n for (e, o), n in r["captura"].items() if e == o)
        linhas.append(f"capture_type: {pct(certos, sum(r['captura'].values()))} right")
    linhas += [
        "",
        f"API: {a['chamadas']} calls | error rate: {pct(erros_api, a['chamadas'])} "
        f"({', '.join(f'{k}: {v}' for k, v in sorted(a['status'].items()))})",
        f"Latency: p50 {fmt(a['p50'])} s | p90 {fmt(a['p90'])} s",
        "Average tokens per document: " + " | ".join(
            f"{k.replace('_tokens', '')} {v:.0f}" for k, v in a["tokens"].items() if v is not None),
    ]
    if r["sem_extracao"]:
        linhas.append(f"Not extracted in the cache: {len(r['sem_extracao'])} documents")
    return linhas


def relatorio_md(r):
    md = [f"# Document-level evaluation: {r['versao']} · {r['modelo']}", "",
          "Generated by `evaluation/score_documents.py` from the cache, with no API calls.", "",
          "## Summary", "", "```", *linhas_resumo(r), "```", ""]

    md += ["## Accuracy per field", "",
           f"Base: document_type on {r['avaliados']} documents (blurred excluded); the other fields only on the "
           f"{r['holerites']} pay stubs. Text compared exactly as printed; "
           "amounts to the cent.", "", "| Field | Right | Errors |", "|---|---|---|"]
    for campo in ["document_type"] + CAMPOS_TEXTO + CAMPOS_VALOR:
        base = r["avaliados"] if campo == "document_type" else r["holerites"]
        md.append(f"| {campo} | {pct(r['acertos'][campo], base)} | {len(r['erros'][campo])} |")
    md.append("")
    for campo in ["document_type"] + CAMPOS_TEXTO + CAMPOS_VALOR:
        if r["erros"][campo]:
            md += [f"**Errors in `{campo}`**", "", "| File | Ground truth | Extracted |", "|---|---|---|"]
            md += [f"| {f} | {fmt(g)} | {fmt(x)} |" for f, g, x in r["erros"][campo]]
            md.append("")

    md += ["## document_type confusion matrix", "",
           "Rows: ground truth" + (" (bank_statement and other_document counted as other)"
                                  if r["versao"] in PROMPTS_TIPO_OTHER else "")
           + ". Columns: extracted. Blurred excluded.", "",
           "| ground truth \\ extracted | " + " | ".join(tipos(r["versao"])) + " |",
           "|---" * (len(tipos(r["versao"])) + 1) + "|"]
    for esperado in tipos(r["versao"]):
        md.append(f"| {esperado} | " + " | ".join(str(r["matriz"][(esperado, t)]) for t in tipos(r["versao"])) + " |")
    md.append("")

    l = r["linhas"]
    md += ["## Earnings lines", "",
           "Matched by description (ignoring accents, case and spaces) and, failing that, by amount.", "",
           f"- Ground truth lines: {l['total_gab']}; found: {l['casadas']}",
           f"- counts_as_income right: {pct(l['conta_ok'], l['casadas'])}",
           f"- Amount right: {pct(l['valor_ok'], l['casadas'])}",
           f"- Description copied exactly: {pct(l['descricao_exata'], l['casadas'])}",
           f"- Skipped by the model: {len(l['puladas'])}; invented: {len(l['inventadas'])}", ""]
    for titulo, itens, cab in (
        ("Wrong counts_as_income", l["conta_erradas"], "| File | Line | Expected | Extracted |"),
        ("Wrong amount", l["valor_errado"], "| File | Line | Ground truth | Extracted |"),
        ("Skipped lines", l["puladas"], "| File | Line | Amount |"),
        ("Invented lines", l["inventadas"], "| File | Line | Amount |"),
    ):
        if itens:
            md += [f"**{titulo}**", "", cab, "|---" * (cab.count("|") - 1) + "|"]
            md += ["| " + " | ".join(fmt(c) for c in item) + " |" for item in itens]
            md.append("")

    md += ["## Invented fields", "", "Value filled in where the ground truth is empty.", ""]
    if any(r["inventados"].values()):
        md += ["| Field | File | Extracted value |", "|---|---|---|"]
        for campo, itens in r["inventados"].items():
            md += [f"| {campo} | {f} | {fmt(v)} |" for f, v in itens]
    else:
        md.append("None.")
    md.append("")

    f = r["fraude"]
    md += ["## Suspected fraud", "",
           "Expected true when extra_text is filled in"
           + (" or degradation = screenshot." if r["versao"] in PROMPTS_PRINT_E_FRAUDE
              else " (from v3 on, a screenshot is not fraud)."), "",
           f"- Right: {pct(f['acertos'], f['total'])}",
           f"- Fraud detected: {len(f['detectadas'])}",
           f"- False alarms: {len(f['alarmes_falsos'])}",
           f"- Fraud missed: {len(f['nao_detectadas'])}", ""]
    for titulo, itens in (("Detected", f["detectadas"]), ("False alarms", f["alarmes_falsos"])):
        if itens:
            md += [f"**{titulo}**", "", "| File | fraud_reason |", "|---|---|"]
            md += [f"| {arq} | {fmt(motivo)} |" for arq, motivo in itens]
            md.append("")
    if f["nao_detectadas"]:
        md += ["**Missed:** " + ", ".join(f["nao_detectadas"]), ""]

    if r["captura"]:
        md += ["## capture_type confusion matrix", "",
               "Rows: ground truth (from degradation: screenshot -> screenshot; skewed and blurred -> photo_of_paper; "
               "none -> original_file). Columns: extracted.", ""] + tabela_captura(r["captura"]) + [""]
        if r["erros_captura"]:
            md += ["**Errors in `capture_type`**", "", "| File | Ground truth | Extracted |", "|---|---|---|"]
            md += [f"| {f} | {g} | {fmt(x)} |" for f, g, x in r["erros_captura"]]
            md.append("")

    md += ["## Blurred documents (excluded from the metrics)", "",
           "The ground truth of these documents is not readable; the legibility decision belongs to the gate (R7). "
           "This only records what the model returned: ideally null fields and no invented values.", ""]
    for doc in r["desfocados"]:
        e = r["extracoes"][doc["file"]]
        md += [f"**{doc['file']}**", "", "```json", json.dumps(e, ensure_ascii=False, indent=2), "```", ""]
    if not r["desfocados"]:
        md += ["No blurred document extracted.", ""]

    a = r["api"]
    md += ["## API: latency, errors and tokens", "",
           f"- Calls logged: {a['chamadas']}",
           "- By status: " + ", ".join(f"{k}: {v}" for k, v in sorted(a["status"].items())),
           f"- Latency (successful calls): p50 {fmt(a['p50'])} s; p90 {fmt(a['p90'])} s",
           "- Average tokens per document: " + "; ".join(
               f"{k} {v:.0f}" for k, v in a["tokens"].items() if v is not None), ""]
    if r["sem_extracao"]:
        md += ["## Documents not extracted in the cache", "", ", ".join(r["sem_extracao"]), ""]
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Avalia as extrações em cache contra o gabarito.")
    parser.add_argument("--prompt", default="extraction_v2", help="versão do prompt, ex.: extraction_v2")
    parser.add_argument("--model", default="gemini-3.8-flash", help="modelo usado na extração")
    args = parser.parse_args()

    r = avaliar(args.prompt, args.model)
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    sufixo = args.prompt.removeprefix("extraction_")
    destino = PASTA_RESULTADOS / f"documents_{sufixo}_{args.model}.md"
    destino.write_text(relatorio_md(r), encoding="utf-8")
    print("\n".join(linhas_resumo(r)))
    print(f"\nFull report: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
