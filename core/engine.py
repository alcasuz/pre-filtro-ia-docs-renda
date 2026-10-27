"""Motor de regras: aplica as regras da v1 aos documentos de um cliente e decide.

Ordem (rules.md): legibilidade, tipo, captura de tela, documento incompleto,
titular, período, renda e, por fim, as revisões (consistência e fraude). Todas as regras rodam, sem parar na primeira
falha, para que a lista completa de motivos e a renda fiquem registradas mesmo
quando o cliente é reprovado. Decisão: qualquer reject vence qualquer review;
qualquer review vence approve. O motivo principal é o primeiro reject na ordem
das regras ou, sem reject, o primeiro review.

Quais documentos cada regra recebe:
- legibilidade: todos os documentos, pela confiança do OCR (Documento.ocr_confidence)
  e pelos dígitos verificadores do CPF lido;
- fraude: os legíveis;
- tipo: os legíveis; um documento de outro tipo junto com holerites é ignorado;
- captura de tela, documento incompleto, titular e consistência: os holerites legíveis;
- período e renda: todos os holerites, inclusive um ilegível cujos dados existam
  (modo oracle). Sem nenhum holerite, período e renda não são avaliados.

Contrato de entrada: o motor não guarda estado. Quem chama informa a
analysis_date (em Cliente) e prior_legibility_failures, quantas reprovações por
ilegibilidade ou documento incompleto o pedido já teve (padrão 0).

Documento escalado por tentativas (too_many_attempts, ilegível ou incompleto): os dados dele faltam no
período e na renda, que reprovariam o cliente por isso e anulariam o fallback
(reject vence review). Então, quando há um documento escalado, uma reprovação de
período ou renda vira revisão, com o motivo original mantido na lista. As outras
reprovações (tipo, captura de tela, titular) continuam valendo.
"""

from .models import APPROVE, PASS, REJECT, REVIEW, Decisao
from .rules import (completeness, consistency, document_type, fraud, identification, income, legibility,
                    screen_capture, time_window)

ORDEM_REGRAS = ["legibility", "document_type", "screen_capture", "completeness", "identification", "time_window",
                "income", "consistency", "fraud"]


def decidir(cliente, documentos, config, prior_legibility_failures=0):
    resultados = [legibility.avaliar(d, config, prior_legibility_failures) for d in documentos]
    ilegiveis = {r.file for r in resultados if r.status != PASS}
    legiveis = [d for d in documentos if d.file not in ilegiveis]

    resultados.append(document_type.avaliar(legiveis))
    holerites = [d for d in documentos if document_type.aceito(d)]
    holerites_legiveis = [d for d in holerites if d.file not in ilegiveis]

    resultados += [screen_capture.avaliar(d) for d in holerites_legiveis]
    resultados += [completeness.avaliar(d, config, prior_legibility_failures) for d in holerites_legiveis]
    escalados = [r.file for r in resultados if r.reason == "too_many_attempts"]
    resultados += [identification.avaliar(d, cliente, config) for d in holerites_legiveis]

    meses_usados, renda_valida = [], None
    if holerites:
        periodo = time_window.avaliar(holerites, cliente, config)
        meses_usados = periodo.details["months_used"]
        renda = income.avaliar(holerites, meses_usados, cliente, config)
        renda_valida = renda.details["valid_income"]
        for r in (periodo, renda):
            if escalados and r.status == REJECT:
                r.status = REVIEW
                r.details["incomplete_due_to"] = escalados
        resultados += [periodo, renda]

    resultados += [consistency.avaliar(d, config) for d in holerites_legiveis]
    resultados += [fraud.avaliar(d) for d in legiveis]

    resultados.sort(key=lambda r: ORDEM_REGRAS.index(r.rule))  # estável: mantém a ordem dos documentos
    motivos = []
    for r in resultados:
        if r.status != PASS and r.reason not in motivos:
            motivos.append(r.reason)
    rejeicoes = [r.reason for r in resultados if r.status == REJECT]
    revisoes = [r.reason for r in resultados if r.status == REVIEW]
    if rejeicoes:
        decisao, principal = REJECT, rejeicoes[0]
    elif revisoes:
        decisao, principal = REVIEW, revisoes[0]
    else:
        decisao, principal = APPROVE, None

    sinais_fraude = []
    for r in resultados:
        if r.reason == "suspected_fraud":
            if r.rule == "fraud":
                sinais_fraude.append(f"{r.file}: {r.details.get('fraud_reason') or 'sinalizado pelo LLM'}")
            else:
                sinais_fraude.append(f"{r.file}: totais não fecham (diferença de R$ {r.details['difference']})")

    return Decisao(
        decision=decisao, main_reason=principal, reasons=motivos, valid_income=renda_valida,
        months_used=meses_usados, fraud_flag=bool(sinais_fraude), fraud_reasons=sinais_fraude,
        results=resultados,
    )
