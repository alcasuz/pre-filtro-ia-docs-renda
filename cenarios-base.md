# Cenários da base de teste (v1: holerite)

> Base 100% fictícia. Nomes, CPFs, empresas e CNPJs inventados; CPFs gerados aleatoriamente com dígito verificador válido, sem relação com pessoas reais.
> Versão: rascunho v0.1 (24/10/2026)

## Princípios

- **Unidade da decisão:** cliente. **Unidade da extração:** documento (cada imagem).
- **Proporção:** ~50% aprova, ~50% reprova ou revisão. A base é enriquecida de propósito e **não** é uma amostra da produção.
- **Cada caminho de cada regra aparece pelo menos uma vez.** Casos de borda ficam perto do limite de 3× a parcela.
- **`data_analise` fixa por cliente** (premissa 2 das regras).

---

## Clientes que devem ser aprovados (16)

| ID | Cenário | Regra testada | Por que está na base |
|---|---|---|---|
| A01 | Caminho feliz: só salário-base (empresa 1) | todas | referência |
| A02 | Caminho feliz: só salário-base (empresa 2, outro layout) | todas | variação de layout |
| A03 | Caminho feliz: só salário-base (empresa 3, outro layout) | todas | variação de layout |
| A04 | Salário + insalubridade/periculosidade | R5 | verba fixa além do salário |
| A05 | Salário + hora extra; renda fixa passa sozinha | R5 | hora extra presente sem mudar a decisão |
| A06 | CPF no formato XXX.XXX.XXX-XX | R2 | normalização do CPF |
| A07 | CPF só com números (XXXXXXXXXXX) | R2 | normalização do CPF |
| A08 | Sem CPF; nome igual ao cadastro, mas com acento e maiúsculas diferentes | R2 | similaridade ≥ 95% após normalizar |
| A09 | Enviou 6 holerites; os 3 mais recentes passam | R3 | seleção dos 3 mais recentes |
| A10 | Mês com férias: holerite mensal proporcional + holerite de férias separado | R3, R5 | soma de férias sem o 1/3 |
| A11 | Holerite de 13º separado na mesma competência | R3 | 13º ignorado |
| A12 | Adiantamento salarial lançado como desconto | R5 | desconto não afeta a renda bruta fixa |
| A13 | Borda: renda = 3,02× a parcela | R6 | fragilidade perto do limite |
| A14 | Borda: renda = 3,05× a parcela | R6 | fragilidade perto do limite |
| A15 | Borda: renda = exatamente 3,00× a parcela | R6 | regra é "≥" |
| A16 | Foto levemente torta, mas legível | R7 | não marcar como ilegível o que é legível |

## Clientes que não devem ser aprovados (16)

### Reprova (12)

| ID | Cenário | Regra testada | Decisão |
|---|---|---|---|
| N01 | Arquivo que não é documento de renda | R1 | reprova |
| N02 | Extrato bancário (tipo não aceito na v1) | R1 | reprova |
| N03 | CPF divergente do cadastro | R2 | reprova |
| N04 | Sem CPF e sem nome | R2 | reprova |
| N05 | Sem CPF; nome de outra pessoa (similaridade < 50%) | R2 | reprova |
| N06 | Holerites fora da janela de 4 meses | R3 | reprova |
| N07 | Mês faltando no meio (meses não consecutivos) | R3 | reprova |
| N08 | Renda claramente abaixo de 3× | R6 | reprova |
| N09 | Borda: renda = 2,98× a parcela | R6 | reprova |
| N10 | Hora extra muda a decisão: renda fixa 2,9×, com hora extra passaria de 3× | R5 | reprova |
| N11 | 1/3 de férias muda a decisão: só passaria somando o 1/3 | R5 | reprova |
| N12 | Um dos 3 holerites ilegível (desfocado) | R7 | reprova com orientação |

### Revisão humana (4)

| ID | Cenário | Regra testada | Decisão |
|---|---|---|---|
| N13 | Print de tela de holerite | R1 | revisão |
| N14 | Sem CPF; nome abreviado (similaridade entre 50% e 95%) | R2 | revisão |
| N15 | Conta não fecha (proventos − descontos ≠ líquido, além da tolerância) | R4 | revisão |
| N16 | Texto no holerite tentando dar instruções ao sistema (prompt injection) | R7 | revisão |

**Total:** 32 clientes, cerca de 90 imagens (a maioria dos clientes envia 3 holerites).

---

## Arquivos da base

### `cadastros.csv` (um por cliente)
`cliente_id, nome, cpf, valor_parcela, data_analise`

### `documentos.csv` (um por imagem; gabarito da extração)
`arquivo, cliente_id, tipo_real, competencia (AAAA-MM), nome_no_doc, cpf_no_doc, total_vencimentos, total_descontos, valor_liquido, degradacao (nenhuma / torta / desfocada / print)`

### `rubricas.csv` (uma por linha do holerite; gabarito da classificação)
`arquivo, codigo, descricao, tipo (vencimento / desconto), valor, conta_como_renda (sim / nao)`

### `gabarito.csv` (um por cliente; preenchido à mão, sem IA)
`cliente_id, cenario, regra_testada, renda_valida_esperada, decisao_esperada (aprova / reprova / revisao), motivo_esperado`