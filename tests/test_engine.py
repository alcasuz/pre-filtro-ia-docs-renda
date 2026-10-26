"""Testes do motor: ordem das regras, precedência e saída completa."""

from core.engine import decidir
from core.models import APPROVE, REJECT, REVIEW

from .helpers import CONFIG, cliente, d, documento_vazio, holerite, tres_meses


def test_caminho_feliz_aprova():
    r = decidir(cliente(), tres_meses(), CONFIG)
    assert (r.decision, r.main_reason, r.reasons) == (APPROVE, None, [])
    assert r.valid_income == d("3000.00") and r.months_used == ["2026-07", "2026-08", "2026-09"]
    assert r.fraud_flag is False


def test_reprova_vence_revisao_e_a_fraude_fica_registrada():
    docs = tres_meses(salario="2000.00")
    docs[2] = holerite(periodo="2026-09", salario="2000.00", fraude=True, motivo_fraude="injection")
    r = decidir(cliente(), docs, CONFIG)
    assert (r.decision, r.main_reason) == (REJECT, "insufficient_income")
    assert r.reasons == ["insufficient_income", "suspected_fraud"]
    assert r.fraud_flag is True and "injection" in r.fraud_reasons[0]


def test_revisao_vence_aprovacao():
    docs = tres_meses()
    docs[0] = holerite(periodo="2026-07", totais=("3000.00", "250.00", "3000.00"))
    r = decidir(cliente(), docs, CONFIG)
    assert (r.decision, r.main_reason) == (REVIEW, "suspected_fraud")
    assert r.fraud_flag is True


def test_legibilidade_vem_antes_do_tipo():
    # O LLM classifica a imagem desfocada como other: o motivo deve ser ilegível, não tipo.
    docs = tres_meses(meses=("2026-07", "2026-09")) + [documento_vazio()]
    r = decidir(cliente(), docs, CONFIG)
    assert (r.decision, r.main_reason) == (REJECT, "illegible")
    assert "type_not_accepted" not in r.reasons


def test_so_documento_nao_aceito_reprova_por_tipo_sem_motivos_de_periodo_ou_renda():
    r = decidir(cliente(), [holerite(tipo="other", periodo="2026-09")], CONFIG)
    assert (r.decision, r.main_reason, r.reasons) == (REJECT, "type_not_accepted", ["type_not_accepted"])
    assert r.valid_income is None and r.months_used == []


def test_extrato_extra_e_ignorado_quando_os_holerites_sao_validos():
    extrato = holerite(tipo="other", periodo="2026-09", arquivo="T01_extrato.png", linhas=[])
    r = decidir(cliente(), tres_meses() + [extrato], CONFIG)
    assert r.decision == APPROVE


def test_motivos_seguem_a_ordem_das_regras():
    docs = tres_meses(salario="1000.00", meses=("2026-01", "2026-02", "2026-03"), cpf="529.982.247-25")
    r = decidir(cliente(), docs, CONFIG)
    assert r.reasons == ["cpf_mismatch", "outside_window", "insufficient_income"]
    assert r.main_reason == "cpf_mismatch"


def test_renda_e_registrada_mesmo_quando_reprovado_por_outra_regra():
    docs = tres_meses(meses=("2026-06", "2026-07", "2026-09"))
    r = decidir(cliente(), docs, CONFIG)
    assert r.main_reason == "non_consecutive_months" and r.valid_income == d("3000.00")


def test_revisao_por_nome_antes_da_revisao_por_fraude():
    docs = tres_meses(nome="OTAVIO O. ARAUJO", cpf=None)
    docs[0] = holerite(periodo="2026-07", nome="OTAVIO O. ARAUJO", cpf=None, fraude=True)
    r = decidir(cliente(), docs, CONFIG)
    assert (r.decision, r.main_reason) == (REVIEW, "name_review")
    assert r.reasons == ["name_review", "suspected_fraud"]
