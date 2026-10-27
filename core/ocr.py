"""OCR com o Tesseract: confiança média das palavras de uma imagem (sinal de legibilidade da R7).

A confiança média é a média simples da confiança (0 a 100) de cada palavra que o
Tesseract reconheceu, ignorando as caixas sem texto (conf = -1). Imagem sem
nenhuma palavra reconhecida tem confiança 0.

A confiança depende da versão do Tesseract e do modelo de idioma; ambos são
registrados junto com o resultado, porque o limite de legibilidade só vale para
a combinação em que foi calibrado.

Uso (gera cache/ocr/confidence.csv para todas as imagens de data/documents.csv):
  .venv/bin/python -m core.ocr
"""

import csv
import os
import shutil
from pathlib import Path

import pytesseract
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
IDIOMA = "por"
CONFIG_TESSERACT = "--psm 3"  # segmentação automática da página (padrão do Tesseract)

# MacPorts instala em /opt/local/bin, que pode não estar no PATH de quem chama o Python.
_comando = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract") or "/opt/local/bin/tesseract"
pytesseract.pytesseract.tesseract_cmd = _comando


def versao_tesseract():
    return str(pytesseract.get_tesseract_version())


def confianca_media(caminho, idioma=IDIOMA):
    """Devolve {"mean_confidence": float de 0 a 100, "words": int} para a imagem."""
    with Image.open(caminho) as imagem:
        dados = pytesseract.image_to_data(imagem, lang=idioma, config=CONFIG_TESSERACT,
                                          output_type=pytesseract.Output.DICT)
    confiancas = [float(c) for c, texto in zip(dados["conf"], dados["text"])
                  if float(c) >= 0 and texto.strip()]
    media = sum(confiancas) / len(confiancas) if confiancas else 0.0
    return {"mean_confidence": round(media, 2), "words": len(confiancas)}


ARQUIVO_CONFIANCAS = RAIZ / "cache" / "ocr" / "confidence.csv"


def carregar_confiancas(caminho=ARQUIVO_CONFIANCAS):
    """{arquivo: confiança média} a partir do cache gerado por main()."""
    with open(caminho, newline="", encoding="utf-8") as f:
        return {linha["file"]: float(linha["mean_confidence"]) for linha in csv.DictReader(f)}


def main():
    with open(RAIZ / "data" / "documents.csv", newline="", encoding="utf-8") as f:
        arquivos = [d["file"] for d in csv.DictReader(f)]
    versao = versao_tesseract()
    destino = ARQUIVO_CONFIANCAS
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, lineterminator="\n", fieldnames=[
            "file", "mean_confidence", "words", "tesseract_version", "lang", "config"])
        escritor.writeheader()
        for i, arquivo in enumerate(arquivos, 1):
            resultado = confianca_media(RAIZ / "data" / "images" / arquivo)
            escritor.writerow({"file": arquivo, **resultado, "tesseract_version": versao,
                               "lang": IDIOMA, "config": CONFIG_TESSERACT})
            print(f"[{i}/{len(arquivos)}] {arquivo}: {resultado['mean_confidence']} ({resultado['words']} palavras)",
                  flush=True)
    print(f"Gravado: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
