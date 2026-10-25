"""Smoke test do Gemini: UMA chamada, com uma imagem e structured output.

Envia o primeiro holerite do A01 com um prompt curto, pede a resposta no
esquema {"document_type", "pay_period"} e grava em
evaluation/smoke_test_result.json o modelo, a resposta, os tokens (lidos dos
metadados de uso da API) e a latência medida no código.

Não há retentativas: qualquer erro (chave inválida, 429 etc.) é mostrado por
completo e o script para. A chave é lida do .env e nunca é impressa.

Uso: .venv/bin/python evaluation/smoke_test.py
"""

import base64
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
IMAGEM = RAIZ / "data" / "images" / "A01_2026-07.png"
RESULTADO = Path(__file__).resolve().parent / "smoke_test_result.json"

# Flash numerado mais recente da lista da chave. Um nome fixo, e não o alias
# gemini-flash-latest, para que o resultado seja comparável entre execuções.
MODELO = "gemini-3.8-flash"
PROMPT = "Classifique este documento e diga qual é a competência."
ESQUEMA = {
    "type": "object",
    "properties": {
        "document_type": {"type": "string"},
        "pay_period": {"type": "string"},
    },
    "required": ["document_type", "pay_period"],
}


def main():
    load_dotenv(RAIZ / ".env")
    chave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not chave:
        sys.exit("GEMINI_API_KEY não encontrada no .env.")

    # attempts=0: nenhuma retentativa. Na Interactions API, attempts=1 ainda
    # permitiria uma segunda chamada.
    cliente = genai.Client(
        api_key=chave,
        http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=0)),
    )
    imagem_b64 = base64.b64encode(IMAGEM.read_bytes()).decode("ascii")

    inicio = time.perf_counter()
    try:
        interacao = cliente.interactions.create(
            model=MODELO,
            input=[
                {"type": "text", "text": PROMPT},
                {"type": "image", "data": imagem_b64, "mime_type": "image/png"},
            ],
            response_format={"type": "text", "mime_type": "application/json", "schema": ESQUEMA},
            store=False,  # não guardar a interação nos servidores do Google
        )
    except Exception as erro:  # mostra tudo e para, sem tentar de novo
        latencia = time.perf_counter() - inicio
        mensagem = f"{type(erro).__module__}.{type(erro).__name__}: {erro}".replace(chave, "***")
        print(f"ERRO após {latencia:.2f} s, sem nova tentativa:\n{mensagem}", file=sys.stderr)
        sys.exit(1)
    latencia = time.perf_counter() - inicio

    uso = interacao.usage
    texto = interacao.output_text or ""
    try:
        resposta = json.loads(texto)
    except json.JSONDecodeError:
        resposta = None

    resultado = {
        "model": MODELO,
        "image": str(IMAGEM.relative_to(RAIZ)),
        "prompt": PROMPT,
        "status": str(interacao.status),
        "response": resposta,
        "response_text": texto,
        "input_tokens": uso.total_input_tokens if uso else None,
        "output_tokens": uso.total_output_tokens if uso else None,
        "thought_tokens": uso.total_thought_tokens if uso else None,
        "total_tokens": uso.total_tokens if uso else None,
        "latency_s": round(latencia, 3),
        "sdk_version": genai.__version__,
        "executed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    RESULTADO.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
