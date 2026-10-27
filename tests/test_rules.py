"""Testes unitários de cada regra (core/rules), com as bordas de rules.md."""

from datetime import date
from decimal import Decimal

import pytest

from core.models import PASS, REJECT, REVIEW, Linha
from core.rules import (consistency, document_type, fraud, identification, income, legibility, screen_capture,
                        time_window)
from core.rules.name_similarity import normalizar, similaridade

from .helpers import CONFIG, CPF, cliente, d, documento_vazio, holerite, tres_meses


# ---------------------------------------------------------------------------
# R7: legibilidade
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("confianca, status", [
    (0.0, REJECT),      # N12: nenhuma palavra reconhecida
    (29.99, REJECT),
    (30.0, PASS),       # borda: exatamente no limite é legível
    (30.01, PASS),
    (62.91, PASS),      # pior holerite legível da base (A16 torto)
])
def test_legibilidade_pela_confianca_do_ocr(confianca, status):
    r = legibility.avaliar(holerite(ocr=confianca), CONFIG)
    assert r.status == status
    assert r.reason == (None if status == PASS else "illegible")
    assert r.details["ocr_confidence"] == confianca


def test_documento_nao_holerite_com_tudo_nulo_mas_legivel_passa_na_legibilidade():
    # Ex.: N01, a conta de luz: o LLM devolve other com tudo nulo, mas o OCR lê bem.
    assert legibility.avaliar(documento_vazio(ocr=84.86), CONFIG).status == PASS


def test_limite_de_legibilidade_vem_da_configuracao():
    from dataclasses import replace
    r = legibility.avaliar(holerite(ocr=50.0), replace(CONFIG, legibility_min_confidence=60.0))
    assert r.status == REJECT


def test_ocr_sem_confianca_e_falha_de_legibilidade():
    r = legibility.avaliar(holerite(ocr=None), CONFIG)
    assert (r.status, r.reason, r.details["criterion"]) == (REJECT, "illegible", "ocr_unavailable")


@pytest.mark.parametrize("falhas_anteriores, status, motivo", [
    (0, REJECT, "illegible"),
    (1, REJECT, "illegible"),
    (2, REVIEW, "too_many_attempts"),   # borda: com 2 falhas anteriores, a nova falha vai para revisão
    (5, REVIEW, "too_many_attempts"),
])
def test_falhas_anteriores_de_legibilidade_no_pedido(falhas_anteriores, status, motivo):
    r = legibility.avaliar(holerite(ocr=12.0), CONFIG, falhas_anteriores)
    assert (r.status, r.reason, r.details["prior_legibility_failures"]) == (status, motivo, falhas_anteriores)


def test_padrao_sem_falhas_anteriores():
    assert legibility.avaliar(holerite(ocr=12.0), CONFIG).reason == "illegible"


def test_falhas_anteriores_valem_tambem_quando_o_ocr_nao_le():
    r = legibility.avaliar(holerite(ocr=None), CONFIG, 2)
    assert (r.status, r.reason) == (REVIEW, "too_many_attempts")


def test_documento_legivel_com_falhas_anteriores_passa():
    assert legibility.avaliar(holerite(ocr=80.0), CONFIG, 2).status == PASS


def test_numero_de_tentativas_vem_da_configuracao():
    from dataclasses import replace
    r = legibility.avaliar(holerite(ocr=12.0), replace(CONFIG, max_legibility_attempts=5), 2)
    assert r.reason == "illegible"


@pytest.mark.parametrize("cpf_doc", ["816.425.287-26", "782.943.622-38", "782.943.622", "111.111.111-11"])
def test_cpf_com_digitos_invalidos_e_ilegivel(cpf_doc):
    # Leitura errada do CPF (ex.: foto tremida), não outro titular: OCR alto não salva.
    r = legibility.avaliar(holerite(cpf=cpf_doc, ocr=88.0), CONFIG)
    assert (r.status, r.reason, r.details["criterion"]) == (REJECT, "illegible", "cpf_check_digits")


@pytest.mark.parametrize("cpf_doc", ["782.943.622-39", "529.982.247-25", None, ""])
def test_cpf_valido_ou_ausente_nao_afeta_a_legibilidade(cpf_doc):
    # Um CPF válido de outra pessoa é cpf_mismatch (R2), não ilegível.
    assert legibility.avaliar(holerite(cpf=cpf_doc), CONFIG).status == PASS


def test_cpf_invalido_tambem_usa_o_fallback_de_tentativas():
    r = legibility.avaliar(holerite(cpf="782.943.622-38"), CONFIG, 2)
    assert (r.status, r.reason) == (REVIEW, "too_many_attempts")


# ---------------------------------------------------------------------------
# R1: tipo de documento
# ---------------------------------------------------------------------------

