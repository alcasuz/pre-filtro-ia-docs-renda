"""Compara versões do porteiro de legibilidade (R7) sem alterar o motor.

Cada versão simulada decide, documento a documento, se ele é legível. Um
documento ilegível entra no motor como o porteiro final o reconheceria (0
palavras no OCR, nenhum campo extraído e tipo unidentified); um legível entra com o OCR marcando ao
menos uma palavra. O motor real roda inalterado, então os critérios do porteiro
final que não dependem do OCR (CPF com dígitos inválidos) valem em todas as
versões.

Versões:
- final: o porteiro do motor (core/rules/legibility.py), sem simulação;
- atual: o porteiro anterior: confiança média do OCR >= LIMITE_CONFIANCA, imagem
  como veio;
- a_rotacao: o mesmo limite, mas lendo a imagem na melhor rotação (0, 90, 180 ou
  270 graus): a de maior soma das confianças das palavras (palavras x média).
  Contar só palavras não serve: numa rotação errada o Tesseract "reconhece" muito
  lixo com confiança baixa (ex.: A01 a 90 graus, 122 palavras com média 28). O
  OSD do Tesseract não está instalado (só o modelo por);
- b_piso_palavras: ilegível só se, na melhor rotação, o OCR reconhecer menos de
  PISO_PALAVRAS palavras;
- c_sem_ocr: sem OCR; ilegível se a competência extraída estiver a mais de
  MESES_COMPETENCIA meses da analysis_date (o CPF inválido já é checado pelo motor).

Bases:
- v1 inteira, nos modos oracle (gabarito) e cache (extração do LLM), contra
  data/ground_truth.csv (decisão e motivo principal);
- as fotos de data/photos.csv: cada foto substitui o documento de origem no
  cliente dele, com os demais documentos do gabarito, como em score_photos.py;
  esperado pelas regras atuais (decisao_esperada de score_photos.py).

O OCR das 4 rotações fica em cache/ocr/rotations_<conjunto>.csv; só é recalculado
para arquivos que faltam. Nenhuma chamada de API.

Uso: .venv/bin/python evaluation/compare_gates.py [--prompt extraction_v3] [--model gemini-3.5-flash-lite]
"""

import argparse
import csv
import json
import sys
from dataclasses import replace
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import config as configuracao  # noqa: E402
from core.engine import decidir  # noqa: E402
from core.inputs import documento_da_extracao  # noqa: E402
from core.rules import legibility  # noqa: E402
from core.ocr import CONJUNTOS, carregar_palavras, confianca_da_imagem  # noqa: E402
from score_applicants import clientes, documentos_cache, documentos_oracle  # noqa: E402
from score_photos import decisao_esperada, ler_csv_bom  # noqa: E402

PASTA_RESULTADOS = Path(__file__).resolve().parent / "results"
ROTACOES = (0, 90, 180, 270)
PISO_PALAVRAS = 5
MESES_COMPETENCIA = 12
LIMITE_CONFIANCA = 30.0  # limite do porteiro anterior (config v1)
VERSOES = ["final", "atual", "a_rotacao", "b_piso_palavras", "c_sem_ocr"]


