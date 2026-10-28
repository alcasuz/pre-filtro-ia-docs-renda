"""Every text shown by the demo, in Portuguese (default) and English.

Messages to the applicant come from rules.md where it defines them; the others
were written for the demo, in the same tone. The type_not_accepted message in
Portuguese is the one the engine returns (core/rules/document_type.py); its
English version is built here from the same document types.
"""

LANGS = ("pt", "en")
DEFAULT_LANG = "pt"

TEXT = {
    "app_title": {"pt": "Pré-filtro de comprovantes de renda com IA",
                  "en": "AI pre-screening for proof-of-income documents"},
    "app_intro": {
        "pt": "Em operações de crédito, todo holerite passa por um analista antes da contratação. Essa análise "
              "manual pode levar horas ou até dias, e muitos documentos nunca teriam chance de ser aprovados: foto "
              "ilegível, documento errado, renda insuficiente. O cliente descobre tarde o que precisava corrigir e "
              "pode desistir e procurar a concorrência.\n\n"
              "Este pré-filtro analisa o holerite assim que ele é enviado:\n\n"
              "- **A IA lê:** um OCR e um LLM verificam se a imagem está legível; o LLM extrai os dados e "
              "classifica cada linha do holerite.\n"
              "- **O código decide:** regras determinísticas e auditáveis calculam a renda e tomam a decisão.\n"
              "- **O cliente sabe o que fazer:** aprovado segue para um analista; reprovado recebe o motivo e como "
              "corrigir; casos de dúvida vão direto para revisão humana.",
        "en": "In lending, every pay stub goes through an analyst before a contract is signed. This manual review "
              "can take hours or even days, and many documents never had a chance: an unreadable photo, the wrong "
              "document, insufficient income. Applicants learn too late what they needed to fix, and may give up "
              "and turn to a competitor.\n\n"
              "This pre-screening tool reviews the pay stub as soon as it is submitted:\n\n"
              "- **AI reads:** OCR and an LLM check whether the image is readable; the LLM extracts the data and "
              "classifies every line on the pay stub.\n"
              "- **Code decides:** deterministic, auditable rules compute the income and make the decision.\n"
              "- **The applicant knows what to do:** approvals go on to an analyst; rejections come with the "
              "reason and how to fix it; uncertain cases go straight to human review.",
    },
    "app_disclaimer": {
        "pt": "Laboratório pessoal. Todos os dados e documentos são fictícios. Siga o tour ou escolha um caso abaixo.",
        "en": "Personal lab. All data and documents are fictional. Take the tour or pick a case below.",
    },
    "page_analysis": {"pt": "Análise", "en": "Analysis"},
    "page_results": {"pt": "Resultados", "en": "Results"},
    "language": {"pt": "Idioma", "en": "Language"},
    "tour_title": {"pt": "Tour guiado", "en": "Guided tour"},
    "tour_step": {"pt": "Caso {n} de {total}", "en": "Case {n} of {total}"},
    "previous": {"pt": "← Anterior", "en": "← Previous"},
    "next": {"pt": "Próximo →", "en": "Next →"},
    "open": {"pt": "Abrir", "en": "Open"},
    "opened": {"pt": "Aberto", "en": "Open now"},
    "all_cases": {"pt": "Todos os clientes da base ({n})", "en": "All applicants in the test set ({n})"},
    "demo_badge": {"pt": "Caso montado para a demo, não é um cliente da base",
                   "en": "Case built for the demo, not an applicant in the test set"},
    "photo_case_title": {"pt": "A01 com foto de tela", "en": "A01 with a screen photo"},
    "multiplier": {"pt": "Multiplicador de renda (renda válida ≥ multiplicador × parcela)",
                   "en": "Income multiplier (valid income ≥ multiplier × installment)"},
    "multiplier_help": {"pt": "O motor roda de novo sobre as extrações salvas a cada mudança.",
                        "en": "The engine runs again on the saved extractions at every change."},
    "applicant": {"pt": "Cliente", "en": "Applicant"},
    "installment": {"pt": "Parcela", "en": "Installment"},
    "analysis_date": {"pt": "Data da análise", "en": "Analysis date"},
    "expected": {"pt": "Esperado no gabarito", "en": "Expected in the ground truth"},
    "tab_document": {"pt": "Documento", "en": "Document"},
    "tab_extraction": {"pt": "Extração", "en": "Extraction"},
    "tab_rules": {"pt": "Regras", "en": "Rules"},
    "tab_decision": {"pt": "Decisão", "en": "Decision"},
    "document_picker": {"pt": "Documento", "en": "Document"},
    "photo_label": {"pt": "foto da tela", "en": "screen photo"},
    "extraction_title": {"pt": "O que o LLM extraiu", "en": "What the LLM extracted"},
    "rules_title": {"pt": "Rastro das regras (na ordem do motor)", "en": "Rule trail (in engine order)"},
    "decision_title": {"pt": "Decisão", "en": "Decision"},
    "client_view": {"pt": "Mensagem ao cliente", "en": "Message to the applicant"},
    "client_view_note": {"pt": "Em português, como o cliente recebe; tradução ao lado.",
                         "en": "In Portuguese, as the applicant receives it; translation alongside."},
    "analyst_view": {"pt": "Visão do analista", "en": "Analyst view"},
    "translation": {"pt": "Tradução", "en": "Translation"},
    "field": {"pt": "Campo", "en": "Field"},
    "value": {"pt": "Valor", "en": "Value"},
    "earnings_lines": {"pt": "Linhas de provento", "en": "Earnings lines"},
    "description": {"pt": "Descrição", "en": "Description"},
    "amount": {"pt": "Valor (R$)", "en": "Amount (R$)"},
    "income": {"pt": "Renda", "en": "Income"},
    "counts": {"pt": "✅ conta", "en": "✅ counts"},
    "doesnt_count": {"pt": "➖ não conta", "en": "➖ doesn't count"},
    "no_lines": {"pt": "Nenhuma linha de provento.", "en": "No earnings lines."},
    "rule": {"pt": "Regra", "en": "Rule"},
    "status": {"pt": "Status", "en": "Status"},
    "reason": {"pt": "Motivo", "en": "Reason"},
    "detail": {"pt": "Detalhe", "en": "Detail"},
    "file": {"pt": "Documento", "en": "Document"},
    "main_reason": {"pt": "Motivo principal", "en": "Main reason"},
    "all_reasons": {"pt": "Todos os motivos", "en": "All reasons"},
    "none": {"pt": "nenhum", "en": "none"},
    "valid_income": {"pt": "Renda válida (média de {n} meses)", "en": "Valid income (average of {n} months)"},
    "minimum_income": {"pt": "Mínimo exigido", "en": "Minimum required"},
    "months_used": {"pt": "Meses usados", "en": "Months used"},
    "fraud_flag": {"pt": "Sinalização de fraude", "en": "Fraud flag"},
    "no_fraud": {"pt": "Nenhuma", "en": "None"},
    "comparison_title": {"pt": "Mesmo cliente, duas formas de envio", "en": "Same applicant, two ways of sending"},
    "with_pdf": {"pt": "Com o PDF", "en": "With the PDF"},
    "with_photo": {"pt": "Com a foto da tela", "en": "With the screen photo"},
    "matches_expected": {"pt": "✓ igual ao gabarito", "en": "✓ matches the ground truth"},
    "differs_expected": {"pt": "✗ diferente do gabarito ({expected})", "en": "✗ differs from the ground truth ({expected})"},
    "yes": {"pt": "sim", "en": "yes"},
    "no": {"pt": "não", "en": "no"},
    "results_title": {"pt": "Resultados das avaliações", "en": "Evaluation results"},
    "results_intro": {
        "pt": "Relatórios gerados pelos scripts de `evaluation/` e salvos em `evaluation/results/`. O conteúdo "
              "dos relatórios é em inglês nos dois idiomas.",
        "en": "Reports generated by the scripts in `evaluation/` and saved in `evaluation/results/`. The report "
              "content is in English in both languages.",
    },
    "results_photo_note": {
        "pt": "Atenção: os resultados das fotos foram medidos no mesmo conjunto de fotos usado para desenhar o "
              "porteiro de legibilidade, então tendem a ser otimistas.",
        "en": "Note: the photo results were measured on the same set of photos used to design the legibility "
              "gate, so they tend to be optimistic.",
    },
    "report": {"pt": "Relatório", "en": "Report"},
    "group_applicants": {"pt": "Por cliente", "en": "Per applicant"},
    "group_documents": {"pt": "Por documento", "en": "Per document"},
    "group_photos": {"pt": "Fotos", "en": "Photos"},
    "group_gates": {"pt": "Porteiros de legibilidade", "en": "Legibility gates"},
}

