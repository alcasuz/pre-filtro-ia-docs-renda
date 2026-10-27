"""Testes unitários de cada regra (core/rules), com as bordas de rules.md."""

from datetime import date
from decimal import Decimal

import pytest

from core.models import PASS, REJECT, REVIEW, Linha
from core.rules import (completeness, consistency, document_type, fraud, identification, income, legibility,
                        screen_capture, time_window)
from core.rules.name_similarity import normalizar, similaridade

from .helpers import CONFIG, CPF, cliente, d, documento_vazio, holerite, tres_meses


# ---------------------------------------------------------------------------
# R7: legibilidade
# ---------------------------------------------------------------------------
def leg(doc, falhas=0, cfg=CONFIG):
    return legibility.avaliar(doc, cfg, falhas)


def test_documento_legivel_passa():
    r = leg(holerite())
    assert (r.status, r.reason) == (PASS, None)


@pytest.mark.parametrize("palavras", [0, None])
def test_ocr_sem_palavras_e_llm_sem_nada_e_ilegivel(palavras):
    # N12: imagem desfocada; None = OCR indisponível conta como zero palavras.
    r = leg(documento_vazio(tipo="payslip", palavras=palavras))
    assert (r.status, r.reason, r.details["criterion"]) == (REJECT, "illegible", "ocr_and_llm_empty")


def test_ocr_sem_palavras_mas_llm_leu_e_legivel():
    # Ex.: foto cortada ou girada em que o Tesseract não lê nada, mas o LLM lê.
    assert leg(holerite(palavras=0)).status == PASS


@pytest.mark.parametrize("campo, kwargs", [
    ("pay_period", {"periodo": "2026-09"}),
    ("name_on_doc", {"nome": "OTÁVIO OLIVEIRA ARAÚJO"}),
    ("cpf_on_doc", {"cpf": "782.943.622-39"}),
    ("total_earnings", {"totais": ("3000.00", None, None)}),
    ("net_pay", {"totais": (None, None, "2750.00")}),
    ("earnings_lines", {"linhas": [Linha("SALÁRIO BASE", Decimal("3000.00"), True)]}),
])
def test_um_campo_extraido_basta_para_nao_ser_ilegivel_pelo_ocr(campo, kwargs):
    vazio = dict(periodo=None, nome=None, cpf=None, totais=(None, None, None), linhas=[], palavras=0)
    assert leg(holerite(**{**vazio, **kwargs})).status == PASS


def test_ocr_com_palavras_e_llm_sem_nada_e_legivel():
    # N01: conta de luz lida pelo OCR; o LLM devolve other com tudo nulo (decide o tipo, R1).
    assert leg(documento_vazio(palavras=120)).status == PASS


@pytest.mark.parametrize("cpf_doc", ["816.425.287-26", "782.943.622-38", "782.943.622", "111.111.111-11"])
def test_cpf_com_digitos_invalidos_e_ilegivel(cpf_doc):
    # Leitura errada do CPF (ex.: foto tremida), não outro titular.
    r = leg(holerite(cpf=cpf_doc))
    assert (r.status, r.reason, r.details["criterion"]) == (REJECT, "illegible", "cpf_check_digits")


@pytest.mark.parametrize("cpf_doc", ["782.943.622-39", "529.982.247-25", None, ""])
def test_cpf_valido_ou_ausente_nao_afeta_a_legibilidade(cpf_doc):
    # Um CPF válido de outra pessoa é cpf_mismatch (R2), não ilegível.
    assert leg(holerite(cpf=cpf_doc)).status == PASS


@pytest.mark.parametrize("periodo", ["2020-08", "2027-11", "2026-01", None, "set/2026"])
def test_competencia_nao_e_criterio_de_legibilidade(periodo):
    # Competência distante, ausente ou mal formatada fica para a R3 (período) e a R8 (incompleto).
    assert leg(holerite(periodo=periodo)).status == PASS


@pytest.mark.parametrize("doc", [
    documento_vazio(tipo="payslip", palavras=0),
    holerite(cpf="782.943.622-38"),
], ids=["ocr_e_llm_vazios", "cpf_invalido"])
@pytest.mark.parametrize("falhas_anteriores, status", [(0, REJECT), (1, REJECT), (2, REVIEW), (5, REVIEW)])
def test_os_dois_criterios_usam_o_mesmo_contador(doc, falhas_anteriores, status):
    r = leg(doc, falhas_anteriores)
    assert r.status == status
    if status == REVIEW:
        assert r.reason == "too_many_attempts"


def test_documento_legivel_com_falhas_anteriores_passa():
    assert leg(holerite(), 2).status == PASS


def test_numero_de_tentativas_vem_da_configuracao():
    from dataclasses import replace
    r = leg(holerite(cpf="782.943.622-38"), 2, replace(CONFIG, max_legibility_attempts=5))
    assert r.reason == "illegible"


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
# Documento incompleto
# ---------------------------------------------------------------------------

def test_holerite_completo_passa():
    assert completeness.avaliar(holerite(), CONFIG).status == PASS


@pytest.mark.parametrize("faltando, kwargs", [
    ("pay_period", {"periodo": None}),
    ("total_earnings", {"totais": (None, "250.00", "2750.00")}),
    ("total_deductions", {"totais": ("3000.00", None, "2750.00")}),
    ("net_pay", {"totais": ("3000.00", "250.00", None)}),
    ("earnings_lines", {"linhas": []}),
])
def test_cada_campo_obrigatorio_faltando_reprova(faltando, kwargs):
    r = completeness.avaliar(holerite(**kwargs), CONFIG)
    assert (r.status, r.reason, r.details["missing"]) == (REJECT, "incomplete_document", [faltando])


def test_competencia_vazia_conta_como_faltando():
    assert completeness.avaliar(holerite(periodo=""), CONFIG).reason == "incomplete_document"


def test_nome_e_cpf_ausentes_nao_sao_desta_regra():
    assert completeness.avaliar(holerite(nome=None, cpf=None), CONFIG).status == PASS


def test_lista_todos_os_campos_faltando():
    r = completeness.avaliar(holerite(totais=(None, None, None), linhas=[]), CONFIG)
    assert r.details["missing"] == ["total_earnings", "total_deductions", "net_pay", "earnings_lines"]


@pytest.mark.parametrize("falhas_anteriores, status, motivo", [
    (0, REJECT, "incomplete_document"),
    (1, REJECT, "incomplete_document"),
    (2, REVIEW, "too_many_attempts"),
])
def test_incompleto_usa_o_contador_de_tentativas(falhas_anteriores, status, motivo):
    r = completeness.avaliar(holerite(linhas=[]), CONFIG, falhas_anteriores)
    assert (r.status, r.reason) == (status, motivo)


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
