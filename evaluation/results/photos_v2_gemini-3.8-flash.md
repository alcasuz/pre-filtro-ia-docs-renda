# Avaliação das fotos (v2): extraction_v2 · gemini-3.8-flash

Gerado por `evaluation/score_photos.py` a partir do cache, sem chamadas à API. Gabarito: os valores do `source_file` de cada foto.

## Resumo

```
Fotos v2 | prompt extraction_v2 | modelo gemini-3.8-flash | avaliadas (legíveis): 1 | ilegíveis à parte: 1
Campos e linhas certos: 7/8 (87.5%) | sem as fotos com nome do arquivo visível: 7/8 (87.5%)
Campos cortados inventados: 0
Porteiro OCR (limite 30): legíveis barradas (falso negativo): 0 | ilegíveis aprovadas: 1 (A10_2026-08_ferias_tremido.jpeg)
API: 10 chamadas | erros: 8/10 (80.0%) | latência p50 162.10 s, p90 196.42 s
Tokens médios por foto: input 1808 | output 214 | thought 3764 | total 5786
Fotos sem extração no cache: A01_2026-07_happy-path.jpeg, A13_2026-07_foto-vertical-de-tela-pc.jpeg, A15_2026-08_foto-horizontal.jpeg, A15_2026-07_foto-horizontal.jpeg, A15_2026-09_foto-vertical-sem-cortar.jpeg, N14_2026-07_inclinado.jpeg, N14_2026-08_foto-com-flash.jpeg, A14_2026-08_occluded.jpg, A14_2026-09_upside_down.jpg, A15_2026-07_cropped-high.jpg, A15_2026-08_motion_blur.jpg, A15_2026-09_motion_blur-medium.jpg, A16_2026-07_cropped.jpg, A16_2026-08_flash_glare.jpg, A16_2026-09_flash_glare.jpg, N01_conta_de_luz_rotated.jpg, N02_extrato_2026-09_none.jpg, N03_2026-07_cropped-high.jpg
```

## Por defeito

| Grupo | Fotos | Campos e linhas certos | Inventados |
|---|---|---|---|
| cropped | 1 | 7/8 (87.5%) | 0 |

## Por severidade

| Grupo | Fotos | Campos e linhas certos | Inventados |
|---|---|---|---|
| high | 1 | 7/8 (87.5%) | 0 |

## Nome do arquivo visível na foto (label_leak)

Nessas fotos o modelo pode ler cliente e competência na barra do visualizador.

| Grupo | Fotos | Campos e linhas certos | Inventados |
|---|---|---|---|
| sem nome visível | 1 | 7/8 (87.5%) | 0 |

## Acurácia por campo

| Campo | Certos |
|---|---|
| document_type | 1/1 (100.0%) |
| pay_period | 1/1 (100.0%) |
| name_on_doc | — |
| cpf_on_doc | 1/1 (100.0%) |
| total_earnings | 1/1 (100.0%) |
| total_deductions | 1/1 (100.0%) |
| net_pay | 1/1 (100.0%) |
| fraud_suspected | 1/1 (100.0%) |

Linhas de provento: 0 encontradas, 1 puladas, 0 inventadas; valor certo —; counts_as_income certo —.

## Foto a foto

### N14_2026-09_cortado.jpeg

Defeito cropped (high) · nome do arquivo visível: no · certos 7/8

| Campo | Gabarito | Extraído | |
|---|---|---|---|
| document_type | payslip | payslip | ✓ |
| pay_period | 2026-09 | 2026-09 | ✓ |
| name_on_doc | (parcial) | null | parcial |
| cpf_on_doc | null | null | ✓ |
| total_earnings | null | null | ✓ |
| total_deductions | 150.93 | 150.93 | ✓ |
| net_pay | 1779.11 | 1779.11 | ✓ |
| fraud_suspected | true | true | ✓ |
| linha pulada: SALÁRIO BASE | 1930.04 | — | ✗ |

## Fotos ilegíveis (fora da acurácia)

**A10_2026-08_ferias_tremido.jpeg**

```json
{
  "document_type": "payslip_vacation",
  "pay_period": "2026-08",
  "name_on_doc": "GABRIELA QUINTANA PINTO",
  "cpf_on_doc": "816.425.287-26",
  "total_earnings": 1263.92,
  "total_deductions": 94.79,
  "net_pay": 1169.13,
  "earnings_lines": [
    {
      "description": "FÉRIAS (10 DIAS)",
      "amount": 947.94,
      "counts_as_income": true
    },
    {
      "description": "1/3 CONSTITUCIONAL DE FÉRIAS",
      "amount": 315.98,
      "counts_as_income": false
    }
  ],
  "fraud_suspected": true,
  "fraud_reason": "A imagem é uma foto de tela de computador exibindo barra de status com ícone de bateria, cabeçalho de aplicativo e interface do sistema operacional."
}
```

## Porteiro do OCR

Limite atual: 30 (provisório, calibrado na base sintética). ⚠️ marca legível barrada pelo porteiro (falso negativo) ou ilegível aprovada.

| Foto | Confiança OCR | Palavras | Porteiro | Seu julgamento | LLM extraiu certo | |
|---|---|---|---|---|---|---|
| A14_2026-08_occluded.jpg | null | — | ilegível | legível | fora da acurácia | ⚠️ |
| A14_2026-09_upside_down.jpg | null | — | ilegível | legível | fora da acurácia | ⚠️ |
| A15_2026-07_cropped-high.jpg | null | — | ilegível | legível | fora da acurácia | ⚠️ |
| A15_2026-08_motion_blur.jpg | null | — | ilegível | legível | fora da acurácia | ⚠️ |
| A15_2026-09_motion_blur-medium.jpg | null | — | ilegível | legível | fora da acurácia | ⚠️ |
| A16_2026-07_cropped.jpg | null | — | ilegível | legível | fora da acurácia | ⚠️ |
| A16_2026-08_flash_glare.jpg | null | — | ilegível | legível | fora da acurácia | ⚠️ |
| A16_2026-09_flash_glare.jpg | null | — | ilegível | legível | fora da acurácia | ⚠️ |
| N01_conta_de_luz_rotated.jpg | null | — | ilegível | legível | fora da acurácia | ⚠️ |
| N02_extrato_2026-09_none.jpg | null | — | ilegível | legível | fora da acurácia | ⚠️ |
| N03_2026-07_cropped-high.jpg | null | — | ilegível | legível | fora da acurácia | ⚠️ |
| A10_2026-08_ferias_tremido.jpeg | 37.25 | 8 | legível | ilegível | fora da acurácia | ⚠️ |
| N14_2026-07_inclinado.jpeg | 41.00 | 1 | legível | legível | fora da acurácia |  |
| A15_2026-09_foto-vertical-sem-cortar.jpeg | 51.83 | 24 | legível | legível | fora da acurácia |  |
| A13_2026-07_foto-vertical-de-tela-pc.jpeg | 55.43 | 21 | legível | legível | fora da acurácia |  |
| A01_2026-07_happy-path.jpeg | 66.03 | 63 | legível | legível | fora da acurácia |  |
| N14_2026-09_cortado.jpeg | 66.39 | 41 | legível | legível | 7/8 |  |
| A15_2026-07_foto-horizontal.jpeg | 77.08 | 49 | legível | legível | fora da acurácia |  |
| A15_2026-08_foto-horizontal.jpeg | 80.21 | 73 | legível | legível | fora da acurácia |  |
| N14_2026-08_foto-com-flash.jpeg | 85.79 | 33 | legível | legível | fora da acurácia |  |
