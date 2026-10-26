"""Motor de regras: aplica as regras da v1 aos documentos de um cliente e decide.

Ordem (rules.md): legibilidade, tipo, titular, período, renda e, por fim, as
revisões (consistência e fraude). Todas as regras rodam, sem parar na primeira
falha, para que a lista completa de motivos e a renda fiquem registradas mesmo
quando o cliente é reprovado. Decisão: qualquer reject vence qualquer review;
qualquer review vence approve. O motivo principal é o primeiro reject na ordem
das regras ou, sem reject, o primeiro review.

Quais documentos cada regra recebe:
- legibilidade e fraude: todos os documentos (a fraude, só os legíveis);
- tipo: os legíveis; um documento de outro tipo junto com holerites é ignorado;
- titular e consistência: os holerites legíveis;
- período e renda: todos os holerites, inclusive um ilegível cujos dados existam
  (modo oracle). Sem nenhum holerite, período e renda não são avaliados.
"""

from .models import APPROVE, PASS, REJECT, REVIEW, Decisao
from .rules import consistency, document_type, fraud, identification, income, legibility, time_window

ORDEM_REGRAS = ["legibility", "document_type", "identification", "time_window", "income",
                "consistency", "fraud"]


def decidir(cliente, documentos, config):
    resultados = [legibility.avaliar(d) for d in documentos]
    ilegiveis = {r.file for r in resultados if r.status != PASS}
    legiveis = [d for d in documentos if d.file not in ilegiveis]

    resultados.append(document_type.avaliar(legiveis))
    holerites = [d for d in documentos if document_type.aceito(d)]
    holerites_legiveis = [d for d in holerites if d.file not in ilegiveis]

    resultados += [identification.avaliar(d, cliente, config) for d in holerites_legiveis]

    meses_usados, renda_valida = [], None
    if holerites:
        periodo = time_window.avaliar(holerites, cliente, config)
        meses_usados = periodo.details["months_used"]
        renda = income.avaliar(holerites, meses_usados, cliente, config)
        renda_valida = renda.details["valid_income"]
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
