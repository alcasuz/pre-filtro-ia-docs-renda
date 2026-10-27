"""R2 (titular): o documento precisa ter o CPF ou o nome do cliente.

Com CPF: compara só os 11 dígitos com o cadastro (qualquer formato); igual
confirma o titular e o nome não é avaliado. Sem CPF: similaridade do nome com o
cadastro, com os limites name_ok e name_review da configuração. Um CPF com
dígitos verificadores inválidos não chega aqui: a legibilidade (R7) já o barrou
como leitura errada, para não virar cpf_mismatch.
"""

import re

from ..models import PASS, REJECT, REVIEW, ResultadoRegra
from .name_similarity import similaridade


def digito_mod11(digitos, pesos):
    resto = sum(d * p for d, p in zip(digitos, pesos)) % 11
    return 0 if resto < 2 else 11 - resto


def normalizar_cpf(cpf):
    return re.sub(r"\D", "", cpf or "")


def cpf_valido(cpf):
    if not re.fullmatch(r"\d{11}", cpf) or len(set(cpf)) == 1:
        return False
    d = [int(c) for c in cpf]
    return (d[9] == digito_mod11(d[:9], range(10, 1, -1))
            and d[10] == digito_mod11(d[:10], range(11, 1, -1)))


def avaliar(doc, cliente, config):
    def resultado(status, reason=None, **details):
        return ResultadoRegra(rule="identification", file=doc.file, status=status,
                              reason=reason, details=details)

    cpf_doc = normalizar_cpf(doc.cpf_on_doc)
    nome_doc = (doc.name_on_doc or "").strip()

    if cpf_doc:
        confere = cpf_doc == normalizar_cpf(cliente.cpf)
        return resultado(PASS if confere else REJECT, None if confere else "cpf_mismatch",
                         basis="cpf", cpf_normalized=cpf_doc, cpf_valid=cpf_valido(cpf_doc))
    if not nome_doc:
        return resultado(REJECT, "id_missing", basis="none")

    if config.name_similarity is None:
        raise ValueError("Fórmula de similaridade de nome não escolhida (name_similarity no YAML).")
    nota = similaridade(nome_doc, cliente.name, config.name_similarity)
    detalhes = {"basis": "name", "formula": config.name_similarity, "similarity": round(nota, 4)}
    if nota >= config.name_ok:
        return resultado(PASS, **detalhes)
    if nota >= config.name_review:
        return resultado(REVIEW, "name_review", **detalhes)
    return resultado(REJECT, "name_mismatch", **detalhes)
