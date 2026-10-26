"""Converte a extração do LLM (JSON do cache) em Documento para o motor."""

from decimal import Decimal

from .models import Documento, Linha


def valor(numero):
    """Número do JSON -> Decimal em centavos; None continua None."""
    if numero is None:
        return None
    return Decimal(str(numero)).quantize(Decimal("0.01"))


def documento_da_extracao(file, extracao, legible=None):
    return Documento(
        file=file,
        document_type=extracao["document_type"],
        pay_period=extracao["pay_period"],
        name_on_doc=extracao["name_on_doc"],
        cpf_on_doc=extracao["cpf_on_doc"],
        total_earnings=valor(extracao["total_earnings"]),
        total_deductions=valor(extracao["total_deductions"]),
        net_pay=valor(extracao["net_pay"]),
        earnings_lines=[Linha(l["description"], valor(l["amount"]), bool(l["counts_as_income"]))
                        for l in extracao["earnings_lines"]],
        fraud_suspected=bool(extracao["fraud_suspected"]),
        fraud_reason=extracao["fraud_reason"],
        legible=legible,
    )
