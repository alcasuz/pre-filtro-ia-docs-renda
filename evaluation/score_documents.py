"""Avalia as extrações em cache contra o gabarito, documento a documento.

Compara cache/<versão>/<modelo>/*.json com data/documents.csv e data/line_items.csv,
sem chamar API nenhuma, e grava o relatório em
evaluation/results/documents_<sufixo>_<modelo>.md
(ex.: extraction_v2 + gemini-3.8-flash -> documents_v2_gemini-3.8-flash.md).

Regras de comparação:
- textos: iguais exatamente como impressos (sem normalizar), porque o prompt
  pede a cópia literal; campo vazio no gabarito equivale a null;
- valores: iguais ao centavo (R$ 0,01);
- document_type: bank_statement e other contam como "other" (tipos da R1);
- fraud_suspected: o esperado é true só quando degradation = screenshot ou
  extra_text está preenchido;
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

TIPOS = ["payslip", "payslip_vacation", "payslip_13th", "other"]
TIPO_NO_EVAL = {"payslip": "payslip", "payslip_vacation": "payslip_vacation",
                "payslip_13th": "payslip_13th", "bank_statement": "other", "other": "other"}
CAMPOS_TEXTO = ["pay_period", "name_on_doc", "cpf_on_doc"]
CAMPOS_VALOR = ["total_earnings", "total_deductions", "net_pay"]


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

    r = {"versao": versao, "modelo": modelo, "total_docs": len(documentos), "avaliados": len(avaliados),
         "desfocados": desfocados, "sem_extracao": sem_extracao, "extracoes": extracoes}

    # Acurácia por campo e campos inventados
    acertos, erros, inventados = Counter(), defaultdict(list), defaultdict(list)
    matriz = Counter()
    for doc in avaliados:
        e = extracoes[doc["file"]]
        esperado_tipo = TIPO_NO_EVAL[doc["true_type"]]
        matriz[(esperado_tipo, e["document_type"])] += 1
        if e["document_type"] == esperado_tipo:
            acertos["document_type"] += 1
        else:
            erros["document_type"].append((doc["file"], esperado_tipo, e["document_type"]))
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
    for doc in avaliados:
        if not doc["true_type"].startswith("payslip"):
            continue
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
    for doc in avaliados:
        e = extracoes[doc["file"]]
        esperado = doc["degradation"] == "screenshot" or bool(doc["extra_text"])
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
        f"Prompt: {r['versao']} | modelo: {r['modelo']} | documentos extraídos: {len(r['extracoes'])}/{r['total_docs']}"
        f" | avaliados (sem os desfocados): {r['avaliados']}",
        "",
        "Acurácia por campo:",
    ]
    for campo in ["document_type"] + CAMPOS_TEXTO + CAMPOS_VALOR:
        linhas.append(f"  {campo:18} {pct(r['acertos'][campo], r['avaliados'])}")
    l = r["linhas"]
    linhas += [
        "",
        f"Linhas de provento: {l['casadas']}/{l['total_gab']} encontradas | "
        f"counts_as_income certo: {pct(l['conta_ok'], l['casadas'])} | valor certo: {pct(l['valor_ok'], l['casadas'])}",
        f"  puladas pelo modelo: {len(l['puladas'])} | inventadas: {len(l['inventadas'])}",
        f"Campos inventados (preenchidos onde o gabarito é vazio): "
        f"{sum(len(v) for v in r['inventados'].values())}",
        f"Fraude: {pct(r['fraude']['acertos'], r['fraude']['total'])} certos | "
        f"detectadas: {len(r['fraude']['detectadas'])} | alarmes falsos: {len(r['fraude']['alarmes_falsos'])} | "
        f"não detectadas: {len(r['fraude']['nao_detectadas'])}",
        "",
        f"API: {a['chamadas']} chamadas | taxa de erro: {pct(erros_api, a['chamadas'])} "
        f"({', '.join(f'{k}: {v}' for k, v in sorted(a['status'].items()))})",
        f"Latência: p50 {fmt(a['p50'])} s | p90 {fmt(a['p90'])} s",
        "Tokens médios por documento: " + " | ".join(
            f"{k.replace('_tokens', '')} {v:.0f}" for k, v in a["tokens"].items() if v is not None),
    ]
    if r["sem_extracao"]:
        linhas.append(f"Sem extração no cache: {len(r['sem_extracao'])} documentos")
    return linhas


def relatorio_md(r):
    md = [f"# Avaliação por documento: {r['versao']} · {r['modelo']}", "",
          "Gerado por `evaluation/score_documents.py` a partir do cache, sem chamadas à API.", "",
          "## Resumo", "", "```", *linhas_resumo(r), "```", ""]

    md += ["## Acurácia por campo", "",
           f"Base: {r['avaliados']} documentos (desfocados fora). Textos comparados exatamente como impressos; "
           "valores ao centavo.", "", "| Campo | Acertos | Erros |", "|---|---|---|"]
    for campo in ["document_type"] + CAMPOS_TEXTO + CAMPOS_VALOR:
        md.append(f"| {campo} | {pct(r['acertos'][campo], r['avaliados'])} | {len(r['erros'][campo])} |")
    md.append("")
    for campo in ["document_type"] + CAMPOS_TEXTO + CAMPOS_VALOR:
        if r["erros"][campo]:
            md += [f"**Erros em `{campo}`**", "", "| Arquivo | Gabarito | Extraído |", "|---|---|---|"]
            md += [f"| {f} | {fmt(g)} | {fmt(x)} |" for f, g, x in r["erros"][campo]]
            md.append("")

    md += ["## Matriz de confusão do document_type", "",
           "Linhas: gabarito (bank_statement contado como other). Colunas: extraído.", "",
           "| gabarito \\ extraído | " + " | ".join(TIPOS) + " |", "|---" * (len(TIPOS) + 1) + "|"]
    for esperado in TIPOS:
        md.append(f"| {esperado} | " + " | ".join(str(r["matriz"][(esperado, t)]) for t in TIPOS) + " |")
    md.append("")

    l = r["linhas"]
    md += ["## Linhas de provento", "",
           "Casamento por descrição (sem acentos, maiúsculas e espaços) e, se não houver, pelo valor.", "",
           f"- Linhas do gabarito: {l['total_gab']}; encontradas: {l['casadas']}",
           f"- counts_as_income certo: {pct(l['conta_ok'], l['casadas'])}",
           f"- Valor certo: {pct(l['valor_ok'], l['casadas'])}",
           f"- Descrição copiada exatamente: {pct(l['descricao_exata'], l['casadas'])}",
           f"- Puladas pelo modelo: {len(l['puladas'])}; inventadas: {len(l['inventadas'])}", ""]
    for titulo, itens, cab in (
        ("counts_as_income errado", l["conta_erradas"], "| Arquivo | Linha | Esperado | Extraído |"),
        ("Valor errado", l["valor_errado"], "| Arquivo | Linha | Gabarito | Extraído |"),
        ("Linhas puladas", l["puladas"], "| Arquivo | Linha | Valor |"),
        ("Linhas inventadas", l["inventadas"], "| Arquivo | Linha | Valor |"),
    ):
        if itens:
            md += [f"**{titulo}**", "", cab, "|---" * (cab.count("|") - 1) + "|"]
            md += ["| " + " | ".join(fmt(c) for c in item) + " |" for item in itens]
            md.append("")

    md += ["## Campos inventados", "", "Valor preenchido onde o gabarito é vazio.", ""]
    if any(r["inventados"].values()):
        md += ["| Campo | Arquivo | Valor extraído |", "|---|---|---|"]
        for campo, itens in r["inventados"].items():
            md += [f"| {campo} | {f} | {fmt(v)} |" for f, v in itens]
    else:
        md.append("Nenhum.")
    md.append("")

    f = r["fraude"]
    md += ["## Suspeita de fraude", "",
           "Esperado true só quando degradation = screenshot ou extra_text está preenchido.", "",
           f"- Acertos: {pct(f['acertos'], f['total'])}",
           f"- Fraudes detectadas: {len(f['detectadas'])}",
           f"- Alarmes falsos: {len(f['alarmes_falsos'])}",
           f"- Fraudes não detectadas: {len(f['nao_detectadas'])}", ""]
    for titulo, itens in (("Detectadas", f["detectadas"]), ("Alarmes falsos", f["alarmes_falsos"])):
        if itens:
            md += [f"**{titulo}**", "", "| Arquivo | fraud_reason |", "|---|---|"]
            md += [f"| {arq} | {fmt(motivo)} |" for arq, motivo in itens]
            md.append("")
    if f["nao_detectadas"]:
        md += ["**Não detectadas:** " + ", ".join(f["nao_detectadas"]), ""]

    md += ["## Documentos desfocados (fora das métricas)", "",
           "O gabarito desses documentos não é legível; a decisão de ilegibilidade é do OCR (R7). "
           "Aqui só se registra o que o modelo devolveu: o ideal é null nos campos, sem valores inventados.", ""]
    for doc in r["desfocados"]:
        e = r["extracoes"][doc["file"]]
        md += [f"**{doc['file']}**", "", "```json", json.dumps(e, ensure_ascii=False, indent=2), "```", ""]
    if not r["desfocados"]:
        md += ["Nenhum documento desfocado extraído.", ""]

    a = r["api"]
    md += ["## API: latência, erros e tokens", "",
           f"- Chamadas registradas: {a['chamadas']}",
           "- Por status: " + ", ".join(f"{k}: {v}" for k, v in sorted(a["status"].items())),
           f"- Latência (chamadas com sucesso): p50 {fmt(a['p50'])} s; p90 {fmt(a['p90'])} s",
           "- Tokens médios por documento: " + "; ".join(
               f"{k} {v:.0f}" for k, v in a["tokens"].items() if v is not None), ""]
    if r["sem_extracao"]:
        md += ["## Documentos sem extração no cache", "", ", ".join(r["sem_extracao"]), ""]
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
    print(f"\nRelatório completo: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
