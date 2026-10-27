"""Estruturas de dados compartilhadas pelo motor de regras, pelo eval e pelo front."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Optional

PASS, REJECT, REVIEW = "pass", "reject", "review"
APPROVE = "approve"

TIPOS_ACEITOS = ("payslip", "payslip_vacation", "payslip_13th")
# Como a imagem foi capturada (R1); as capturas de tela são reprovadas.
CAPTURAS_DE_TELA = ("photo_of_screen", "screenshot")


@dataclass
class Linha:
    description: str
    amount: Decimal
    counts_as_income: bool


@dataclass
class Documento:
    """Um documento como o motor o enxerga, venha do LLM (cache) ou do gabarito (oracle)."""

    file: str
    document_type: str
    pay_period: Optional[str]
    name_on_doc: Optional[str]
    cpf_on_doc: Optional[str]
    total_earnings: Optional[Decimal]
    total_deductions: Optional[Decimal]
    net_pay: Optional[Decimal]
    earnings_lines: list[Linha]
    fraud_suspected: bool
    fraud_reason: Optional[str] = None
    # Número de palavras que o OCR reconheceu, sinal de legibilidade da R7 (None = sem OCR).
    ocr_words: Optional[int] = None
    # original_file, photo_of_paper, photo_of_screen ou screenshot; None em extrações
    # anteriores ao prompt v3, que não informam a captura.
    capture_type: Optional[str] = None


@dataclass
class Cliente:
    applicant_id: str
    name: str
    cpf: str
    installment_amount: Decimal
    analysis_date: date


@dataclass
class ResultadoRegra:
    rule: str
    status: str
    reason: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    file: Optional[str] = None


@dataclass
class Decisao:
    decision: str
    main_reason: Optional[str]
    reasons: list[str]
    valid_income: Optional[Decimal]
    months_used: list[str]
    fraud_flag: bool
    fraud_reasons: list[str]
    results: list[ResultadoRegra]
