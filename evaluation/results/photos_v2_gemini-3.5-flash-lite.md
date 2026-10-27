# Avaliação das fotos (v2): extraction_v2 · gemini-3.5-flash-lite

Gerado por `evaluation/score_photos.py` a partir do cache, sem chamadas à API. Gabarito: os valores do `source_file` de cada foto.

## Resumo

```
Fotos v2 | prompt extraction_v2 | modelo gemini-3.5-flash-lite | avaliadas (legíveis): 8 | ilegíveis à parte: 1
Campos e linhas certos: 70/72 (97.2%) | sem as fotos com nome do arquivo visível: 43/44 (97.7%)
Campos cortados inventados: 2
Porteiro OCR (limite 30): legíveis barradas (falso negativo): 0 | ilegíveis aprovadas: 1 (A10_2026-08_ferias_tremido.jpeg)
API: 9 chamadas | erros: 0/9 (0.0%) | latência p50 2.79 s, p90 4.92 s
Tokens médios por foto: input 1805 | output 222 | thought 0 | total 2027
Fotos sem extração no cache: A14_2026-08_occluded.jpg, A14_2026-09_upside_down.jpg, A15_2026-07_cropped-high.jpg, A15_2026-08_motion_blur.jpg, A15_2026-09_motion_blur-medium.jpg, A16_2026-07_cropped.jpg, A16_2026-08_flash_glare.jpg, A16_2026-09_flash_glare.jpg, N01_conta_de_luz_rotated.jpg, N02_extrato_2026-09_none.jpg, N03_2026-07_cropped-high.jpg
```

## Por defeito

| Grupo | Fotos | Campos e linhas certos | Inventados |
|---|---|---|---|
| cropped | 1 | 7/8 (87.5%) | 2 |
| flash_glare | 1 | 9/9 (100.0%) | 0 |
| none | 2 | 18/18 (100.0%) | 0 |
| screen_ui_visible | 2 | 19/19 (100.0%) | 0 |
| small_in_frame | 1 | 8/9 (88.9%) | 0 |
| tilted | 1 | 9/9 (100.0%) | 0 |

## Por severidade

| Grupo | Fotos | Campos e linhas certos | Inventados |
|---|---|---|---|
| high | 1 | 7/8 (87.5%) | 2 |
| low | 2 | 19/19 (100.0%) | 0 |
| medium | 3 | 26/27 (96.3%) | 0 |
| none | 2 | 18/18 (100.0%) | 0 |

## Nome do arquivo visível na foto (label_leak)

Nessas fotos o modelo pode ler cliente e competência na barra do visualizador.

| Grupo | Fotos | Campos e linhas certos | Inventados |
|---|---|---|---|
| com nome visível | 3 | 27/28 (96.4%) | 0 |
| sem nome visível | 5 | 43/44 (97.7%) | 2 |

## Acurácia por campo

| Campo | Certos |
|---|---|
| document_type | 8/8 (100.0%) |
| pay_period | 8/8 (100.0%) |
| name_on_doc | 7/7 (100.0%) |
| cpf_on_doc | 8/8 (100.0%) |
| total_earnings | 7/8 (87.5%) |
| total_deductions | 8/8 (100.0%) |
| net_pay | 8/8 (100.0%) |
| fraud_suspected | 7/8 (87.5%) |

Linhas de provento: 9 encontradas, 0 puladas, 0 inventadas; valor certo 9/9 (100.0%); counts_as_income certo 9/9 (100.0%).

## Foto a foto

### A01_2026-07_happy-path.jpeg

Defeito none (none) · nome do arquivo visível: no · certos 9/9

| Campo | Gabarito | Extraído | |
|---|---|---|---|
| document_type | payslip | payslip | ✓ |
| pay_period | 2026-07 | 2026-07 | ✓ |
| name_on_doc | OTÁVIO OLIVEIRA ARAÚJO | OTÁVIO OLIVEIRA ARAÚJO | ✓ |
| cpf_on_doc | 782.943.622-39 | 782.943.622-39 | ✓ |
| total_earnings | 2388.00 | 2388.00 | ✓ |
| total_deductions | 192.15 | 192.15 | ✓ |
| net_pay | 2195.85 | 2195.85 | ✓ |
| fraud_suspected | true | true | ✓ |
| linha: SALÁRIO BASE | | 'SALÁRIO BASE' 2388.00 conta=true | ✓ |

