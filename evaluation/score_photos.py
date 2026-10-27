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
- partial_fields: o modelo extrai o que aparece e o motor decide; o valor é
  mostrado, mas não conta como acerto, erro ou invenção;
- fotos com expected_legible = no ficam fora da acurácia, num bloco separado;
- label_leak = yes (o nome do arquivo aparece na foto) é reportado à parte.
O porteiro de legibilidade usa cache/ocr/confidence_v2.csv e o limite de
config/default_rules.yaml, sem alterar nada no motor.

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
from core.models import CAPTURAS_DE_TELA  # noqa: E402
from score_documents import (CAMPOS_TEXTO, CAMPOS_VALOR, PROMPTS_PRINT_E_FRAUDE, TIPO_NO_EVAL,  # noqa: E402
                             casar_linhas, centavos, fmt, pct, percentil, tabela_captura, vazio_para_nulo)

PASTA_DADOS = RAIZ / "data"
PASTA_RESULTADOS = Path(__file__).resolve().parent / "results"
CAMPOS = ["document_type"] + CAMPOS_TEXTO + CAMPOS_VALOR + ["fraud_suspected"]


def ler_csv(caminho):
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lista(texto):
    return [c for c in texto.split(";") if c]


def avaliar_foto(foto, doc, proventos, e, prompt):
    """Compara uma extração com o documento de origem, campo a campo e linha a linha."""
    cortados, parciais = set(lista(foto["cut_fields"])), set(lista(foto["partial_fields"]))
    campos, inventados = [], []
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

    resultados = []
    for foto in fotos:
        caminho = pasta / f"{foto['file']}.json"
        e = json.loads(caminho.read_text(encoding="utf-8"))["extraction"] if caminho.exists() else None
        r = {"foto": foto, "extracao": e, "ocr": ocr.get(foto["file"])}
        if e is not None and foto["expected_legible"] == "yes":
            r.update(avaliar_foto(foto, docs[foto["source_file"]], proventos[foto["source_file"]], e, prompt))
        resultados.append(r)
    return {"prompt": prompt, "modelo": modelo, "limite": cfg.legibility_min_confidence,
            "resultados": resultados, "log": log}


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
    porteiro = [x for x in r["resultados"] if x["ocr"]]
    fn = [x["foto"]["file"] for x in porteiro if x["foto"]["expected_legible"] == "yes"
          and float(x["ocr"]["mean_confidence"]) < r["limite"]]
    fp = [x["foto"]["file"] for x in porteiro if x["foto"]["expected_legible"] == "no"
          and float(x["ocr"]["mean_confidence"]) >= r["limite"]]
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
        f"Porteiro OCR (limite {r['limite']:g}): legíveis barradas (falso negativo): {len(fn)}"
        + (f" ({', '.join(fn)})" if fn else "")
        + f" | ilegíveis aprovadas: {len(fp)}" + (f" ({', '.join(fp)})" if fp else ""),
        f"API: {len(r['log'])} chamadas | erros: {pct(len(r['log']) - len(ok), len(r['log']))} | "
        f"latência p50 {fmt(percentil(lat, 50)) if lat else '—'} s, p90 {fmt(percentil(lat, 90)) if lat else '—'} s",
        "Tokens médios por foto: " + " | ".join(f"{k.replace('_tokens', '')} {v:.0f}" for k, v in tokens.items()),
    ]
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
        md += ["| Foto | Gabarito | Extraído |", "|---|---|---|"]
        md += [f"| {x['foto']['file']} | {x['foto']['expected_capture_type']} | {fmt(x['extracao'].get('capture_type'))} |"
               for x in r["resultados"] if x["extracao"]] + [""]

    md += ["## Fotos ilegíveis (fora da acurácia)", ""]
    for x in r["resultados"]:
        if x["foto"]["expected_legible"] == "no":
            md += [f"**{x['foto']['file']}**", "", "```json",
                   json.dumps(x["extracao"], ensure_ascii=False, indent=2), "```", ""]

    md += ["## Porteiro do OCR", "",
           f"Limite atual: {r['limite']:g} (provisório, calibrado na base sintética). "
           "⚠️ marca legível barrada pelo porteiro (falso negativo) ou ilegível aprovada.", "",
           "| Foto | Confiança OCR | Palavras | Porteiro | Seu julgamento | LLM extraiu certo | |",
           "|---|---|---|---|---|---|---|"]
    sem_ocr = [x["foto"]["file"] for x in r["resultados"] if not x["ocr"]]
    for x in sorted((x for x in r["resultados"] if x["ocr"]), key=lambda x: float(x["ocr"]["mean_confidence"])):
        conf = float(x["ocr"]["mean_confidence"]) if x["ocr"] else None
        passa = conf is not None and conf >= r["limite"]
        legivel = x["foto"]["expected_legible"] == "yes"
        if "campos" in x:
            a, t = acerto(x)
            llm = f"{a}/{t}" + (" (tudo)" if a == t else "")
        else:
            llm = "fora da acurácia"
        alerta = "⚠️" if passa != legivel else ""
        md.append(f"| {x['foto']['file']} | {fmt(conf)} | {x['ocr']['words'] if x['ocr'] else '—'} | "
                  f"{'legível' if passa else 'ilegível'} | {'legível' if legivel else 'ilegível'} | {llm} | {alerta} |")
    if sem_ocr:
        md += ["", "Sem OCR (rode `.venv/bin/python -m core.ocr --set v2`): " + ", ".join(sem_ocr)]
    return "\n".join(md) + "\n"


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