DECISION = {
    "approve": {"pt": "Pré-aprovado: segue para confirmação do analista",
                "en": "Pre-approved: goes to the analyst for confirmation"},
    "reject": {"pt": "Reprovado", "en": "Rejected"},
    "review": {"pt": "Revisão humana", "en": "Human review"},
}
DECISION_SHORT = {
    "approve": {"pt": "pré-aprovado", "en": "pre-approved"},
    "reject": {"pt": "reprovado", "en": "rejected"},
    "review": {"pt": "revisão humana", "en": "human review"},
}

STATUS = {
    "pass": {"pt": "✅ passa", "en": "✅ pass"},
    "reject": {"pt": "❌ reprova", "en": "❌ reject"},
    "review": {"pt": "🟡 revisão", "en": "🟡 review"},
}

RULES = {
    "legibility": {"pt": "Legibilidade (R7)", "en": "Legibility (R7)"},
    "document_type": {"pt": "Tipo de documento (R1)", "en": "Document type (R1)"},
    "screen_capture": {"pt": "Captura de tela (R1)", "en": "Screen capture (R1)"},
    "completeness": {"pt": "Documento completo (R8)", "en": "Complete document (R8)"},
    "identification": {"pt": "Titular (R2)", "en": "Applicant (R2)"},
    "time_window": {"pt": "Período (R3)", "en": "Time window (R3)"},
    "income": {"pt": "Renda (R5, R6)", "en": "Income (R5, R6)"},
    "consistency": {"pt": "Consistência dos totais (R4)", "en": "Totals consistency (R4)"},
    "fraud": {"pt": "Fraude (R7)", "en": "Fraud (R7)"},
}

