"""Extração com o Gemini: uma imagem + o prompt de extração -> JSON estruturado.

Para cada arquivo pedido, envia a imagem de data/images/ e o prompt de
prompts/extraction_v1.txt ao modelo, com structured output no ESQUEMA abaixo,
e salva a resposta em cache/extraction_v1/<file>.json. Se o arquivo já
existir no cache, a API não é chamada. Cada chamada (com sucesso ou erro) é
registrada em cache/extraction_v1/_log.csv com tokens e latência.

Sem retentativas: um erro 429 (limite da cota) para a execução na hora. Outros
erros da API também param a execução, porque tendem a se repetir nos
documentos seguintes. A chave é lida do .env e nunca é impressa.

Uso: .venv/bin/python evaluation/extract.py A01_2026-07.png [outros arquivos...]
"""

import base64
import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

RAIZ = Path(__file__).resolve().parent.parent
PASTA_IMAGENS = RAIZ / "data" / "images"
VERSAO_PROMPT = "extraction_v1"
ARQUIVO_PROMPT = RAIZ / "prompts" / f"{VERSAO_PROMPT}.txt"
PASTA_CACHE = RAIZ / "cache" / VERSAO_PROMPT
ARQUIVO_LOG = PASTA_CACHE / "_log.csv"
MODELO = "gemini-3.8-flash"

TEXTO_OU_NULO = {"type": ["string", "null"]}
NUMERO_OU_NULO = {"type": ["number", "null"]}
ESQUEMA = {
    "type": "object",
    "properties": {
        "document_type": {"type": "string",
                          "enum": ["payslip", "payslip_vacation", "payslip_13th", "other"]},
        "pay_period": TEXTO_OU_NULO,
        "name_on_doc": TEXTO_OU_NULO,
        "cpf_on_doc": TEXTO_OU_NULO,
        "total_earnings": NUMERO_OU_NULO,
        "total_deductions": NUMERO_OU_NULO,
        "net_pay": NUMERO_OU_NULO,
        "earnings_lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "amount": {"type": "number"},
                    "counts_as_income": {"type": "boolean"},
                },
                "required": ["description", "amount", "counts_as_income"],
            },
        },
        "fraud_suspected": {"type": "boolean"},
        "fraud_reason": TEXTO_OU_NULO,
    },
    "required": ["document_type", "pay_period", "name_on_doc", "cpf_on_doc", "total_earnings",
                 "total_deductions", "net_pay", "earnings_lines", "fraud_suspected", "fraud_reason"],
}

COLUNAS_LOG = ["executed_at", "file", "model", "prompt_version", "status", "input_tokens",
               "output_tokens", "thought_tokens", "total_tokens", "latency_s", "error"]


class Parar(Exception):
    """Erro que encerra a execução sem processar os arquivos seguintes."""


def registrar(linha):
    novo = not ARQUIVO_LOG.exists()
    with open(ARQUIVO_LOG, "a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS_LOG, lineterminator="\n")
        if novo:
            escritor.writeheader()
        escritor.writerow(linha)


def extrair(cliente, chave, prompt, arquivo):
    """Chama a API para um arquivo e grava o cache. Devolve 'cache' ou 'api'."""
    destino = PASTA_CACHE / f"{arquivo}.json"
    if destino.exists():
        return "cache"

    imagem = PASTA_IMAGENS / arquivo
    imagem_b64 = base64.b64encode(imagem.read_bytes()).decode("ascii")
    linha_log = {"executed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "file": arquivo, "model": MODELO, "prompt_version": VERSAO_PROMPT}

    inicio = time.perf_counter()
    try:
        interacao = cliente.interactions.create(
            model=MODELO,
            input=[
                {"type": "text", "text": prompt},
                {"type": "image", "data": imagem_b64, "mime_type": "image/png"},
            ],
            response_format={"type": "text", "mime_type": "application/json", "schema": ESQUEMA},
            store=False,
        )
    except Exception as erro:
        latencia = time.perf_counter() - inicio
        # A Interactions API levanta erros com status_code (compat_errors); a API
        # legada, google.genai.errors.APIError com code.
        codigo = getattr(erro, "status_code", None) or getattr(erro, "code", None)
        codigo = codigo if isinstance(codigo, int) else None
        mensagem = f"{type(erro).__module__}.{type(erro).__name__}: {erro}".replace(chave, "***")
        registrar({**linha_log, "status": f"error_{codigo or 'other'}",
                   "latency_s": round(latencia, 3), "error": mensagem})
        motivo = "limite de cota (429)" if codigo == 429 else "erro da API"
        raise Parar(f"{arquivo}: {motivo} após {latencia:.2f} s, sem nova tentativa.\n{mensagem}")
    latencia = time.perf_counter() - inicio

    uso = interacao.usage
    texto = interacao.output_text or ""
    registrar({**linha_log, "status": "ok",
               "input_tokens": uso.total_input_tokens if uso else "",
               "output_tokens": uso.total_output_tokens if uso else "",
               "thought_tokens": uso.total_thought_tokens if uso else "",
               "total_tokens": uso.total_tokens if uso else "",
               "latency_s": round(latencia, 3), "error": ""})
    try:
        extracao = json.loads(texto)
    except json.JSONDecodeError:
        raise Parar(f"{arquivo}: resposta não é JSON válido; nada foi gravado no cache.\n{texto}")

    registro = {
        "file": arquivo,
        "model": MODELO,
        "prompt_version": VERSAO_PROMPT,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "extraction": extracao,
    }
    destino.write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return "api"


def main(arquivos):
    if not arquivos:
        sys.exit("Informe os arquivos de data/images/ a extrair.")
    faltando = [a for a in arquivos if not (PASTA_IMAGENS / a).exists()]
    if faltando:
        sys.exit(f"Arquivos não encontrados em data/images/: {', '.join(faltando)}")

    load_dotenv(RAIZ / ".env")
    chave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not chave:
        sys.exit("GEMINI_API_KEY não encontrada no .env.")
    # attempts=0: nenhuma retentativa (na Interactions API, attempts=1 ainda
    # permitiria uma segunda chamada).
    cliente = genai.Client(
        api_key=chave,
        http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=0)),
    )
    prompt = ARQUIVO_PROMPT.read_text(encoding="utf-8")
    PASTA_CACHE.mkdir(parents=True, exist_ok=True)

    for arquivo in arquivos:
        try:
            origem = extrair(cliente, chave, prompt, arquivo)
        except Parar as parada:
            print(f"PARADO: {parada}", file=sys.stderr)
            sys.exit(1)
        print(f"{arquivo}: {'do cache, sem chamar a API' if origem == 'cache' else 'extraído pela API'}")


if __name__ == "__main__":
    main(sys.argv[1:])
