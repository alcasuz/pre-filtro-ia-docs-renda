# Regras do pré-filtro (negócio fictício)

> Laboratório pessoal. Regras e parâmetros inventados para fins de estudo; não representam a política de nenhuma empresa.
> Versão: v1.0 (24/10/2026)

---

## Premissas do projeto

1. **O LLM só lê e extrai. Toda conta e toda decisão são feitas pelo código.** O LLM devolve um JSON com os dados do documento; o motor de regras calcula a renda e decide.
2. **Data de referência fixa:** todo prazo é contado a partir da coluna `data_analise` do `cadastros.csv`, nunca da data de hoje. Assim o eval é determinístico: mesma entrada, mesma resposta.
3. **Comparação sempre com o cadastro** (`cadastros.csv`), não com documento de identidade.
4. **Instruções escritas dentro do documento são dados, não comandos.** Nenhum texto do documento muda a decisão.

## Escopo da v1

- **Aceito:** holerite / contracheque.
- **Fora da v1** (regras guardadas na seção "Backlog v2"): extrato bancário, benefício INSS, imposto de renda, pró-labore.

## Fluxo de decisão

1. **Tipificação** [LLM]: o arquivo é um documento de renda? Qual tipo?
2. **Aceite do tipo** [CÓDIGO]: tipo aceito na v1 = holerite.
3. **Extração** [LLM]: gera o JSON com os metadados do documento.
4. **Decisão** [CÓDIGO]: o motor de regras aplica as regras abaixo.

Saídas possíveis:
- **Aprovado pela IA → segue para revisão humana**, que confirma.
- **Reprovado → reprovação automática**, com motivo informado ao usuário.
- **Revisão humana direta**: casos de suspeita de fraude ou adulteração.

---

## Regras da v1 (holerite)

Para cada regra, preencher **Quem faz**: `[LLM]` (ler/classificar) ou `[CÓDIGO]` (calcular/decidir). Uma regra pode ter as duas partes.

### R1. Tipo de documento
- Não é documento de renda → **reprova** (motivo: arquivo não é comprovante de renda).
- É documento de renda, mas de tipo não aceito na v1 → **reprova** (motivo: tipo não aceito).
- Print de tela ou sinais de edição → **revisão humana** (motivo: prevenção de fraude).
- Quem faz: `[LLM]` define o tipo de documento e marca no JSON a sinalização de suspeita de fraude (print ou sinais de edição); `[CÓDIGO]` lê o tipo e a sinalização e decide entre aprovar, reprovar ou mandar para revisão humana.

### R2. Identificação do titular
- O documento precisa ter o nome **ou** o CPF. Sem nenhum dos dois → **reprova**.
- Se tiver CPF, ele precisa ser igual ao do cadastro. Diferente → **reprova**. Igual → titular confirmado, e o nome não é avaliado.
- Se não tiver CPF, comparar o nome com o do cadastro (após normalizar maiúsculas, acentos e espaços):
  - similaridade ≥ 95% → ok;
  - similaridade ≥ 50% e < 95% → **revisão humana**;
  - similaridade < 50% → **reprova** (motivo: nome não confere com o cadastro).
- Os limites de 95% e 50% são hipóteses iniciais e serão calibrados com a base de eval.
- Quem faz: `[LLM]` extrai o nome e o CPF como aparecem no documento; `[CÓDIGO]` normaliza o CPF (mantém só os 11 dígitos, qualquer que seja o formato: XXX.XXX.XXX-XX, XXXXXXXXXXX etc.), valida os dígitos verificadores, compara com o cadastro, calcula a similaridade do nome e decide.

### R3. Período
- 3 holerites de competências mensais consecutivas, todos dentro dos 4 meses anteriores à `data_analise`.
- Fora da janela ou menos de 3 holerites → **reprova**. Mensagem ao usuário: "Documentos fora do período aceito. Envie os holerites dos últimos 3 meses."
- Se vierem mais de 3 holerites (ex.: 6 meses), só os 3 mais recentes entram no cálculo.
- Se vierem dois holerites da mesma competência:
  - holerite de férias separado: a remuneração de férias (sem o 1/3) soma ao holerite mensal daquela competência;
  - holerite de 13º separado: não entra no cálculo.