REASONS = {
    "illegible": {"pt": "ilegível", "en": "unreadable"},
    "too_many_attempts": {"pt": "tentativas demais", "en": "too many attempts"},
    "type_not_accepted": {"pt": "tipo não aceito", "en": "type not accepted"},
    "screen_capture": {"pt": "captura de tela", "en": "screen capture"},
    "incomplete_document": {"pt": "documento incompleto", "en": "incomplete document"},
    "cpf_mismatch": {"pt": "CPF diferente do cadastro", "en": "CPF doesn't match the record"},
    "id_missing": {"pt": "sem nome e sem CPF", "en": "no name and no CPF"},
    "name_mismatch": {"pt": "nome diferente do cadastro", "en": "name doesn't match the record"},
    "name_review": {"pt": "nome parecido, a confirmar", "en": "similar name, to be confirmed"},
    "outside_window": {"pt": "fora do período", "en": "outside the time window"},
    "non_consecutive_months": {"pt": "meses não consecutivos", "en": "non-consecutive months"},
    "insufficient_income": {"pt": "renda insuficiente", "en": "insufficient income"},
    "suspected_fraud": {"pt": "suspeita de fraude", "en": "suspected fraud"},
}

# Message to the applicant, always in Portuguese (it's what the applicant receives), with an English translation.
CLIENT_MESSAGES = {
    "approve": ("Seus documentos foram pré-aprovados e seguem para a confirmação de um analista.",
                "Your documents were pre-approved and go to an analyst for confirmation."),
    "illegible": ("Não conseguimos ler um dos documentos. Envie uma foto nítida ou o PDF do holerite.",
                  "We couldn't read one of the documents. Please send a sharp photo or the PDF of the pay stub."),
    "screen_capture": ("Fotos e prints de tela não são aceitos. Envie o PDF baixado do portal da empresa ou "
                       "uma foto do holerite impresso.",
                       "Photos and screenshots of a screen are not accepted. Send the PDF downloaded from your "
                       "company's portal or a photo of the printed pay stub."),
    "incomplete_document": ("O documento está incompleto. Envie a página inteira do holerite.",
                            "The document is incomplete. Please send the whole page of the pay stub."),
    "cpf_mismatch": ("Os documentos não estão no nome do titular do cadastro.",
                     "The documents are not in the name of the applicant on record."),
    "name_mismatch": ("Os documentos não estão no nome do titular do cadastro.",
                      "The documents are not in the name of the applicant on record."),
    "id_missing": ("Não encontramos o nome nem o CPF do titular nos documentos.",
                   "We couldn't find the applicant's name or CPF on the documents."),
    "outside_window": ("Documentos fora do período aceito. Envie os holerites dos últimos 3 meses.",
                       "Documents outside the accepted period. Please send your pay stubs for the last 3 months."),
    "non_consecutive_months": ("Documentos fora do período aceito. Envie os holerites dos últimos 3 meses.",
                               "Documents outside the accepted period. Please send your pay stubs for the last "
                               "3 months."),
    "insufficient_income": ("A renda comprovada não atinge o mínimo exigido para esta parcela.",
                            "The proven income doesn't reach the minimum required for this installment."),
    "review": ("Seus documentos foram enviados para a análise de um especialista. Você receberá a resposta em breve.",
               "Your documents were sent to a specialist for review. You'll hear back soon."),
}