def test_tipo_so_documentos_nao_aceitos_reprova():
    r = document_type.avaliar([holerite(tipo="other")])
    assert (r.status, r.reason) == (REJECT, "type_not_accepted")


def test_tipo_extrato_extra_junto_com_holerites_e_ignorado():
    extrato = holerite(tipo="other", arquivo="T01_extrato.png")
    r = document_type.avaliar(tres_meses() + [extrato])
    assert r.status == PASS and r.details["ignored"] == ["T01_extrato.png"]


@pytest.mark.parametrize("tipo", ["payslip", "payslip_vacation", "payslip_13th"])
def test_tipos_aceitos(tipo):
    assert document_type.avaliar([holerite(tipo=tipo)]).status == PASS


# ---------------------------------------------------------------------------
# R1: captura de tela
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("captura, status, motivo", [
    ("original_file", PASS, None),
    ("photo_of_paper", PASS, None),
    ("photo_of_screen", REJECT, "screen_capture"),
    ("screenshot", REJECT, "screen_capture"),
])
def test_captura_de_tela_reprova(captura, status, motivo):
    r = screen_capture.avaliar(holerite(captura=captura))
    assert (r.status, r.reason, r.details["capture_type"]) == (status, motivo, captura)


def test_extracao_sem_capture_type_nao_e_avaliada():
    # Extrações dos prompts v1 e v2 não têm o campo.
    r = screen_capture.avaliar(holerite(captura=None))
    assert (r.status, r.details["evaluated"]) == (PASS, False)


# ---------------------------------------------------------------------------
# R2: titular (CPF)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cpf_doc", ["782.943.622-39", "78294362239", "782 943 622 39", "782.943.622/39"])
def test_cpf_em_formatos_diferentes_confere(cpf_doc):
    r = identification.avaliar(holerite(cpf=cpf_doc), cliente(), CONFIG)
    assert (r.status, r.details["basis"], r.details["cpf_normalized"]) == (PASS, "cpf", CPF)


def test_cpf_diferente_reprova_mesmo_com_nome_igual():
    r = identification.avaliar(holerite(cpf="529.982.247-25"), cliente(), CONFIG)
    assert (r.status, r.reason) == (REJECT, "cpf_mismatch")


def test_cpf_confere_e_nome_nao_e_avaliado():
    r = identification.avaliar(holerite(nome="OUTRA PESSOA QUALQUER"), cliente(), CONFIG)
    assert r.status == PASS and "similarity" not in r.details


def test_sem_cpf_e_sem_nome_reprova():
    r = identification.avaliar(holerite(nome=None, cpf=None), cliente(), CONFIG)
    assert (r.status, r.reason) == (REJECT, "id_missing")


def test_nome_em_branco_conta_como_ausente():
    r = identification.avaliar(holerite(nome="   ", cpf=""), cliente(), CONFIG)
    assert r.reason == "id_missing"


@pytest.mark.parametrize("cpf, valido", [
    ("78294362239", True), ("52998224725", True),
    ("78294362238", False), ("11111111111", False), ("7829436223", False),
])
def test_digitos_verificadores_do_cpf(cpf, valido):
    assert identification.cpf_valido(cpf) is valido


# ---------------------------------------------------------------------------
# R2: titular (similaridade de nome, token_sort_ratio)
# ---------------------------------------------------------------------------

FAIXA = {PASS: "aprovado", REVIEW: "revisão", REJECT: "reprova"}

CASOS_NOME = [
    # (descrição, cadastro, nome no documento, faixas aceitas)
    ("acento e maiúsculas (A08)", "Marcos Conceição Rezende", "MARCOS CONCEICAO REZENDE", {PASS}),
    ("abreviado (N14)", "Larissa Magalhães Pinto Cardoso", "LARISSA M. P. CARDOSO", {REVIEW}),
    ("outra pessoa (N05)", "Inês Fontes Quintana", "HENRIQUE DUARTE MEDEIROS", {REJECT}),
    ("ordem invertida", "Marcos Conceição Rezende", "REZENDE MARCOS CONCEICAO", {PASS}),
    ("pai × filho (Filho)", "José Carlos Ferreira", "JOSE CARLOS FERREIRA FILHO", {REVIEW}),
    ("pai × filho (Junior)", "Carlos Alberto Souza", "CARLOS ALBERTO SOUZA JUNIOR", {REVIEW}),
    ("filho Junior × pai", "Carlos Alberto Souza Junior", "CARLOS ALBERTO SOUZA", {REVIEW}),
    ("pai × filho (Jr)", "Carlos Alberto Souza", "CARLOS ALBERTO SOUZA JR", {REVIEW}),
    ("irmãos", "Ana Paula Souza Lima", "PEDRO HENRIQUE SOUZA LIMA", {REVIEW}),
    ("irmãos, nomes curtos", "Ana Souza Lima", "BIA SOUZA LIMA", {REVIEW}),
    ("Jr abreviado → Junior", "Carlos Alberto Souza Junior", "CARLOS ALBERTO SOUZA JR", {PASS}),
    ("Jr. abreviado → Junior", "Carlos Alberto Souza Junior", "CARLOS ALBERTO SOUZA JR.", {PASS}),
    ("casamento: só o 1º nome igual", "Fernanda Oliveira Costa", "FERNANDA RIBEIRO MACHADO", {REVIEW, REJECT}),
    ("casamento: 1º nome + 1 sobrenome", "Fernanda Oliveira Costa", "FERNANDA OLIVEIRA MACHADO", {REVIEW, REJECT}),
    ("nome curto contido em outro", "Maria Silva", "MARIA APARECIDA SILVA SOUZA", {REVIEW}),
]


