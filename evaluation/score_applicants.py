"""Eval por cliente: roda o motor de regras e compara com data/ground_truth.csv.

Dois modos de entrada, sem nenhuma chamada de API:
- --source oracle: documentos montados a partir do gabarito (documents.csv e
  line_items.csv), simulando um LLM perfeito. Mede o motor de regras com o OCR
  real. Fraude = extra_text preenchido; capture_type pela degradation
  (captura_esperada de score_documents.py); bank_statement conta como other.
  Documento com degradation = blurred vem sem nenhum campo, como um LLM perfeito
  devolveria para uma imagem que não dá para ler.
- --source cache --model <modelo>: documentos vindos do cache do LLM
  (cache/<prompt>/<modelo>/). Mede o sistema de ponta a ponta.
Nos dois modos, o número de palavras do OCR vem de cache/ocr/confidence.csv
(gerado por .venv/bin/python -m core.ocr).

Reporta matriz de confusão (approve, reject, review), acerto por classe, acerto
do motivo principal, taxa de falso negativo (deveria aprovar e foi reprovado),
diferença de renda válida e a lista de clientes errados. Grava o relatório em
evaluation/results/applicants_<fonte>[_<prompt>_<modelo>].md.

Uso:
  .venv/bin/python evaluation/score_applicants.py --source oracle
  .venv/bin/python evaluation/score_applicants.py --source cache --model gemini-3.5-flash-lite
"""

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import config as configuracao  # noqa: E402
from core.engine import decidir  # noqa: E402
from core.inputs import documento_da_extracao  # noqa: E402
from core.models import Cliente, Documento, Linha  # noqa: E402
from core.ocr import ARQUIVO_CONFIANCAS, carregar_palavras  # noqa: E402
from score_documents import captura_esperada  # noqa: E402

PASTA_DADOS = RAIZ / "data"
PASTA_RESULTADOS = Path(__file__).resolve().parent / "results"
CLASSES = ["approve", "reject", "review"]


def ler_csv(nome, encoding="utf-8"):
    with open(PASTA_DADOS / nome, newline="", encoding=encoding) as f:
        return list(csv.DictReader(f))


def dinheiro(texto):
    return Decimal(texto).quantize(Decimal("0.01")) if texto not in ("", None) else None


def clientes():
    return {a["applicant_id"]: Cliente(a["applicant_id"], a["name"], a["cpf"], dinheiro(a["installment_amount"]),
                                       date.fromisoformat(a["analysis_date"]))
            for a in ler_csv("applicants.csv")}


TIPO_NO_EVAL = {"bank_statement": "other"}


def documentos_oracle(palavras):
    proventos = defaultdict(list)
    for l in ler_csv("line_items.csv"):
        if l["kind"] == "earning":
            proventos[l["file"]].append(Linha(l["description"], dinheiro(l["amount"]), l["counts_as_income"] == "yes"))
    por_cliente, faltando = defaultdict(list), []
    for d in ler_csv("documents.csv"):
        fraude = bool(d["extra_text"])
        if d["degradation"] == "blurred":
            d = {**d, **{c: "" for c in ("pay_period", "name_on_doc", "cpf_on_doc", "total_earnings",
                                          "total_deductions", "net_pay")}}
            proventos[d["file"]] = []
        por_cliente[d["applicant_id"]].append(Documento(
            file=d["file"], document_type=TIPO_NO_EVAL.get(d["true_type"], d["true_type"]),
            pay_period=d["pay_period"] or None, name_on_doc=d["name_on_doc"] or None,
            cpf_on_doc=d["cpf_on_doc"] or None, total_earnings=dinheiro(d["total_earnings"]),
            total_deductions=dinheiro(d["total_deductions"]), net_pay=dinheiro(d["net_pay"]),
            earnings_lines=proventos[d["file"]], fraud_suspected=fraude,
            fraud_reason="texto de injection" if fraude else None,
            ocr_words=palavras.get(d["file"]), capture_type=captura_esperada(d),
        ))
    return por_cliente, faltando


def documentos_cache(prompt, modelo, palavras):
    pasta = RAIZ / "cache" / prompt / modelo
    if not pasta.is_dir():
        sys.exit(f"Cache não encontrado: {pasta.relative_to(RAIZ)}")
    por_cliente, faltando = defaultdict(list), []
    for d in ler_csv("documents.csv"):
        caminho = pasta / f"{d['file']}.json"
        if not caminho.exists():
            faltando.append(d["file"])
            continue
        extracao = json.loads(caminho.read_text(encoding="utf-8"))["extraction"]
        por_cliente[d["applicant_id"]].append(documento_da_extracao(d["file"], extracao, palavras.get(d["file"])))
    return por_cliente, faltando