### A13_2026-07_foto-vertical-de-tela-pc.jpeg

Defeito screen_ui_visible (low) · nome do arquivo visível: yes · certos 10/10

| Campo | Gabarito | Extraído | |
|---|---|---|---|
| document_type | payslip | payslip | ✓ |
| pay_period | 2026-07 | 2026-07 | ✓ |
| name_on_doc | CONCEIÇÃO VIEIRA NOGUEIRA | CONCEIÇÃO VIEIRA NOGUEIRA | ✓ |
| cpf_on_doc | 925.912.632-05 | 925.912.632-05 | ✓ |
| total_earnings | 3306.13 | 3306.13 | ✓ |
| total_deductions | 348.39 | 348.39 | ✓ |
| net_pay | 2957.74 | 2957.74 | ✓ |
| fraud_suspected | true | true | ✓ |
| linha: SALÁRIO BASE | | 'SALÁRIO BASE' 2955.25 conta=true | ✓ |
| linha: ADICIONAL NOTURNO | | 'ADICIONAL NOTURNO' 350.88 conta=true | ✓ |

### A15_2026-08_foto-horizontal.jpeg

Defeito screen_ui_visible (low) · nome do arquivo visível: no · certos 9/9

| Campo | Gabarito | Extraído | |
|---|---|---|---|
| document_type | payslip | payslip | ✓ |
| pay_period | 2026-08 | 2026-08 | ✓ |
| name_on_doc | ANTÔNIO MEDEIROS REZENDE | ANTÔNIO MEDEIROS REZENDE | ✓ |
| cpf_on_doc | 966.362.917-70 | 966.362.917-70 | ✓ |
| total_earnings | 4050.00 | 4050.00 | ✓ |
| total_deductions | 535.84 | 535.84 | ✓ |
| net_pay | 3514.16 | 3514.16 | ✓ |
| fraud_suspected | true | true | ✓ |
| linha: SALÁRIO BASE | | 'SALÁRIO BASE' 4050.00 conta=true | ✓ |

### A15_2026-07_foto-horizontal.jpeg

Defeito none (none) · nome do arquivo visível: no · certos 9/9

| Campo | Gabarito | Extraído | |
|---|---|---|---|
| document_type | payslip | payslip | ✓ |
| pay_period | 2026-07 | 2026-07 | ✓ |
| name_on_doc | ANTÔNIO MEDEIROS REZENDE | ANTÔNIO MEDEIROS REZENDE | ✓ |
| cpf_on_doc | 966.362.917-70 | 966.362.917-70 | ✓ |
| total_earnings | 4050.00 | 4050.00 | ✓ |
| total_deductions | 535.84 | 535.84 | ✓ |
| net_pay | 3514.16 | 3514.16 | ✓ |
| fraud_suspected | true | true | ✓ |
| linha: SALÁRIO BASE | | 'SALÁRIO BASE' 4050.00 conta=true | ✓ |

### A15_2026-09_foto-vertical-sem-cortar.jpeg

Defeito small_in_frame (medium) · nome do arquivo visível: yes · certos 8/9

| Campo | Gabarito | Extraído | |
|---|---|---|---|
| document_type | payslip | payslip | ✓ |
| pay_period | 2026-09 | 2026-09 | ✓ |
| name_on_doc | ANTÔNIO MEDEIROS REZENDE | ANTÔNIO MEDEIROS REZENDE | ✓ |
| cpf_on_doc | 966.362.917-70 | 966.362.917-70 | ✓ |
| total_earnings | 4050.00 | 4050.00 | ✓ |
| total_deductions | 535.84 | 535.84 | ✓ |
| net_pay | 3514.16 | 3514.16 | ✓ |
| fraud_suspected | true | false | ✗ |
| linha: SALÁRIO BASE | | 'SALÁRIO BASE' 4050.00 conta=true | ✓ |