def ler_csv(caminho):
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def leituras_por_rotacao(conjunto):
    """{arquivo: {ângulo: {"mean_confidence", "words"}}}, com cache em disco."""
    lista, pasta, _ = CONJUNTOS[conjunto]
    destino = RAIZ / "cache" / "ocr" / f"rotations_{conjunto}.csv"
    leituras = {}
    if destino.exists():
        for l in ler_csv(destino):
            leituras.setdefault(l["file"], {})[int(l["angle"])] = {
                "mean_confidence": float(l["mean_confidence"]), "words": int(l["words"])}
    arquivos = [d["file"] for d in ler_csv(lista)]
    faltando = [a for a in arquivos if len(leituras.get(a, {})) < len(ROTACOES)]
    if faltando:
        novo = not destino.exists()
        with open(destino, "a", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=["file", "angle", "mean_confidence", "words"], lineterminator="\n")
            if novo:
                escritor.writeheader()
            for i, arquivo in enumerate(faltando, 1):
                with Image.open(pasta / arquivo) as imagem:
                    imagem.load()
                    for angulo in ROTACOES:
                        if angulo in leituras.get(arquivo, {}):
                            continue
                        girada = imagem.rotate(angulo, expand=True) if angulo else imagem
                        r = confianca_da_imagem(girada)
                        leituras.setdefault(arquivo, {})[angulo] = r
                        escritor.writerow({"file": arquivo, "angle": angulo, **r})
                print(f"[OCR {conjunto} {i}/{len(faltando)}] {arquivo}", flush=True)
    return leituras


def melhor_rotacao(leituras):
    return max(leituras.values(), key=lambda r: r["words"] * r["mean_confidence"])


def meses_de_distancia(periodo, analysis_date):
    try:
        ano, mes = int(periodo[:4]), int(periodo[5:7])
    except (TypeError, ValueError):
        return None
    return abs((analysis_date.year * 12 + analysis_date.month) - (ano * 12 + mes))


def legivel(versao, doc, cliente, leituras, limite):
    rot = leituras.get(doc.file)
    if versao == "atual":
        return rot is not None and rot[0]["mean_confidence"] >= limite
    if versao == "a_rotacao":
        return rot is not None and melhor_rotacao(rot)["mean_confidence"] >= limite
    if versao == "b_piso_palavras":
        return rot is not None and melhor_rotacao(rot)["words"] >= PISO_PALAVRAS
    distancia = meses_de_distancia(doc.pay_period, cliente.analysis_date)
    return distancia is None or distancia <= MESES_COMPETENCIA


def aplicar(versao, docs, cliente, leituras, limite):
    if versao == "final":
        return docs
    return [replace(d, ocr_words=max(d.ocr_words or 0, 1)) if legivel(versao, d, cliente, leituras, limite)
            else replace(d, ocr_words=0, document_type="unidentified", pay_period=None, name_on_doc=None, cpf_on_doc=None, total_earnings=None,
                         total_deductions=None, net_pay=None, earnings_lines=[])
            for d in docs]


def avaliar_v1(versao, por_cliente, cadastro, gabarito, leituras, cfg):
    erros = []
    for g in gabarito:
        cid = g["applicant_id"]
        docs = aplicar(versao, por_cliente.get(cid, []), cadastro[cid], leituras, LIMITE_CONFIANCA)
        d = decidir(cadastro[cid], docs, cfg, prior_legibility_failures=0)
        esperado = (g["expected_decision"], g["expected_reason"] or None)
        if (d.decision, d.main_reason) != esperado:
            erros.append(f"{cid} ({esperado[0]}/{esperado[1]} → {d.decision}/{d.main_reason})")
    return len(gabarito) - len(erros), erros


def avaliar_fotos(versao, fotos, extracoes, oracle, cadastro, gabarito, documentos, leituras, cfg):
    certas, erros, barradas = 0, [], []
    for foto in fotos:
        cid = foto["applicant_id"]
        palavras = leituras.get(foto["file"], {}).get(0, {}).get("words")
        doc = documento_da_extracao(foto["file"], extracoes[foto["file"]], palavras)
        if versao == "final":
            barrada = legibility.avaliar(doc, cfg).status != "pass"
        else:
            barrada = not legivel(versao, doc, cadastro[cid], leituras, LIMITE_CONFIANCA)
        if barrada and foto["expected_legible"] == "yes":
            barradas.append(foto["file"])
        outros = [d for d in oracle[cid] if d.file != foto["source_file"]]
        docs = aplicar(versao, outros + [doc], cadastro[cid], leituras, LIMITE_CONFIANCA)
        d = decidir(cadastro[cid], docs, cfg, prior_legibility_failures=0)
        esperado = decisao_esperada(foto, gabarito[cid], documentos[foto["source_file"]], True)
        if (d.decision, d.main_reason) == esperado:
            certas += 1
        else:
            erros.append(f"{foto['file']} ({esperado[0]}/{esperado[1]} → {d.decision}/{d.main_reason})")
    return certas, erros, barradas