def avaliar(fonte, prompt, modelo):
    cfg = configuracao.carregar()
    if not ARQUIVO_CONFIANCAS.exists():
        sys.exit("Sem confiança de OCR: rode .venv/bin/python -m core.ocr")
    palavras = carregar_palavras()
    arquivos = [d["file"] for d in ler_csv("documents.csv")]
    sem_ocr = [a for a in arquivos if a not in palavras]
    if sem_ocr:
        sys.exit(f"Documentos sem OCR: {', '.join(sem_ocr)}")
    if fonte == "oracle":
        docs, faltando = documentos_oracle(palavras)
    else:
        docs, faltando = documentos_cache(prompt, modelo, palavras)
    gabarito = ler_csv("ground_truth.csv", encoding="utf-8-sig")
    cadastro = clientes()

    linhas = []
    for g in gabarito:
        cid = g["applicant_id"]
        # A base não tem histórico de envios: todo pedido começa sem falhas de legibilidade.
        decisao = decidir(cadastro[cid], docs.get(cid, []), cfg, prior_legibility_failures=0)
        esperada_renda = dinheiro(g["expected_valid_income"])
        linhas.append({
            "cliente": cid, "cenario": g["scenario"],
            "esperado": g["expected_decision"], "obtido": decisao.decision,
            "motivo_esperado": g["expected_reason"] or None, "motivo_obtido": decisao.main_reason,
            "motivos": decisao.reasons, "renda_esperada": esperada_renda, "renda_obtida": decisao.valid_income,
            "meses": decisao.months_used, "fraude": decisao.fraud_flag, "sinais_fraude": decisao.fraud_reasons,
        })
    return {"fonte": fonte, "prompt": prompt, "modelo": modelo, "config": cfg, "linhas": linhas,
            "faltando": faltando}


def metricas(r):
    linhas = r["linhas"]
    matriz = Counter((l["esperado"], l["obtido"]) for l in linhas)
    por_classe = {c: (matriz[(c, c)], sum(1 for l in linhas if l["esperado"] == c)) for c in CLASSES}
    decisao_ok = sum(l["esperado"] == l["obtido"] for l in linhas)
    motivo_ok = sum(l["motivo_esperado"] == l["motivo_obtido"] for l in linhas)
    aprovaveis = [l for l in linhas if l["esperado"] == "approve"]
    falsos_negativos = [l for l in aprovaveis if l["obtido"] == "reject"]
    comparaveis = [l for l in linhas if l["renda_esperada"] is not None and l["renda_obtida"] is not None]
    renda_diferente = [l for l in comparaveis if abs(l["renda_esperada"] - l["renda_obtida"]) > Decimal("0.01")]
    so_um_lado = [l for l in linhas if (l["renda_esperada"] is None) != (l["renda_obtida"] is None)]
    errados = [l for l in linhas if l["esperado"] != l["obtido"] or l["motivo_esperado"] != l["motivo_obtido"]]
    return {"matriz": matriz, "por_classe": por_classe, "decisao_ok": decisao_ok, "motivo_ok": motivo_ok,
            "total": len(linhas), "aprovaveis": len(aprovaveis), "falsos_negativos": falsos_negativos,
            "comparaveis": comparaveis, "renda_diferente": renda_diferente, "so_um_lado": so_um_lado,
            "errados": errados}


def pct(a, b):
    return f"{a}/{b} ({100 * a / b:.1f}%)" if b else "—"


def fmt(v):
    if v is None:
        return "—"
    if isinstance(v, list):
        return ", ".join(v) if v else "—"
    return str(v)


def titulo(r):
    return "oracle (gabarito)" if r["fonte"] == "oracle" else f"cache {r['prompt']} · {r['modelo']}"