@pytest.mark.parametrize("descricao, cadastro, nome_doc, faixas", CASOS_NOME, ids=[c[0] for c in CASOS_NOME])
def test_similaridade_de_nome_cai_na_faixa_esperada(descricao, cadastro, nome_doc, faixas):
    r = identification.avaliar(holerite(nome=nome_doc, cpf=None), cliente(nome=cadastro), CONFIG)
    assert r.status in faixas, (f"{descricao}: nota {r.details['similarity']} caiu em {FAIXA[r.status]}, "
                                f"esperado {[FAIXA[f] for f in faixas]}")


def test_nome_curto_contido_em_outro_nunca_aprova():
    nota = similaridade("MARIA APARECIDA SILVA SOUZA", "Maria Silva", "token_sort_ratio")
    assert nota < CONFIG.name_ok


def test_limites_de_similaridade_sao_inclusivos(monkeypatch):
    for nota, esperado in ((0.95, PASS), (0.9499, REVIEW), (0.50, REVIEW), (0.4999, REJECT)):
        monkeypatch.setattr(identification, "similaridade", lambda *a, n=nota: n)
        r = identification.avaliar(holerite(cpf=None), cliente(), CONFIG)
        assert r.status == esperado, f"nota {nota}"


def test_normalizacao_do_nome():
    assert normalizar("  Inês   da  Conceição jr. ") == "INES DA CONCEICAO JUNIOR"


# ---------------------------------------------------------------------------
# R3: período
# ---------------------------------------------------------------------------

def test_janela_sao_os_4_meses_anteriores_sem_o_mes_da_analise():
    assert sorted(time_window.janela(date(2026, 10, 15), 4)) == ["2026-06", "2026-07", "2026-08", "2026-09"]


def test_janela_atravessa_a_virada_do_ano():
    assert sorted(time_window.janela(date(2027, 1, 5), 4)) == ["2026-09", "2026-10", "2026-11", "2026-12"]


def test_tres_meses_consecutivos_na_janela_passa():
    r = time_window.avaliar(tres_meses(), cliente(), CONFIG)
    assert r.status == PASS and r.details["months_used"] == ["2026-07", "2026-08", "2026-09"]


def test_seis_meses_usa_os_tres_mais_recentes():
    docs = tres_meses(meses=("2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"))
    r = time_window.avaliar(docs, cliente(), CONFIG)
    assert r.status == PASS and r.details["months_used"] == ["2026-07", "2026-08", "2026-09"]


def test_fora_da_janela_reprova():
    r = time_window.avaliar(tres_meses(meses=("2026-01", "2026-02", "2026-03")), cliente(), CONFIG)
    assert r.reason == "outside_window"


def test_mes_da_analise_esta_fora_da_janela():
    r = time_window.avaliar(tres_meses(meses=("2026-08", "2026-09", "2026-10")), cliente(), CONFIG)
    assert r.reason == "outside_window"


def test_mes_faltando_no_meio_reprova():
    r = time_window.avaliar(tres_meses(meses=("2026-06", "2026-07", "2026-09")), cliente(), CONFIG)
    assert r.reason == "non_consecutive_months"


def test_menos_de_tres_meses_reprova_como_fora_do_periodo():
    r = time_window.avaliar(tres_meses(meses=("2026-08", "2026-09")), cliente(), CONFIG)
    assert r.reason == "outside_window"


def test_holerite_de_13o_nao_forma_mes():
    docs = tres_meses(meses=("2026-08", "2026-09")) + [holerite(periodo="2026-07", tipo="payslip_13th")]
    assert time_window.avaliar(docs, cliente(), CONFIG).reason == "outside_window"


def test_ferias_e_mensal_da_mesma_competencia_formam_um_mes():
    docs = tres_meses() + [holerite(periodo="2026-08", tipo="payslip_vacation")]
    assert time_window.avaliar(docs, cliente(), CONFIG).details["months_used"] == ["2026-07", "2026-08", "2026-09"]


