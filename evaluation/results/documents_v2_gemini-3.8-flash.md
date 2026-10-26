# Avaliação por documento: extraction_v2 · gemini-3.8-flash

Gerado por `evaluation/score_documents.py` a partir do cache, sem chamadas à API.

## Resumo

```
Prompt: extraction_v2 | modelo: gemini-3.8-flash | documentos extraídos: 10/98 | avaliados (sem os desfocados): 10

Acurácia por campo:
  document_type      10/10 (100.0%)
  pay_period         10/10 (100.0%)
  name_on_doc        10/10 (100.0%)
  cpf_on_doc         10/10 (100.0%)
  total_earnings     10/10 (100.0%)
  total_deductions   10/10 (100.0%)
  net_pay            10/10 (100.0%)

Linhas de provento: 12/12 encontradas | counts_as_income certo: 12/12 (100.0%) | valor certo: 12/12 (100.0%)
  puladas pelo modelo: 0 | inventadas: 0
Campos inventados (preenchidos onde o gabarito é vazio): 0
Fraude: 10/10 (100.0%) certos | detectadas: 0 | alarmes falsos: 0 | não detectadas: 0

API: 21 chamadas | taxa de erro: 11/21 (52.4%) (error_429: 1, error_503: 7, error_timeout: 3, ok: 10)
Latência: p50 40.27 s | p90 65.64 s
Tokens médios por documento: input 1788 | output 204 | thought 333 | total 2325
Sem extração no cache: 88 documentos
```

## Acurácia por campo

Base: 10 documentos (desfocados fora). Textos comparados exatamente como impressos; valores ao centavo.

| Campo | Acertos | Erros |
|---|---|---|
| document_type | 10/10 (100.0%) | 0 |
| pay_period | 10/10 (100.0%) | 0 |
| name_on_doc | 10/10 (100.0%) | 0 |
| cpf_on_doc | 10/10 (100.0%) | 0 |
| total_earnings | 10/10 (100.0%) | 0 |
| total_deductions | 10/10 (100.0%) | 0 |
| net_pay | 10/10 (100.0%) | 0 |

## Matriz de confusão do document_type

Linhas: gabarito (bank_statement contado como other). Colunas: extraído.

| gabarito \ extraído | payslip | payslip_vacation | payslip_13th | other |
|---|---|---|---|---|
| payslip | 10 | 0 | 0 | 0 |
| payslip_vacation | 0 | 0 | 0 | 0 |
| payslip_13th | 0 | 0 | 0 | 0 |
| other | 0 | 0 | 0 | 0 |

## Linhas de provento

Casamento por descrição (sem acentos, maiúsculas e espaços) e, se não houver, pelo valor.

- Linhas do gabarito: 12; encontradas: 12
- counts_as_income certo: 12/12 (100.0%)
- Valor certo: 12/12 (100.0%)
- Descrição copiada exatamente: 12/12 (100.0%)
- Puladas pelo modelo: 0; inventadas: 0

## Campos inventados

Valor preenchido onde o gabarito é vazio.

Nenhum.

## Suspeita de fraude

Esperado true só quando degradation = screenshot ou extra_text está preenchido.

- Acertos: 10/10 (100.0%)
- Fraudes detectadas: 0
- Alarmes falsos: 0
- Fraudes não detectadas: 0

## Documentos desfocados (fora das métricas)

O gabarito desses documentos não é legível; a decisão de ilegibilidade é do OCR (R7). Aqui só se registra o que o modelo devolveu: o ideal é null nos campos, sem valores inventados.

Nenhum documento desfocado extraído.

## API: latência, erros e tokens

- Chamadas registradas: 21
- Por status: error_429: 1, error_503: 7, error_timeout: 3, ok: 10
- Latência (chamadas com sucesso): p50 40.27 s; p90 65.64 s
- Tokens médios por documento: input_tokens 1788; output_tokens 204; thought_tokens 333; total_tokens 2325

## Documentos sem extração no cache

A03_2026-08.png, A03_2026-09.png, A04_2026-09.png, A05_2026-07.png, A05_2026-08.png, A05_2026-09.png, A06_2026-07.png, A06_2026-08.png, A06_2026-09.png, A07_2026-07.png, A07_2026-08.png, A07_2026-09.png, A08_2026-07.png, A08_2026-08.png, A08_2026-09.png, A09_2026-05.png, A09_2026-06.png, A09_2026-07.png, A09_2026-08.png, A09_2026-09.png, A10_2026-07.png, A10_2026-08.png, A10_2026-08_ferias.png, A10_2026-09.png, A11_2026-07.png, A11_2026-08.png, A11_2026-09.png, A11_2026-09_13o.png, A12_2026-07.png, A12_2026-08.png, A12_2026-09.png, A13_2026-07.png, A13_2026-08.png, A13_2026-09.png, A14_2026-07.png, A14_2026-08.png, A14_2026-09.png, A15_2026-07.png, A15_2026-08.png, A15_2026-09.png, A16_2026-07.png, A16_2026-08.png, A16_2026-09.png, N01_conta_de_luz.png, N02_extrato_2026-09.png, N03_2026-07.png, N03_2026-08.png, N03_2026-09.png, N04_2026-07.png, N04_2026-08.png, N04_2026-09.png, N05_2026-07.png, N05_2026-08.png, N05_2026-09.png, N06_2026-01.png, N06_2026-02.png, N06_2026-03.png, N07_2026-06.png, N07_2026-07.png, N07_2026-09.png, N08_2026-07.png, N08_2026-08.png, N08_2026-09.png, N09_2026-07.png, N09_2026-08.png, N09_2026-09.png, N10_2026-07.png, N10_2026-08.png, N10_2026-09.png, N11_2026-07.png, N11_2026-08.png, N11_2026-08_ferias.png, N11_2026-09.png, N12_2026-07.png, N12_2026-08.png, N12_2026-09.png, N13_2026-07.png, N13_2026-08.png, N13_2026-09.png, N14_2026-07.png, N14_2026-08.png, N14_2026-09.png, N15_2026-07.png, N15_2026-08.png, N15_2026-09.png, N16_2026-07.png, N16_2026-08.png, N16_2026-09.png
