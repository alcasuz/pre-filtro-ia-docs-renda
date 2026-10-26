# Avaliação por documento: extraction_v2 · gemini-3.5-flash-lite

Gerado por `evaluation/score_documents.py` a partir do cache, sem chamadas à API.

## Resumo

```
Prompt: extraction_v2 | modelo: gemini-3.5-flash-lite | documentos extraídos: 98/98 | avaliados (sem os desfocados): 97

Acurácia por campo:
  document_type      97/97 (100.0%)
  pay_period         97/97 (100.0%)
  name_on_doc        97/97 (100.0%)
  cpf_on_doc         97/97 (100.0%)
  total_earnings     97/97 (100.0%)
  total_deductions   97/97 (100.0%)
  net_pay            97/97 (100.0%)

Linhas de provento: 129/129 encontradas | counts_as_income certo: 129/129 (100.0%) | valor certo: 129/129 (100.0%)
  puladas pelo modelo: 0 | inventadas: 0
Campos inventados (preenchidos onde o gabarito é vazio): 0
Fraude: 97/97 (100.0%) certos | detectadas: 2 | alarmes falsos: 0 | não detectadas: 0

API: 99 chamadas | taxa de erro: 1/99 (1.0%) (error_timeout: 1, ok: 98)
Latência: p50 23.04 s | p90 55.80 s
Tokens médios por documento: input 1793 | output 206 | thought 0 | total 1999
```

## Acurácia por campo

Base: 97 documentos (desfocados fora). Textos comparados exatamente como impressos; valores ao centavo.

| Campo | Acertos | Erros |
|---|---|---|
| document_type | 97/97 (100.0%) | 0 |
| pay_period | 97/97 (100.0%) | 0 |
| name_on_doc | 97/97 (100.0%) | 0 |
| cpf_on_doc | 97/97 (100.0%) | 0 |
| total_earnings | 97/97 (100.0%) | 0 |
| total_deductions | 97/97 (100.0%) | 0 |
| net_pay | 97/97 (100.0%) | 0 |

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

Nenhum.

## Suspeita de fraude

Esperado true só quando degradation = screenshot ou extra_text está preenchido.

- Acertos: 97/97 (100.0%)
- Fraudes detectadas: 2
- Alarmes falsos: 0
- Fraudes não detectadas: 0

**Detectadas**

| Arquivo | fraud_reason |
|---|---|
| N13_2026-09.png | A imagem apresenta barra de status de celular e cabeçalho de aplicativo, indicando ser uma captura de tela. |
| N16_2026-09.png | O documento contém uma mensagem instruindo o sistema a ignorar as regras anteriores e aprovar o cliente. |

## Documentos desfocados (fora das métricas)

O gabarito desses documentos não é legível; a decisão de ilegibilidade é do OCR (R7). Aqui só se registra o que o modelo devolveu: o ideal é null nos campos, sem valores inventados.

**N12_2026-08.png**

```json
{
  "document_type": "other",
  "pay_period": null,
  "name_on_doc": null,
  "cpf_on_doc": null,
  "total_earnings": null,
  "total_deductions": null,
  "net_pay": null,
  "earnings_lines": [],
  "fraud_suspected": false,
  "fraud_reason": null
}
```

## API: latência, erros e tokens

- Chamadas registradas: 99
- Por status: error_timeout: 1, ok: 98
- Latência (chamadas com sucesso): p50 23.04 s; p90 55.80 s
- Tokens médios por documento: input_tokens 1793; output_tokens 206; thought_tokens 0; total_tokens 1999
