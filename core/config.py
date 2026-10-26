"""Carrega os parâmetros do motor de config/default_rules.yaml."""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Optional

import yaml

ARQUIVO_PADRAO = Path(__file__).resolve().parent.parent / "config" / "default_rules.yaml"


@dataclass(frozen=True)
class ConfigRegras:
    version: int
    income_multiplier: Decimal
    consistency_tolerance: Decimal
    name_ok: float
    name_review: float
    window_months: int
    required_months: int
    # Fórmula de similaridade de nome (core/rules/name_similarity.py); None até ser escolhida.
    name_similarity: Optional[str] = None


def carregar(caminho=ARQUIVO_PADRAO):
    dados = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
    return ConfigRegras(
        version=int(dados["version"]),
        income_multiplier=Decimal(str(dados["income_multiplier"])),
        consistency_tolerance=Decimal(str(dados["consistency_tolerance"])),
        name_ok=float(dados["name_ok"]),
        name_review=float(dados["name_review"]),
        window_months=int(dados["window_months"]),
        required_months=int(dados["required_months"]),
        name_similarity=dados.get("name_similarity"),
    )
