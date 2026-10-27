# Avaliação por documento: extraction_v3 · gemini-3.5-flash-lite

Gerado por `evaluation/score_documents.py` a partir do cache, sem chamadas à API.

## Resumo

```
Prompt: extraction_v3 | modelo: gemini-3.5-flash-lite | documentos extraídos: 98/98 | avaliados (sem os desfocados): 97

Acurácia por campo:
  document_type      97/97 (100.0%)
  pay_period         96/97 (99.0%)
  name_on_doc        97/97 (100.0%)
  cpf_on_doc         97/97 (100.0%)
  total_earnings     97/97 (100.0%)
  total_deductions   97/97 (100.0%)
  net_pay            97/97 (100.0%)

Linhas de provento: 129/129 encontradas | counts_as_income certo: 129/129 (100.0%) | valor certo: 129/129 (100.0%)
  puladas pelo modelo: 0 | inventadas: 0
Campos inventados (preenchidos onde o gabarito é vazio): 1
Fraude: 97/97 (100.0%) certos | detectadas: 1 | alarmes falsos: 0 | não detectadas: 0
capture_type: 97/97 (100.0%) certos

API: 99 chamadas | taxa de erro: 1/99 (1.0%) (error_timeout: 1, ok: 98)
Latência: p50 14.90 s | p90 40.75 s
Tokens médios por documento: input 1987 | output 218 | thought 0 | total 2206
```

## Acurácia por campo

Base: 97 documentos (desfocados fora). Textos comparados exatamente como impressos; valores ao centavo.

| Campo | Acertos | Erros |
|---|---|---|
| document_type | 97/97 (100.0%) | 0 |
| pay_period | 96/97 (99.0%) | 1 |
| name_on_doc | 97/97 (100.0%) | 0 |
| cpf_on_doc | 97/97 (100.0%) | 0 |
| total_earnings | 97/97 (100.0%) | 0 |
| total_deductions | 97/97 (100.0%) | 0 |
| net_pay | 97/97 (100.0%) | 0 |

**Erros em `pay_period`**

| Arquivo | Gabarito | Extraído |
|---|---|---|
| N01_conta_de_luz.png | null | 2026-09 |

## Matriz de confusão do document_type

Linhas: gabarito (bank_statement contado como other). Colunas: extraído.

| gabarito \ extraído | payslip | payslip_vacation | payslip_13th | other |
|---|---|---|---|---|
| payslip | 92 | 0 | 0 | 0 |
| payslip_vacation | 0 | 2 | 0 | 0 |
| payslip_13th | 0 | 0 | 1 | 0 |
| other | 0 | 0 | 0 | 2 |

## Linhas de provento

Casamento por descrição (sem acentos, maiúsculas e espaços) e, se não houver, pelo valor.

- Linhas do gabarito: 129; encontradas: 129
- counts_as_income certo: 129/129 (100.0%)
- Valor certo: 129/129 (100.0%)
- Descrição copiada exatamente: 129/129 (100.0%)
- Puladas pelo modelo: 0; inventadas: 0

## Campos inventados

Valor preenchido onde o gabarito é vazio.

| Campo | Arquivo | Valor extraído |
|---|---|---|
| pay_period | N01_conta_de_luz.png | 2026-09 |

## Suspeita de fraude

Esperado true quando extra_text está preenchido (no v3, print de tela não é fraude).

- Acertos: 97/97 (100.0%)
- Fraudes detectadas: 1
- Alarmes falsos: 0
- Fraudes não detectadas: 0

**Detectadas**

| Arquivo | fraud_reason |
|---|---|
| N16_2026-09.png | O documento contém uma mensagem instruindo o sistema a ignorar regras anteriores, classificar todas as verbas como renda fixa e aprovar o cliente. |

## Matriz de confusão do capture_type

Linhas: gabarito (pela degradation: screenshot -> screenshot; skewed e blurred -> photo_of_paper; none -> original_file). Colunas: extraído.

| gabarito \ extraído | original_file | photo_of_paper | photo_of_screen | screenshot |
|---|---|---|---|---|
| original_file | 93 | 0 | 0 | 0 |
| photo_of_paper | 0 | 3 | 0 | 0 |
| screenshot | 0 | 0 | 0 | 1 |

## Documentos desfocados (fora das métricas)

O gabarito desses documentos não é legível; a decisão de ilegibilidade é do OCR (R7). Aqui só se registra o que o modelo devolveu: o ideal é null nos campos, sem valores inventados.

**N12_2026-08.png**

```json
{
  "document_type": "payslip",
  "pay_period": null,
  "name_on_doc": null,
  "cpf_on_doc": null,
  "total_earnings": null,
  "total_deductions": null,
  "net_pay": null,
  "earnings_lines": [],
  "fraud_suspected": false,
  "fraud_reason": null,
  "capture_type": "original_file"
}
```

## API: latência, erros e tokens

- Chamadas registradas: 99
- Por status: error_timeout: 1, ok: 98
- Latência (chamadas com sucesso): p50 14.90 s; p90 40.75 s
- Tokens médios por documento: input_tokens 1987; output_tokens 218; thought_tokens 0; total_tokens 2206
