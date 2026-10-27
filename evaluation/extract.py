"""Extração com o Gemini: uma imagem + o prompt de extração -> JSON estruturado.

Para cada arquivo, envia a imagem de data/images/ e o prompt de
prompts/<versão>.txt ao modelo, com structured output no ESQUEMA abaixo (o v3
acrescenta capture_type), e
salva a resposta em cache/<versão>/<modelo>/<file>.json. Se o arquivo já
existir no cache, a API não é chamada; por isso, rodar de novo continua de onde
parou. Cada chamada (com sucesso ou erro) é registrada em
cache/<versão>/<modelo>/_log.csv com tokens e latência.

Com --all, os documentos seguem uma ordem de prioridade: primeiro um documento
por cliente, o mais informativo do cenário; depois os demais. Assim, uma cota
diária pequena cobre o máximo de cenários.

Erros, sempre sem retentativa:
- 429 (limite da cota): para a execução na hora;
- 503 (modelo sobrecarregado), tempo limite (TEMPO_LIMITE_MS) ou queda de
  conexão: registra no log e segue para o próximo documento, que fica fora do
  cache e é tentado de novo na próxima execução;
- qualquer outro erro: para a execução, porque tende a se repetir.
A chave é lida do .env e nunca é impressa.

Com --set v2, a lista vem de data/photos.csv, as imagens de data/images/v2/ e o
cache fica em cache/photos_v2/<versão>/<modelo>/, separado da base v1.

Uso:
  .venv/bin/python evaluation/extract.py --prompt extraction_v2 --model gemini-3.5-flash --all
  .venv/bin/python evaluation/extract.py --set v2 --prompt extraction_v2 --model gemini-3.5-flash-lite --all
  .venv/bin/python evaluation/extract.py --prompt extraction_v1 A01_2026-07.png [...]
"""

import argparse
import base64
import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types

RAIZ = Path(__file__).resolve().parent.parent
PASTA_IMAGENS = RAIZ / "data" / "images"
ARQUIVO_DOCUMENTOS = RAIZ / "data" / "documents.csv"
CONJUNTOS = {
    # conjunto: (pasta das imagens, pasta-base do cache)
    "v1": (PASTA_IMAGENS, RAIZ / "cache"),
    "v2": (PASTA_IMAGENS / "v2", RAIZ / "cache" / "photos_v2"),
}
TIPOS_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
MODELO_PADRAO = "gemini-3.8-flash"
# Sem tempo limite, uma conexão que cai (ex.: o Mac entra em repouso) deixa a
# chamada esperando para sempre. 300 s é mais que o dobro da maior latência vista.
TEMPO_LIMITE_MS = 300_000

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
# A partir do v3, o modelo também informa como a imagem foi capturada (R1).
TIPOS_CAPTURA = ["original_file", "photo_of_paper", "photo_of_screen", "screenshot"]
ESQUEMA_V3 = {
    "type": "object",
    "properties": {**ESQUEMA["properties"], "capture_type": {"type": "string", "enum": TIPOS_CAPTURA}},
    "required": ESQUEMA["required"] + ["capture_type"],
}
ESQUEMAS = {"extraction_v3": ESQUEMA_V3}  # versões fora daqui usam ESQUEMA

COLUNAS_LOG = ["executed_at", "file", "model", "prompt_version", "status", "input_tokens",
               "output_tokens", "thought_tokens", "total_tokens", "latency_s", "error"]


class Parar(Exception):
    """Erro que encerra a execução sem processar os arquivos seguintes."""


class Pular(Exception):
    """Erro que deixa este arquivo para a próxima execução e segue para o seguinte."""