def test_competencia_em_formato_invalido_e_ignorada():
    docs = tres_meses(meses=("2026-07", "2026-08")) + [holerite(periodo="setembro/26")]
    assert time_window.avaliar(docs, cliente(), CONFIG).reason == "outside_window"


# ---------------------------------------------------------------------------
# R5 + R6: renda
# ---------------------------------------------------------------------------

MESES = ["2026-07", "2026-08", "2026-09"]


def test_renda_exatamente_3x_aprova():
    r = income.avaliar(tres_meses(salario="3000.00"), MESES, cliente(parcela="1000.00"), CONFIG)
    assert (r.status, r.details["valid_income"]) == (PASS, d("3000.00"))


def test_renda_um_centavo_abaixo_de_3x_reprova():
    docs = [holerite(periodo="2026-07", salario="2999.99")] + tres_meses(meses=MESES[1:])
    r = income.avaliar(docs, MESES, cliente(parcela="1000.00"), CONFIG)
    assert (r.status, r.reason) == (REJECT, "insufficient_income")


def test_comparacao_nao_arredonda_a_media_antes():
    # Soma 8999.99: a média arredondada daria 3000.00, mas a renda real está abaixo de 3x.
    docs = [holerite(periodo="2026-07", salario="2999.99")] + tres_meses(meses=MESES[1:])
    r = income.avaliar(docs, MESES, cliente(parcela="1000.00"), CONFIG)
    assert r.details["valid_income"] == d("3000.00") and r.status == REJECT


def test_hora_extra_e_um_terco_de_ferias_nao_contam():
    linhas = [Linha("SALÁRIO BASE", d("2900.00"), True), Linha("HORAS EXTRAS 50%", d("500.00"), False),
              Linha("1/3 CONSTITUCIONAL DE FÉRIAS", d("300.00"), False)]
    docs = [holerite(periodo=m, linhas=linhas) for m in MESES]
    r = income.avaliar(docs, MESES, cliente(parcela="1000.00"), CONFIG)
    assert (r.status, r.details["valid_income"]) == (REJECT, d("2900.00"))


def test_ferias_somam_ao_mensal_da_mesma_competencia():
    ferias = holerite(periodo="2026-08", tipo="payslip_vacation",
                      linhas=[Linha("FÉRIAS (10 DIAS)", d("1000.00"), True)])
    docs = [holerite(periodo="2026-07"), holerite(periodo="2026-08", salario="2000.00"),
            ferias, holerite(periodo="2026-09")]
    r = income.avaliar(docs, MESES, cliente(), CONFIG)
    assert r.details["monthly_income"]["2026-08"] == d("3000.00") and r.status == PASS


def test_holerite_de_13o_nao_entra_na_renda():
    docs = tres_meses(salario="2000.00") + [holerite(periodo="2026-09", tipo="payslip_13th", salario="5000.00")]
    r = income.avaliar(docs, MESES, cliente(), CONFIG)
    assert r.details["valid_income"] == d("2000.00")


def test_multiplicador_vem_da_configuracao():
    from dataclasses import replace
    r = income.avaliar(tres_meses(salario="3000.00"), MESES, cliente(parcela="1000.00"),
                       replace(CONFIG, income_multiplier=Decimal("3.5")))
    assert r.status == REJECT


# ---------------------------------------------------------------------------
# R4: consistência
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("liquido, esperado", [
    ("2750.00", PASS),   # diferença 0
    ("2650.00", PASS),   # diferença exatamente R$ 100: dentro da tolerância
    ("2850.00", PASS),   # R$ 100 na outra direção
    ("2649.99", REVIEW),  # R$ 100,01
    ("2850.01", REVIEW),
])
def test_tolerancia_de_100_reais(liquido, esperado):
    r = consistency.avaliar(holerite(totais=("3000.00", "250.00", liquido)), CONFIG)
    assert r.status == esperado
    if esperado == REVIEW:
        assert r.reason == "suspected_fraud"


def test_consistencia_com_total_ausente_nao_e_avaliada():
    r = consistency.avaliar(holerite(totais=("3000.00", None, "2750.00")), CONFIG)
    assert r.status == PASS and r.details["evaluated"] is False


# ---------------------------------------------------------------------------
# Fraude (R7: injection ou sinais de edição)
# ---------------------------------------------------------------------------

def test_fraude_sinalizada_vai_para_revisao():
    r = fraud.avaliar(holerite(fraude=True, motivo_fraude="texto pedindo aprovação"))
    assert (r.status, r.reason, r.details["fraud_reason"]) == (REVIEW, "suspected_fraud", "texto pedindo aprovação")


def test_sem_fraude_passa():
    assert fraud.avaliar(holerite()).status == PASS