### N14_2026-07_inclinado.jpeg

Defeito tilted (medium) · nome do arquivo visível: yes · certos 9/9

| Campo | Gabarito | Extraído | |
|---|---|---|---|
| document_type | payslip | payslip | ✓ |
| pay_period | 2026-07 | 2026-07 | ✓ |
| name_on_doc | LARISSA M. P. CARDOSO | LARISSA M. P. CARDOSO | ✓ |
| cpf_on_doc | null | null | ✓ |
| total_earnings | 1930.04 | 1930.04 | ✓ |
| total_deductions | 150.93 | 150.93 | ✓ |
| net_pay | 1779.11 | 1779.11 | ✓ |
| fraud_suspected | true | true | ✓ |
| linha: SALÁRIO BASE | | 'SALÁRIO BASE' 1930.04 conta=true | ✓ |

### N14_2026-08_foto-com-flash.jpeg

Defeito flash_glare (medium) · nome do arquivo visível: no · certos 9/9

| Campo | Gabarito | Extraído | |
|---|---|---|---|
| document_type | payslip | payslip | ✓ |
| pay_period | 2026-08 | 2026-08 | ✓ |
| name_on_doc | LARISSA M. P. CARDOSO | LARISSA M. P. CARDOSO | ✓ |
| cpf_on_doc | null | null | ✓ |
| total_earnings | 1930.04 | 1930.04 | ✓ |
| total_deductions | 150.93 | 150.93 | ✓ |
| net_pay | 1779.11 | 1779.11 | ✓ |
| fraud_suspected | true | true | ✓ |
| linha: SALÁRIO BASE | | 'SALÁRIO BASE' 1930.04 conta=true | ✓ |

### N14_2026-09_cortado.jpeg

Defeito cropped (high) · nome do arquivo visível: no · certos 7/8

| Campo | Gabarito | Extraído | |
|---|---|---|---|
| document_type | payslip | payslip | ✓ |
| pay_period | 2026-09 | 2026-09 | ✓ |
| name_on_doc | (parcial) | ISSA M. P. CARDOSO | parcial |
| cpf_on_doc | null | null | ✓ |
| total_earnings | null | 1930.04 | ✗ |
| total_deductions | 150.93 | 150.93 | ✓ |
| net_pay | 1779.11 | 1779.11 | ✓ |
| fraud_suspected | true | true | ✓ |
| linha: SALÁRIO BASE | | 'Salário' 1930.04 conta=true | ✓ |

Inventados nos campos cortados: total_earnings = 1930.04; earnings_lines.description = Salário

## Fotos ilegíveis (fora da acurácia)

**A10_2026-08_ferias_tremido.jpeg**

```json
{
  "document_type": "payslip_vacation",
  "pay_period": "2026-10",
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
  "fraud_suspected": false,
  "fraud_reason": null
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
| N14_2026-07_inclinado.jpeg | 41.00 | 1 | legível | legível | 9/9 (tudo) |  |
| A15_2026-09_foto-vertical-sem-cortar.jpeg | 51.83 | 24 | legível | legível | 8/9 |  |
| A13_2026-07_foto-vertical-de-tela-pc.jpeg | 55.43 | 21 | legível | legível | 10/10 (tudo) |  |
| A01_2026-07_happy-path.jpeg | 66.03 | 63 | legível | legível | 9/9 (tudo) |  |
| N14_2026-09_cortado.jpeg | 66.39 | 41 | legível | legível | 7/8 |  |
| A15_2026-07_foto-horizontal.jpeg | 77.08 | 49 | legível | legível | 9/9 (tudo) |  |
| A15_2026-08_foto-horizontal.jpeg | 80.21 | 73 | legível | legível | 9/9 (tudo) |  |
| N14_2026-08_foto-com-flash.jpeg | 85.79 | 33 | legível | legível | 9/9 (tudo) |  |