class Extrator:
    def __init__(self, cliente, chave, versao, modelo, intervalo_minimo=0.0, conjunto="v1"):
        self.cliente = cliente
        self.chave = chave
        self.versao = versao
        self.modelo = modelo
        self.intervalo_minimo = intervalo_minimo
        self.ultima_chamada = None
        self.prompt = (RAIZ / "prompts" / f"{versao}.txt").read_text(encoding="utf-8")
        self.esquema = ESQUEMAS.get(versao, ESQUEMA)
        self.pasta_imagens, base_cache = CONJUNTOS[conjunto]
        self.pasta_cache = base_cache / versao / modelo
        self.arquivo_log = self.pasta_cache / "_log.csv"
        self.pasta_cache.mkdir(parents=True, exist_ok=True)

    def registrar(self, linha):
        novo = not self.arquivo_log.exists()
        with open(self.arquivo_log, "a", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=COLUNAS_LOG, lineterminator="\n")
            if novo:
                escritor.writeheader()
            escritor.writerow(linha)

    def extrair(self, arquivo):
        """Chama a API para um arquivo e grava o cache. Devolve 'cache' ou 'api'."""
        destino = self.pasta_cache / f"{arquivo}.json"
        if destino.exists():
            return "cache"

        imagem = self.pasta_imagens / arquivo
        imagem_b64 = base64.b64encode(imagem.read_bytes()).decode("ascii")
        # Respeita o limite por minuto: o início de duas chamadas fica a pelo
        # menos intervalo_minimo segundos de distância (leituras do cache não contam).
        if self.ultima_chamada is not None:
            espera = self.intervalo_minimo - (time.monotonic() - self.ultima_chamada)
            if espera > 0:
                time.sleep(espera)
        self.ultima_chamada = time.monotonic()
        linha_log = {"executed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "file": arquivo, "model": self.modelo, "prompt_version": self.versao}

        inicio = time.perf_counter()
        try:
            interacao = self.cliente.interactions.create(
                model=self.modelo,
                input=[
                    {"type": "text", "text": self.prompt},
                    {"type": "image", "data": imagem_b64, "mime_type": TIPOS_MIME[imagem.suffix.lower()]},
                ],
                response_format={"type": "text", "mime_type": "application/json", "schema": self.esquema},
                store=False,
            )
        except Exception as erro:
            latencia = time.perf_counter() - inicio
            # A Interactions API levanta erros com status_code (compat_errors); a API
            # legada, google.genai.errors.APIError com code.
            codigo = getattr(erro, "status_code", None) or getattr(erro, "code", None)
            codigo = codigo if isinstance(codigo, int) else None
            classes = {c.__name__ for c in type(erro).__mro__}
            if "APITimeoutError" in classes or isinstance(erro, httpx.TimeoutException):
                status = "error_timeout"
            elif "APIConnectionError" in classes or isinstance(erro, httpx.TransportError):
                status = "error_connection"
            else:
                status = f"error_{codigo or 'other'}"
            mensagem = f"{type(erro).__module__}.{type(erro).__name__}: {erro}".replace(self.chave, "***")
            self.registrar({**linha_log, "status": status,
                            "latency_s": round(latencia, 3), "error": mensagem})
            if codigo == 503 or status in ("error_timeout", "error_connection"):
                motivo = {"error_timeout": "tempo limite", "error_connection": "falha de conexão"}.get(
                    status, "modelo sobrecarregado (503)")
                raise Pular(f"{arquivo}: {motivo} após {latencia:.2f} s; fica para a próxima execução.")
            motivo = "limite de cota (429)" if codigo == 429 else "erro da API"
            raise Parar(f"{arquivo}: {motivo} após {latencia:.2f} s, sem nova tentativa.\n{mensagem}")
        latencia = time.perf_counter() - inicio

        uso = interacao.usage
        texto = interacao.output_text or ""
        self.registrar({**linha_log, "status": "ok",
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
            "model": self.modelo,
            "prompt_version": self.versao,
            "prompt_sha256": hashlib.sha256(self.prompt.encode("utf-8")).hexdigest(),
            "extraction": extracao,
        }
        destino.write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return "api"


def centavos(texto):
    return round(float(texto) * 100) if texto else None


def peso_informativo(doc):
    """Quanto o documento diz sobre o cenário do cliente (maior = mais informativo)."""
    peso = 0
    if doc["degradation"] != "none" or doc["extra_text"]:
        peso += 4
    if doc["true_type"] != "payslip":
        peso += 2
    totais = [centavos(doc[c]) for c in ("total_earnings", "total_deductions", "net_pay")]
    if None not in totais and totais[0] - totais[1] != totais[2]:
        peso += 4  # conta que não fecha (N15)
    return peso


def ordem_de_prioridade(documentos):
    """Um documento por cliente (o mais informativo) primeiro; depois os demais, na ordem do CSV."""
    por_cliente = {}
    for doc in documentos:
        atual = por_cliente.get(doc["applicant_id"])
        if atual is None or peso_informativo(doc) > peso_informativo(atual):
            por_cliente[doc["applicant_id"]] = doc
    primeiros = [d["file"] for d in por_cliente.values()]
    return primeiros + [d["file"] for d in documentos if d["file"] not in primeiros]


def main():
    parser = argparse.ArgumentParser(description="Extrai documentos com o Gemini, com cache.")
    parser.add_argument("--prompt", required=True, help="versão do prompt, ex.: extraction_v2")
    parser.add_argument("--set", choices=sorted(CONJUNTOS), default="v1",
                        help="v1: base sintética (documents.csv); v2: fotos (photos.csv)")
    parser.add_argument("--model", default=MODELO_PADRAO, help=f"modelo (padrão: {MODELO_PADRAO})")
    parser.add_argument("--min-interval", type=float, default=0.0,
                        help="segundos mínimos entre o início de duas chamadas (ex.: 4 = até 15 por minuto)")
    parser.add_argument("--all", action="store_true",
                        help="todos os arquivos de data/documents.csv, em ordem de prioridade")
    parser.add_argument("arquivos", nargs="*", help="arquivos de data/images/")
    args = parser.parse_args()

    if args.all == bool(args.arquivos):
        sys.exit("Informe --all ou uma lista de arquivos (não os dois).")
    pasta_imagens = CONJUNTOS[args.set][0]
    if args.all and args.set == "v2":
        with open(RAIZ / "data" / "photos.csv", newline="", encoding="utf-8") as f:
            arquivos = [d["file"] for d in csv.DictReader(f)]
    elif args.all:
        with open(ARQUIVO_DOCUMENTOS, newline="", encoding="utf-8") as f:
            arquivos = ordem_de_prioridade(list(csv.DictReader(f)))
    else:
        arquivos = args.arquivos
    faltando = [a for a in arquivos if not (pasta_imagens / a).exists()]
    if faltando:
        sys.exit(f"Arquivos não encontrados em {pasta_imagens.relative_to(RAIZ)}/: {', '.join(faltando)}")
    if not (RAIZ / "prompts" / f"{args.prompt}.txt").exists():
        sys.exit(f"Prompt não encontrado: prompts/{args.prompt}.txt")

    load_dotenv(RAIZ / ".env")
    chave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not chave:
        sys.exit("GEMINI_API_KEY não encontrada no .env.")
    # attempts=0: nenhuma retentativa (na Interactions API, attempts=1 ainda
    # permitiria uma segunda chamada).
    cliente = genai.Client(
        api_key=chave,
        http_options=types.HttpOptions(timeout=TEMPO_LIMITE_MS,
                                       retry_options=types.HttpRetryOptions(attempts=0)),
    )
    extrator = Extrator(cliente, chave, args.prompt, args.model, args.min_interval, args.set)
    print(f"Modelo: {args.model} | prompt: {args.prompt} | intervalo mínimo: {args.min_interval:g} s | "
          f"cache: {extrator.pasta_cache.relative_to(RAIZ)}", flush=True)

    contagem = {"api": 0, "cache": 0, "pulados": 0}
    for i, arquivo in enumerate(arquivos, 1):
        try:
            origem = extrator.extrair(arquivo)
        except Pular as pulo:
            contagem["pulados"] += 1
            print(f"[{i}/{len(arquivos)}] PULADO: {pulo}", flush=True)
            continue
        except Parar as parada:
            print(f"[{i}/{len(arquivos)}] PARADO: {parada}", file=sys.stderr, flush=True)
            print(f"Resumo até aqui: {contagem}", flush=True)
            sys.exit(1)
        contagem[origem] += 1
        if origem == "api":
            print(f"[{i}/{len(arquivos)}] {arquivo}: extraído pela API", flush=True)
    print(f"Fim: {contagem['api']} extraídos pela API, {contagem['cache']} já no cache, "
          f"{contagem['pulados']} pulados por 503, tempo limite ou conexão "
          "(rode de novo para tentá-los).", flush=True)


if __name__ == "__main__":
    main()
