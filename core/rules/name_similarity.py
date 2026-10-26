"""Fórmulas de similaridade de nome (R2), todas de 0 a 1 sobre nomes normalizados.

A fórmula usada pelo motor é escolhida em config/default_rules.yaml (name_similarity).
"""

import difflib
import unicodedata

from rapidfuzz import fuzz


# Abreviações de sufixo expandidas antes da comparação ("JR" e "JUNIOR" são o mesmo nome).
SUFIXOS = {"JR": "JUNIOR", "JR.": "JUNIOR"}


def normalizar(nome):
    """Maiúsculas, sem acentos, espaços únicos e sufixos abreviados expandidos (R2)."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", nome) if not unicodedata.combining(c))
    return " ".join(SUFIXOS.get(palavra, palavra) for palavra in sem_acento.upper().split())


FORMULAS = {
    "difflib_ratio": lambda a, b: difflib.SequenceMatcher(None, a, b).ratio(),
    "rapidfuzz_ratio": lambda a, b: fuzz.ratio(a, b) / 100,
    "token_sort_ratio": lambda a, b: fuzz.token_sort_ratio(a, b) / 100,
    "token_set_ratio": lambda a, b: fuzz.token_set_ratio(a, b) / 100,
}


def similaridade(nome_doc, nome_cadastro, formula):
    return FORMULAS[formula](normalizar(nome_doc), normalizar(nome_cadastro))