def main():
    parser = argparse.ArgumentParser(description="Compara versões do porteiro de legibilidade.")
    parser.add_argument("--prompt", default="extraction_v4")
    parser.add_argument("--model", default="gemini-3.5-flash-lite")
    args = parser.parse_args()

    cfg = configuracao.carregar()
    leituras = {**leituras_por_rotacao("v1"), **leituras_por_rotacao("v2")}
    cadastro = clientes()
    gabarito_lista = ler_csv_bom(RAIZ / "data" / "ground_truth.csv")
    gabarito = {g["applicant_id"]: g for g in gabarito_lista}
    documentos = {d["file"]: d for d in ler_csv(RAIZ / "data" / "documents.csv")}
    palavras = carregar_palavras()
    oracle, _ = documentos_oracle(palavras)
    cache, faltando = documentos_cache(args.prompt, args.model, palavras)
    if faltando:
        sys.exit(f"v1 documents not extracted in the cache: {', '.join(faltando)}")
    fotos = [f for f in ler_csv(RAIZ / "data" / "photos.csv") if f["expected_legible"]]
    pasta_fotos = RAIZ / "cache" / "photos_v2" / args.prompt / args.model
    extracoes = {f["file"]: json.loads((pasta_fotos / f"{f['file']}.json").read_text(encoding="utf-8"))["extraction"]
                 for f in fotos}

    linhas = []
    for versao in VERSOES:
        o_ok, o_err = avaliar_v1(versao, oracle, cadastro, gabarito_lista, leituras, cfg)
        c_ok, c_err = avaliar_v1(versao, cache, cadastro, gabarito_lista, leituras, cfg)
        f_ok, f_err, barradas = avaliar_fotos(versao, fotos, extracoes, oracle, cadastro, gabarito, documentos,
                                              leituras, cfg)
        linhas.append({"versao": versao, "oracle": (o_ok, o_err), "cache": (c_ok, c_err),
                       "fotos": (f_ok, f_err), "barradas": barradas})

    total_v1, total_fotos = len(gabarito_lista), len(fotos)
    md = [f"# Legibility gate comparison · {args.prompt} · {args.model}", "",
          f"Generated by `evaluation/compare_gates.py`, with no API calls. Confidence threshold (atual and a): "
          f"{LIMITE_CONFIANCA:g}; word floor: {PISO_PALAVRAS}; pay period at most "
          f"{MESES_COMPETENCIA} months away (c). Right decision = right decision and main reason.", "",
          "| Version | v1 oracle | v1 cache | Photos | Readable photos blocked (false negative) |", "|---|---|---|---|---|"]
    for l in linhas:
        md.append(f"| {l['versao']} | {l['oracle'][0]}/{total_v1} | {l['cache'][0]}/{total_v1} | "
                  f"{l['fotos'][0]}/{total_fotos} | {len(l['barradas'])}"
                  + (f": {', '.join(l['barradas'])}" if l["barradas"] else "") + " |")
    md += ["", "## Errors per version", ""]
    for l in linhas:
        md += [f"### {l['versao']}", ""]
        for nome, chave in (("v1 oracle", "oracle"), ("v1 cache", "cache"), ("Photos", "fotos")):
            md.append(f"- {nome}: " + ("; ".join(l[chave][1]) if l[chave][1] else "none"))
        md.append("")
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    destino = PASTA_RESULTADOS / f"gates_{args.prompt.removeprefix('extraction_')}_{args.model}.md"
    destino.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\nReport: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