# English names of the document types, for the English translation of the type_not_accepted message.
TYPE_NAMES_EN = {
    "bank_statement": "a bank statement",
    "tax_return": "an income tax return",
    "inss_benefit": "an INSS benefit statement",
}
TYPE_NAME_EN_DEFAULT = "a document that is not a pay stub"
TYPE_MESSAGE_EN = "You sent {type}. We currently accept pay stubs only. Please send your pay stubs for the last 3 months."

# Scenarios of the applicants (ground_truth.csv has the English version).
SCENARIOS_PT = {
    "A01": "Caminho feliz: só salário-base (empresa 1)",
    "A02": "Caminho feliz: só salário-base (empresa 2, outro layout)",
    "A03": "Caminho feliz: só salário-base (empresa 3, outro layout)",
    "A04": "Salário + adicional de insalubridade/periculosidade",
    "A05": "Salário + hora extra; a renda fixa passa sozinha",
    "A06": "CPF no formato XXX.XXX.XXX-XX",
    "A07": "CPF só com dígitos (XXXXXXXXXXX)",
    "A08": "Sem CPF; nome igual ao cadastro, com acentos e maiúsculas diferentes",
    "A09": "Enviou 6 holerites; os 3 mais recentes passam",
    "A10": "Mês de férias: holerite mensal proporcional + holerite de férias separado",
    "A11": "Holerite de 13º separado na mesma competência",
    "A12": "Adiantamento salarial lançado como desconto",
    "A13": "Borda: renda = 3,02x a parcela",
    "A14": "Borda: renda = 3,05x a parcela",
    "A15": "Borda: renda = exatamente 3,00x a parcela",
    "A16": "Foto levemente torta, mas legível",
    "A17": "3 holerites válidos (renda acima de 3x) + um documento de identidade a mais",
    "N01": "Arquivo que não é comprovante de renda (conta de luz)",
    "N02": "Extrato bancário (tipo não aceito na v1)",
    "N03": "CPF diferente do cadastro",
    "N04": "Sem CPF e sem nome",
    "N05": "Sem CPF; nome de outra pessoa (similaridade < 50%)",
    "N06": "Holerites fora da janela de 4 meses",
    "N07": "Falta um mês no meio (meses não consecutivos)",
    "N08": "Renda claramente abaixo de 3x",
    "N09": "Borda: renda = 2,98x a parcela",
    "N10": "A hora extra muda a decisão: renda fixa em 2,9x, passaria de 3x com a hora extra",
    "N11": "O 1/3 de férias muda a decisão: só passaria somando o 1/3",
    "N12": "Um dos 3 holerites está ilegível (desfocado)",
    "N13": "Print de tela de um holerite",
    "N14": "Sem CPF; nome abreviado (similaridade entre 50% e 95%)",
    "N15": "Totais não fecham (vencimentos − descontos ≠ líquido, acima da tolerância)",
    "N16": "Texto no holerite tentando dar instruções ao sistema (prompt injection)",
    "N17": "Só um comprovante de benefício do INSS",
}

