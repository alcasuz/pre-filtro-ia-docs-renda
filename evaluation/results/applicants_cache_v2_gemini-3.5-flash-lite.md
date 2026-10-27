# Avaliação por cliente: cache extraction_v2 · gemini-3.5-flash-lite

Gerado por `evaluation/score_applicants.py`, sem chamadas à API. Configuração: `config/default_rules.yaml` v1 (multiplicador 3, similaridade token_sort_ratio, legibilidade OCR >= 30).

## Resumo

```
Fonte: cache extraction_v2 · gemini-3.5-flash-lite | config v1 | clientes: 32
Decisão certa: 32/32 (100.0%) | motivo principal certo: 32/32 (100.0%)
Acerto por classe: approve 16/16 (100.0%) | reject 12/12 (100.0%) | review 4/4 (100.0%)
Falso negativo (deveria aprovar, foi reprovado): 0/16 (0.0%)
Renda válida diferente do gabarito (> R$ 0,01): 0 de 30 comparáveis
Clientes com decisão ou motivo errado: 0
```

## Matriz de confusão

Linhas: gabarito. Colunas: motor.

| gabarito \ obtido | approve | reject | review |
|---|---|---|---|
| approve | 16 | 0 | 0 |
| reject | 0 | 12 | 0 |
| review | 0 | 0 | 4 |

## Clientes errados (decisão ou motivo principal)

Nenhum.

## Renda válida

Comparáveis: 30; diferentes do gabarito (> R$ 0,01): 0.

## Todos os clientes

| Cliente | Esperado | Obtido | Motivo esperado | Motivo obtido | Renda gabarito | Renda motor | Fraude |
|---|---|---|---|---|---|---|---|
| A01 | approve | approve | — | — | 2388.00 | 2388.00 | não |
| A02 | approve | approve | — | — | 2712.60 | 2712.60 | não |
| A03 | approve | approve | — | — | 1823.28 | 1823.28 | não |
| A04 | approve | approve | — | — | 1607.40 | 1607.40 | não |
| A05 | approve | approve | — | — | 2776.85 | 2776.85 | não |
| A06 | approve | approve | — | — | 3856.81 | 3856.81 | não |
| A07 | approve | approve | — | — | 4208.64 | 4208.64 | não |
| A08 | approve | approve | — | — | 4867.52 | 4867.52 | não |
| A09 | approve | approve | — | — | 3293.46 | 3293.46 | não |
| A10 | approve | approve | — | — | 2843.82 | 2843.82 | não |
| A11 | approve | approve | — | — | 3128.16 | 3128.16 | não |
| A12 | approve | approve | — | — | 3428.36 | 3428.36 | não |
| A13 | approve | approve | — | — | 3358.24 | 3358.24 | não |
| A14 | approve | approve | — | — | 1796.45 | 1796.45 | não |
| A15 | approve | approve | — | — | 4050.00 | 4050.00 | não |
| A16 | approve | approve | — | — | 2622.00 | 2622.00 | não |
| N01 | reject | reject | type_not_accepted | type_not_accepted | — | — | não |
| N02 | reject | reject | type_not_accepted | type_not_accepted | — | — | não |
| N03 | reject | reject | cpf_mismatch | cpf_mismatch | 2938.54 | 2938.54 | não |
| N04 | reject | reject | id_missing | id_missing | 2418.00 | 2418.00 | não |
| N05 | reject | reject | name_mismatch | name_mismatch | 1845.18 | 1845.18 | não |
| N06 | reject | reject | outside_window | outside_window | 4632.16 | 4632.16 | não |
| N07 | reject | reject | non_consecutive_months | non_consecutive_months | 2358.63 | 2358.63 | não |
| N08 | reject | reject | insufficient_income | insufficient_income | 1516.54 | 1516.54 | não |
| N09 | reject | reject | insufficient_income | insufficient_income | 1737.34 | 1737.34 | não |
| N10 | reject | reject | insufficient_income | insufficient_income | 3378.50 | 3378.50 | não |
| N11 | reject | reject | insufficient_income | insufficient_income | 1898.73 | 1898.73 | não |
| N12 | reject | reject | illegible | illegible | 2808.93 | 2808.93 | não |
| N13 | review | review | suspected_fraud | suspected_fraud | 5031.00 | 5031.00 | sim |
| N14 | review | review | name_review | name_review | 1930.04 | 1930.04 | não |
| N15 | review | review | suspected_fraud | suspected_fraud | 2802.60 | 2802.60 | sim |
| N16 | review | review | suspected_fraud | suspected_fraud | 5856.06 | 5856.06 | sim |
