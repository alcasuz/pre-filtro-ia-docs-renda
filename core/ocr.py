"""OCR com o Tesseract: confiança média das palavras de uma imagem (sinal de legibilidade da R7).

A confiança média é a média simples da confiança (0 a 100) de cada palavra que o
Tesseract reconheceu, ignorando as caixas sem texto (conf = -1). Imagem sem
nenhuma palavra reconhecida tem confiança 0.

A confiança depende da versão do Tesseract e do modelo de idioma; ambos são
registrados junto com o resultado, porque o limite de legibilidade só vale para
a combinação em que foi calibrado.

Uso:
  .venv/bin/python -m core.ocr            # base v1 (data/documents.csv) -> cache/ocr/confidence.csv
  .venv/bin/python -m core.ocr --set v2   # fotos v2 (data/photos.csv)   -> cache/ocr/confidence_v2.csv
"""

import argparse
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
        return confianca_da_imagem(imagem, idioma)


def confianca_da_imagem(imagem, idioma=IDIOMA):
    """Como confianca_media, para uma imagem já aberta (ex.: girada)."""
    dados = pytesseract.image_to_data(imagem, lang=idioma, config=CONFIG_TESSERACT,
                                      output_type=pytesseract.Output.DICT)
    confiancas = [float(c) for c, texto in zip(dados["conf"], dados["text"])
                  if float(c) >= 0 and texto.strip()]
    media = sum(confiancas) / len(confiancas) if confiancas else 0.0
    return {"mean_confidence": round(media, 2), "words": len(confiancas)}


ARQUIVO_CONFIANCAS = RAIZ / "cache" / "ocr" / "confidence.csv"
CONJUNTOS = {
    # conjunto: (lista de arquivos, pasta das imagens, arquivo de saída)
    "v1": (RAIZ / "data" / "documents.csv", RAIZ / "data" / "images", ARQUIVO_CONFIANCAS),
    "v2": (RAIZ / "data" / "photos.csv", RAIZ / "data" / "images" / "v2",
           RAIZ / "cache" / "ocr" / "confidence_v2.csv"),
}


def carregar_confiancas(caminho=ARQUIVO_CONFIANCAS):
    """{arquivo: confiança média} a partir do cache gerado por main()."""
    with open(caminho, newline="", encoding="utf-8") as f:
        return {linha["file"]: float(linha["mean_confidence"]) for linha in csv.DictReader(f)}


def main():
    parser = argparse.ArgumentParser(description="Confiança média do OCR para cada imagem do conjunto.")
    parser.add_argument("--set", choices=sorted(CONJUNTOS), default="v1")
    args = parser.parse_args()
    lista, pasta, destino = CONJUNTOS[args.set]
    with open(lista, newline="", encoding="utf-8") as f:
        arquivos = [d["file"] for d in csv.DictReader(f)]
    versao = versao_tesseract()
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, lineterminator="\n", fieldnames=[
            "file", "mean_confidence", "words", "tesseract_version", "lang", "config"])
        escritor.writeheader()
        for i, arquivo in enumerate(arquivos, 1):
            resultado = confianca_media(pasta / arquivo)
            escritor.writerow({"file": arquivo, **resultado, "tesseract_version": versao,
                               "lang": IDIOMA, "config": CONFIG_TESSERACT})
            print(f"[{i}/{len(arquivos)}] {arquivo}: {resultado['mean_confidence']} ({resultado['words']} palavras)",
                  flush=True)
    print(f"Gravado: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