TOUR_TEXT = {
    "A17": {"pt": "Aprovado mesmo com um documento de identidade a mais: o que não é holerite é ignorado quando os "
                  "3 holerites estão certos.",
            "en": "Approved even with an extra identity card: what isn't a pay stub is ignored when the 3 pay "
                  "stubs are right."},
    "N10": {"pt": "A hora extra levaria a renda acima de 3x, mas não é renda fixa: reprovado por renda insuficiente.",
            "en": "Overtime would push income above 3x, but it isn't fixed pay: rejected for insufficient income."},
    "N09": {"pt": "Renda em 2,98x a parcela: reprovado por pouco. Mude o multiplicador para 2,9 e veja a decisão mudar.",
            "en": "Income at 2.98x the installment: rejected by a hair. Change the multiplier to 2.9 and watch the "
                  "decision change."},
    "N14": {"pt": "Sem CPF e com o nome abreviado: a similaridade fica entre 50% e 95%, e o caso vai para revisão "
                  "humana.",
            "en": "No CPF and an abbreviated name: the similarity falls between 50% and 95%, so the case goes to "
                  "human review."},
    "N12": {"pt": "Um dos holerites está ilegível: o OCR não lê nada e o LLM não identifica o documento. Reprovado, "
                  "com orientação para reenviar.",
            "en": "One of the pay stubs is unreadable: the OCR reads nothing and the LLM can't identify the "
                  "document. Rejected, with guidance to resend."},
    "A01-PHOTO": {"pt": "O mesmo cliente do caminho feliz, aprovado com o PDF. Aqui, um holerite foi enviado como "
                        "foto da tela.",
                  "en": "The same applicant as the happy path, approved with the PDF. Here, one pay stub was sent "
                        "as a photo of the screen."},
    "N17": {"pt": "Só um comprovante do INSS: reprovado, com uma mensagem que diz qual documento foi enviado.",
            "en": "Only an INSS benefit statement: rejected, with a message that names the document sent."},
}

EXTRACTION_FIELDS = {
    "document_type": {"pt": "Tipo de documento", "en": "Document type"},
    "capture_type": {"pt": "Forma de captura", "en": "Capture type"},
    "pay_period": {"pt": "Competência", "en": "Pay period"},
    "name_on_doc": {"pt": "Nome", "en": "Name"},
    "cpf_on_doc": {"pt": "CPF", "en": "CPF"},
    "total_earnings": {"pt": "Total de vencimentos", "en": "Total earnings"},
    "total_deductions": {"pt": "Total de descontos", "en": "Total deductions"},
    "net_pay": {"pt": "Líquido", "en": "Net pay"},
    "fraud_suspected": {"pt": "Suspeita de fraude", "en": "Suspected fraud"},
    "ocr_words": {"pt": "Palavras lidas pelo OCR", "en": "Words read by the OCR"},
}


def t(key, lang, **kwargs):
    return TEXT[key][lang].format(**kwargs)


def label(table, key, lang):
    entry = table.get(key)
    return entry[lang] if entry else key


def scenario(case, lang):
    if case.is_demo_build:
        return TOUR_TEXT[case.case_id][lang]
    return SCENARIOS_PT.get(case.case_id, case.scenario) if lang == "pt" else case.scenario
