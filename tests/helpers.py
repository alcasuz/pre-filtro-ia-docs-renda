"""Construtores curtos de Documento e Cliente para os testes."""

from datetime import date
from decimal import Decimal

from core.config import ConfigRegras
from core.models import Cliente, Documento, Linha

CPF = "78294362239"  # CPF fictício com dígitos verificadores válidos

CONFIG = ConfigRegras(version=1, income_multiplier=Decimal("3"), consistency_tolerance=Decimal("100"),
                      name_ok=0.95, name_review=0.50, window_months=4, required_months=3,
                      max_legibility_attempts=3,
                      name_similarity="token_sort_ratio")


def d(valor):
    return Decimal(valor)


def cliente(nome="Otávio Oliveira Araújo", cpf=CPF, parcela="1000.00", analise=date(2026, 10, 15)):
    return Cliente("T01", nome, cpf, d(parcela), analise)


def holerite(periodo="2026-09", salario="3000.00", tipo="payslip", arquivo=None, linhas=None,
             nome="OTÁVIO OLIVEIRA ARAÚJO", cpf="782.943.622-39", totais=("3000.00", "250.00", "2750.00"),
             fraude=False, motivo_fraude=None, palavras=120, captura="original_file"):
    if linhas is None:
        linhas = [Linha("SALÁRIO BASE", d(salario), True)]
    return Documento(
        file=arquivo or f"T01_{periodo}_{tipo}.png", document_type=tipo, pay_period=periodo,
        name_on_doc=nome, cpf_on_doc=cpf,
        total_earnings=None if totais[0] is None else d(totais[0]),
        total_deductions=None if totais[1] is None else d(totais[1]),
        net_pay=None if totais[2] is None else d(totais[2]),
        earnings_lines=linhas, fraud_suspected=fraude, fraud_reason=motivo_fraude, ocr_words=palavras,
        capture_type=captura,
    )


def documento_vazio(tipo="other", arquivo="T01_borrado.png", palavras=0):
    """O que o LLM devolve para uma imagem desfocada (ou um documento que não é holerite): tudo nulo."""
    return Documento(file=arquivo, document_type=tipo, pay_period=None, name_on_doc=None,
                     cpf_on_doc=None, total_earnings=None, total_deductions=None, net_pay=None,
                     earnings_lines=[], fraud_suspected=False, ocr_words=palavras)


def tres_meses(salario="3000.00", meses=("2026-07", "2026-08", "2026-09"), **kwargs):
    return [holerite(periodo=m, salario=salario, **kwargs) for m in meses]