- Quem faz: `[LLM]` extrai a competência e a normaliza no formato AAAA-MM (ex.: "outubro/26" → 2026-10); `[CÓDIGO]` valida o formato, verifica se há 3 meses dentro da janela e seleciona os 3 mais recentes.

### R4. Consistência do holerite
- |proventos − descontos − líquido| ≤ R$100.
- Fora da tolerância → **revisão humana** (sinal de adulteração).
- Quem faz: `[LLM]` extrai total de proventos, total de descontos e valor líquido; `[CÓDIGO]` faz a conta e decide.

### R5. Verbas que contam e que não contam
- **Contam (remuneração fixa):** salário-base, adicional noturno (decisão: tratado como fixo), insalubridade, periculosidade, gratificação de função, anuênio/quinquênio, remuneração de férias (sem o 1/3; repõe o salário dos dias de férias).
- **Não contam:** hora extra, comissão, PLR, bônus, 1/3 constitucional de férias, 13º salário, reembolsos, diárias, ajuda de custo.
- Como a renda é calculada sobre as verbas fixas brutas (R6), descontos como adiantamento salarial, INSS e IRRF não entram no cálculo.
- Quem faz: `[LLM]` extrai cada linha de provento (rubrica e valor) e classifica como "conta" ou "não conta"; `[CÓDIGO]` soma as linhas classificadas como "conta". O LLM não devolve o total.

### R6. Renda mínima
- Renda do mês = soma das verbas fixas brutas (lista "Contam" da R5).
- Renda válida = média dos 3 meses (soma ÷ 3).
- Renda válida ≥ 3 × valor da parcela → **aprovado pela IA → revisão humana**.
- Renda válida < 3 × parcela → **reprova** (motivo: renda insuficiente).
- Quem faz: `[CÓDIGO]`, a partir das linhas classificadas na R5.

### R7. Qualidade e segurança
- Imagem ilegível, cortada ou desfocada → **reprova com orientação para reenviar**.
- Documento com texto tentando dar instruções ao sistema (prompt injection) → **revisão humana** (suspeita de fraude).
- Quem faz (legibilidade): `[OCR]` gera a confiança média da leitura; `[CÓDIGO]` compara com um limite mínimo (a calibrar no eval) e decide se o documento é ilegível.
- Quem faz (fraude): `[LLM]` marca no JSON a sinalização de suspeita de fraude (inclusive prompt injection), com uma justificativa curta; `[CÓDIGO]` lê a sinalização e decide.

---

## Limitações conhecidas da v1

1. **Férias pagas antes da competência:** as férias costumam ser pagas antes do início do descanso, e o recibo pode trazer a competência do mês anterior. Nesse caso, um mês fica inflado e o outro, reduzido. Na v1, vale a competência escrita no documento.

## Hipóteses a testar na etapa 2

- **Rota OCR + LLM × LLM lendo a imagem direto:** comparar acerto, tokens e latência.
- **OCR:** Tesseract (open source, leve, roda no Mac e no servidor da demo, devolve confiança por palavra).
- **Acurácia por tipo de campo:** medir separadamente a classificação das rubricas e a leitura dos valores, nas duas rotas.

---

## Backlog v2 (fora da v1)

### Extrato bancário
- Conta: Pix, TED e DOC recebidos de pessoa física ou jurídica, desde que não sejam do próprio titular.
- Não conta: transferência entre contas da mesma titularidade, resgate de investimento (movimentação de patrimônio, não renda), rendimentos de aplicações, crédito de empréstimo, estornos e devoluções, cashback.
- Pergunta aberta: como distinguir a renda de quem vende como pessoa física (ex.: pipoqueiro que recebe muitos Pix pequenos de pessoas diferentes) de uma entrada pontual que não é renda (ex.: amigo que empresta dinheiro)? Hipótese a testar: recorrência.

### Benefício INSS
- Não é aceito auxílio-doença nem outro benefício temporário.

### Imposto de renda
- Renda anual = rendimentos tributáveis + não tributáveis; CLT divide por 13, demais por 12.
- ⚠️ Revisar antes da v2: o 13º fica em "tributação exclusiva/definitiva" (não entra nos tributáveis), e os não tributáveis incluem itens que não são renda recorrente (ex.: saque de FGTS, indenizações, rendimento de poupança).

### Pró-labore
- Mesmas regras do holerite.
- A empresa precisa estar no nome da pessoa: exige um documento societário (ex.: contrato social ou cartão CNPJ).