def resumo(r, m):
    linhas = [
        f"Fonte: {titulo(r)} | config v{r['config'].version} | clientes: {m['total']}",
        f"Decisão certa: {pct(m['decisao_ok'], m['total'])} | motivo principal certo: {pct(m['motivo_ok'], m['total'])}",
        "Acerto por classe: " + " | ".join(f"{c} {pct(*m['por_classe'][c])}" for c in CLASSES),
        f"Falso negativo (deveria aprovar, foi reprovado): {pct(len(m['falsos_negativos']), m['aprovaveis'])}",
        f"Renda válida diferente do gabarito (> R$ 0,01): {len(m['renda_diferente'])} de {len(m['comparaveis'])} comparáveis"
        + (f"; presente só de um lado: {len(m['so_um_lado'])}" if m["so_um_lado"] else ""),
        f"Clientes com decisão ou motivo errado: {len(m['errados'])}"
        + (" (" + ", ".join(l["cliente"] for l in m["errados"]) + ")" if m["errados"] else ""),
    ]
    if r["faltando"]:
        linhas.append(f"Documentos sem extração no cache: {len(r['faltando'])}")
    return linhas


def relatorio(r, m):
    md = [f"# Avaliação por cliente: {titulo(r)}", "",
          f"Gerado por `evaluation/score_applicants.py`, sem chamadas à API. Configuração: "
          f"`config/default_rules.yaml` v{r['config'].version} "
          f"(multiplicador {r['config'].income_multiplier}, similaridade {r['config'].name_similarity}, "
          "porteiro: OCR e LLM sem leitura ou CPF inválido).", "",
          "## Resumo", "", "```", *resumo(r, m), "```", "",
          "## Matriz de confusão", "", "Linhas: gabarito. Colunas: motor.", "",
          "| gabarito \\ obtido | " + " | ".join(CLASSES) + " |", "|---" * (len(CLASSES) + 1) + "|"]
    for e in CLASSES:
        md.append(f"| {e} | " + " | ".join(str(m["matriz"][(e, o)]) for o in CLASSES) + " |")
    md += ["", "## Clientes errados (decisão ou motivo principal)", ""]
    if m["errados"]:
        md += ["| Cliente | Cenário | Esperado | Obtido | Motivo esperado | Motivo obtido | Todos os motivos |",
               "|---|---|---|---|---|---|---|"]
        md += [f"| {l['cliente']} | {l['cenario']} | {l['esperado']} | {l['obtido']} | {fmt(l['motivo_esperado'])} | "
               f"{fmt(l['motivo_obtido'])} | {fmt(l['motivos'])} |" for l in m["errados"]]
    else:
        md.append("Nenhum.")
    md += ["", "## Renda válida", "",
           f"Comparáveis: {len(m['comparaveis'])}; diferentes do gabarito (> R$ 0,01): {len(m['renda_diferente'])}.", ""]
    divergentes = m["renda_diferente"] + m["so_um_lado"]
    if divergentes:
        md += ["| Cliente | Gabarito | Motor | Meses usados |", "|---|---|---|---|"]
        md += [f"| {l['cliente']} | {fmt(l['renda_esperada'])} | {fmt(l['renda_obtida'])} | {fmt(l['meses'])} |"
               for l in divergentes]
        md.append("")
    md += ["## Todos os clientes", "",
           "| Cliente | Esperado | Obtido | Motivo esperado | Motivo obtido | Renda gabarito | Renda motor | Fraude |",
           "|---|---|---|---|---|---|---|---|"]
    md += [f"| {l['cliente']} | {l['esperado']} | {l['obtido']} | {fmt(l['motivo_esperado'])} | {fmt(l['motivo_obtido'])} | "
           f"{fmt(l['renda_esperada'])} | {fmt(l['renda_obtida'])} | {'sim' if l['fraude'] else 'não'} |"
           for l in r["linhas"]]
    if r["faltando"]:
        md += ["", "## Documentos sem extração no cache", "", ", ".join(r["faltando"])]
    return "\n".join(md) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Eval por cliente do motor de regras.")
    parser.add_argument("--source", choices=["oracle", "cache"], required=True)
    parser.add_argument("--model", help="modelo do cache (obrigatório com --source cache)")
    parser.add_argument("--prompt", default="extraction_v3", help="versão do prompt do cache")
    args = parser.parse_args()
    if args.source == "cache" and not args.model:
        sys.exit("Com --source cache, informe --model.")

    r = avaliar(args.source, args.prompt, args.model)
    m = metricas(r)
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    nome = "applicants_oracle.md" if args.source == "oracle" else \
        f"applicants_cache_{args.prompt.removeprefix('extraction_')}_{args.model}.md"
    destino = PASTA_RESULTADOS / nome
    destino.write_text(relatorio(r, m), encoding="utf-8")
    print("\n".join(resumo(r, m)))
    print(f"\nRelatório completo: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
