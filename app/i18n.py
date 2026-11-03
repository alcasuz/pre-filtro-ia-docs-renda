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
    "hero_badge": {"pt": "Laboratório pessoal · dados fictícios", "en": "Personal lab · fictional data"},
    "hero_lede": {"pt": "Holerite analisado em segundos: a IA lê, regras auditáveis decidem e o cliente sabe o que "
                        "corrigir.",
                  "en": "A pay stub reviewed in seconds: AI reads it, auditable rules decide, and the applicant "
                        "knows what to fix."},
    "hero_problem": {"pt": "Hoje todo holerite espera horas ou dias por um analista, e o cliente descobre tarde que "
                           "mandou uma foto ilegível ou o documento errado.",
                     "en": "Today every pay stub waits hours or days for an analyst, and applicants learn too late "
                           "that they sent an unreadable photo or the wrong document."},
    "step1_title": {"pt": "A IA lê", "en": "AI reads"},
    "step1_text": {"pt": "Um OCR e um LLM conferem se a imagem é legível; o LLM extrai os dados e classifica cada "
                         "linha do holerite.",
                   "en": "OCR and an LLM check that the image is readable; the LLM extracts the data and classifies "
                         "every line of the pay stub."},
    "step2_title": {"pt": "O código decide", "en": "Code decides"},
    "step2_text": {"pt": "Regras determinísticas e auditáveis calculam a renda e tomam a decisão. A IA não decide.",
                   "en": "Deterministic, auditable rules compute the income and make the decision. The AI doesn't "
                         "decide."},
    "step3_title": {"pt": "O cliente sabe o que fazer", "en": "The applicant knows what to do"},
    "step3_text": {"pt": "Aprovado segue para um analista; reprovado recebe o motivo e como corrigir; dúvida vai para "
                         "revisão humana.",
                   "en": "Approvals go on to an analyst; rejections get the reason and the fix; doubts go to human "
                         "review."},
    "proof_title": {"pt": "Resultado nas avaliações", "en": "Evaluation results"},
    "start_tour": {"pt": "Começar o tour", "en": "Start the tour"},
    "tour_intro": {"pt": "8 casos, um por regra importante. Abra um caso para ver o documento, o que a IA leu e por "
                         "que o código decidiu assim.",
                   "en": "8 cases, one per key rule. Open a case to see the document, what the AI read and why the "
                         "code decided that way."},
    "view_case": {"pt": "Ver caso", "en": "View case"},
    "filter_all": {"pt": "Todos", "en": "All"},
    "group_who": {"pt": "Quem e quando", "en": "Who and when"},
    "group_values": {"pt": "Valores", "en": "Amounts"},
    "group_capture": {"pt": "Como o documento chegou", "en": "How the document arrived"},
    "document_n": {"pt": "Documento {n}", "en": "Document {n}"},
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
    "cta_title": {"pt": "Quer ver como foi construído?", "en": "Want to see how it was built?"},
    "cta_text": {"pt": "Regras, avaliações, decisões de produto e o código estão no repositório.",
                 "en": "Rules, evaluations, product decisions and the code are in the repository."},
    "cta_github": {"pt": "Repositório no GitHub", "en": "GitHub repository"},
    "cta_linkedin": {"pt": "Suzane Lima no LinkedIn", "en": "Suzane Lima on LinkedIn"},
    "footer": {"pt": "Laboratório pessoal com dados fictícios", "en": "Personal lab with fictional data"},
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
    "section_read": {"pt": "1. A IA leu", "en": "1. The AI read"},
    "section_read_note": {"pt": "O LLM extraiu os campos de cada documento; o OCR conferiu se a imagem é legível.",
                          "en": "The LLM extracted the fields of each document; the OCR checked that the image is "
                                "readable."},
    "section_rules": {"pt": "2. As regras decidiram", "en": "2. The rules decided"},
    "section_rules_note": {"pt": "Regras determinísticas no código, na ordem do motor. As que não passaram vêm "
                                 "primeiro.",
                           "en": "Deterministic rules in code, in engine order. Those that didn't pass come first."},
    "section_analyst": {"pt": "3. O analista recebeu", "en": "3. The analyst was told"},
    "rules_passed": {"pt": "Regras que passaram ({n})", "en": "Rules that passed ({n})"},
    "decisive": {"pt": "decidiu o caso", "en": "decided the case"},
    "rules_word": {"pt": "Regras", "en": "Rules"},
    "approve_next": {"pt": "Segue para a confirmação de um analista.", "en": "Goes on to an analyst for confirmation."},
    "client_message": {"pt": "Mensagem enviada ao cliente", "en": "Message sent to the applicant"},
    "original_pt": {"pt": "Enviada em português: {text}", "en": "Sent in Portuguese: {text}"},
    "policy_sim": {"pt": "Simular política", "en": "Simulate policy"},
    "not_found": {"pt": "não encontrado", "en": "not found"},
    "totals_missing": {"pt": "totais ausentes", "en": "totals missing"},
    "analyst_view": {"pt": "Visão do analista", "en": "Analyst view"},
    "field": {"pt": "Campo", "en": "Field"},
    "value": {"pt": "Valor", "en": "Value"},
    "earnings_lines": {"pt": "Linhas de provento", "en": "Earnings lines"},
    "description": {"pt": "Descrição", "en": "Description"},
    "amount": {"pt": "Valor (R$)", "en": "Amount (R$)"},
    "income": {"pt": "Renda", "en": "Income"},
    "counts": {"pt": "conta como renda", "en": "counts as income"},
    "doesnt_count": {"pt": "não conta", "en": "doesn't count"},
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
        "pt": "Como o pré-filtro se saiu numa base de teste fictícia: {applicants} clientes, {documents} documentos e "
              "{photos} fotos de celular. Para cada cliente, a resposta certa foi definida à mão antes do teste.",
        "en": "How the pre-screening did on a fictional test set: {applicants} applicants, {documents} documents and "
              "{photos} phone photos. For each applicant, the right answer was set by hand before the test.",
    },
    "tile_decision_q": {"pt": "O pré-filtro decidiu certo?", "en": "Did the pre-screening decide right?"},
    "tile_decision_v": {"pt": "{right} de {total}", "en": "{right} of {total}"},
    "tile_decision_c": {"pt": "clientes com a mesma decisão da resposta certa.",
                        "en": "applicants got the same decision as the right answer."},
    "tile_decision_short": {"pt": "decisões certas", "en": "right decisions"},
    "tile_good_q": {"pt": "Algum cliente bom foi recusado?", "en": "Was any good applicant rejected?"},
    "tile_good_none": {"pt": "Nenhum", "en": "None"},
    "tile_good_c": {"pt": "dos {total} que deviam ser aprovados. É o erro mais caro: perder um cliente bom.",
                    "en": "of the {total} who should be approved. It's the costliest mistake: losing a good applicant."},
    "tile_good_short": {"pt": "clientes bons recusados", "en": "good applicants rejected"},
    "tile_time_q": {"pt": "Quanto tempo leva?", "en": "How long does it take?"},
    "tile_time_v": {"pt": "{p50} s", "en": "{p50} s"},
    "tile_time_c": {"pt": "por documento, e 9 em cada 10 ficam prontos em até {p90} s. A análise manual leva horas "
                          "ou dias.",
                    "en": "per document, and 9 in 10 are done within {p90} s. Manual review takes hours or days."},
    "tile_time_short": {"pt": "por documento", "en": "per document"},
    "tile_photo_q": {"pt": "E com foto de celular?", "en": "And with a phone photo?"},
    "tile_photo_c": {"pt": "fotos tiradas no celular levaram à decisão certa.",
                     "en": "photos taken on a phone led to the right decision."},
    "tile_photo_short": {"pt": "certas com foto de celular", "en": "right with a phone photo"},
    "invented_alert": {"pt": "Atenção: em {n} vez(es), a IA preencheu um campo que não existe no documento.",
                       "en": "Warning: {n} time(s), the AI filled a field that isn't on the document."},
    "classes_title": {"pt": "Decisões por tipo de cliente", "en": "Decisions by type of applicant"},
    "classes_intro": {"pt": "Cada barra mostra quantos clientes de cada grupo receberam a decisão certa.",
                      "en": "Each bar shows how many applicants in each group got the right decision."},
    "class_approve": {"pt": "Deviam ser pré-aprovados", "en": "Should be pre-approved"},
    "class_reject": {"pt": "Deviam ser reprovados", "en": "Should be rejected"},
    "class_review": {"pt": "Deviam ir para revisão humana", "en": "Should go to human review"},
    "classes_reason": {"pt": "O motivo da decisão também bateu em {right} de {total} clientes.",
                       "en": "The reason for the decision also matched for {right} of {total} applicants."},
    "fields_title": {"pt": "A IA leu os dados certos?", "en": "Did the AI read the right data?"},
    "fields_intro": {"pt": "Acerto de cada campo lido pela IA, comparado com o que está impresso no documento. O tipo "
                           "vale para {scored} documentos; os demais campos, para os {stubs} holerites.",
                     "en": "How often the AI read each field right, compared with what is printed on the document. "
                           "The type covers {scored} documents; the other fields, the {stubs} pay stubs."},
    "lines_all_right": {"pt": "Todas as {n} linhas de provento foram encontradas e classificadas corretamente como "
                              "renda ou não.",
                        "en": "All {n} earnings lines were found and correctly classified as income or not."},
    "lines_some": {"pt": "Linhas de provento: {found} de {total} encontradas; {right} classificadas corretamente como "
                         "renda ou não.",
                   "en": "Earnings lines: {found} of {total} found; {right} correctly classified as income or not."},
    "fraud_line": {"pt": "Tentativas de fraude encontradas: {detected} de {total}; {alarms}.",
                   "en": "Fraud attempts found: {detected} of {total}; {alarms}."},
    "false_alarms_0": {"pt": "nenhum alarme falso", "en": "no false alarms"},
    "false_alarms_1": {"pt": "1 alarme falso", "en": "1 false alarm"},
    "false_alarms_n": {"pt": "{n} alarmes falsos", "en": "{n} false alarms"},
    "photos_title": {"pt": "Fotos de celular: o que mais atrapalha", "en": "Phone photos: what gets in the way"},
    "photos_intro": {"pt": "Acerto dos campos lidos em {readable} fotos legíveis, por tipo de defeito, do pior para o "
                           "melhor.",
                     "en": "Fields read right in {readable} readable photos, by type of defect, worst first."},
    "photo_count_1": {"pt": "1 foto", "en": "1 photo"},
    "photo_count_n": {"pt": "{n} fotos", "en": "{n} photos"},
    "results_photo_note": {
        "pt": "Essas fotos também foram usadas para ajustar o sistema, então o resultado tende a ser otimista.",
        "en": "These photos were also used to tune the system, so the result tends to be optimistic.",
    },
    "of_n": {"pt": "{right} de {total}", "en": "{right} of {total}"},
    "source_files": {"pt": "Arquivos de origem no GitHub (em inglês)", "en": "Source files on GitHub"},
    "results_missing": {"pt": "Os resumos das avaliações ainda não foram gerados.",
                        "en": "The evaluation summaries haven't been generated yet."},
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
    "pass": {"pt": "passou", "en": "passed"},
    "reject": {"pt": "reprovou", "en": "rejected"},
    "review": {"pt": "revisão", "en": "review"},
    "na": {"pt": "não avaliada", "en": "not evaluated"},
}
# "Regras: 1 reprovou · 7 passaram" — (singular, plural) per status.
COUNT_WORDS = {
    "reject": {"pt": ("reprovou", "reprovaram"), "en": ("rejected", "rejected")},
    "review": {"pt": ("em revisão", "em revisão"), "en": ("in review", "in review")},
    "na": {"pt": ("não avaliada", "não avaliadas"), "en": ("not evaluated", "not evaluated")},
    "pass": {"pt": ("passou", "passaram"), "en": ("passed", "passed")},
}

# Values the LLM returns for document_type and capture_type (prompts/extraction_v4.txt).
DOC_TYPES = {
    "payslip": {"pt": "Holerite", "en": "Pay stub"},
    "payslip_vacation": {"pt": "Holerite de férias", "en": "Vacation pay stub"},
    "payslip_13th": {"pt": "Holerite de 13º", "en": "13th-salary pay stub"},
    "bank_statement": {"pt": "Extrato bancário", "en": "Bank statement"},
    "tax_return": {"pt": "Declaração de imposto de renda", "en": "Income tax return"},
    "inss_benefit": {"pt": "Comprovante de benefício do INSS", "en": "INSS benefit statement"},
    "other_document": {"pt": "Outro documento", "en": "Other document"},
    "unidentified": {"pt": "Não identificado", "en": "Unidentified"},
}
CAPTURE_TYPES = {
    "original_file": {"pt": "Arquivo original", "en": "Original file"},
    "photo_of_paper": {"pt": "Foto do papel", "en": "Photo of paper"},
    "photo_of_screen": {"pt": "Foto da tela", "en": "Photo of a screen"},
    "screenshot": {"pt": "Print de tela", "en": "Screenshot"},
}

RULES = {
    "legibility": {"pt": "Legibilidade", "en": "Legibility"},
    "document_type": {"pt": "Tipo de documento", "en": "Document type"},
    "screen_capture": {"pt": "Captura de tela", "en": "Screen capture"},
    "completeness": {"pt": "Documento completo", "en": "Complete document"},
    "identification": {"pt": "Titular", "en": "Applicant"},
    "time_window": {"pt": "Período", "en": "Time window"},
    "income": {"pt": "Renda", "en": "Income"},
    "consistency": {"pt": "Consistência dos totais", "en": "Totals consistency"},
    "fraud": {"pt": "Fraude", "en": "Fraud"},
}
# Defects of the phone photos (data/photos.csv), for the results page.
DEFECTS = {
    "none": {"pt": "Sem defeito", "en": "No defect"},
    "cropped": {"pt": "Cortada", "en": "Cropped"},
    "flash_glare": {"pt": "Reflexo do flash", "en": "Flash glare"},
    "motion_blur": {"pt": "Tremida", "en": "Motion blur"},
    "occluded": {"pt": "Parte coberta", "en": "Partly covered"},
    "rotated": {"pt": "Girada", "en": "Rotated"},
    "screen_ui_visible": {"pt": "Tela do aparelho aparecendo", "en": "Device screen visible"},
    "small_in_frame": {"pt": "Documento pequeno na foto", "en": "Document small in the frame"},
    "tilted": {"pt": "Inclinada", "en": "Tilted"},
    "upside_down": {"pt": "De cabeça para baixo", "en": "Upside down"},
}

# Each rule as the question it answers, for people who don't know rules.md.
RULE_QUESTIONS = {
    "legibility": {"pt": "Dá para ler o documento?", "en": "Can the document be read?"},
    "document_type": {"pt": "É um holerite?", "en": "Is it a pay stub?"},
    "screen_capture": {"pt": "Foi enviado como foto ou print de tela?", "en": "Was it sent as a photo or screenshot of a screen?"},
    "completeness": {"pt": "O holerite está completo?", "en": "Is the pay stub complete?"},
    "identification": {"pt": "Está no nome do cliente?", "en": "Is it in the applicant's name?"},
    "time_window": {"pt": "São os últimos 3 meses?", "en": "Are these the last 3 months?"},
    "income": {"pt": "A renda é suficiente?", "en": "Is the income enough?"},
    "consistency": {"pt": "Os totais fecham?", "en": "Do the totals add up?"},
    "fraud": {"pt": "Há sinal de fraude?", "en": "Any sign of fraud?"},
}

MONTHS = {
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
           "novembro", "dezembro"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"],
}


def month_name(period, lang):
    """'2026-07' → 'julho/2026' or 'July 2026'; anything else is returned as it is."""
    try:
        year, month = period.split("-")
        name = MONTHS[lang][int(month) - 1]
    except (AttributeError, ValueError, IndexError):
        return period
    return f"{name}/{year}" if lang == "pt" else f"{name} {year}"

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
    # With the numbers from the income rule; the line above is the fallback when the rule has none.
    "insufficient_income_values": (
        "Sua renda comprovada é de {income} por mês (média de {months} meses). Para a parcela de {installment}, "
        "a renda mínima é de {minimum}.",
        "Your proven income is {income} a month (average of {months} months). For an installment of "
        "{installment}, the minimum income is {minimum}."),
    "review": ("Seus documentos foram enviados para a análise de um especialista. Você receberá a resposta em breve.",
               "Your documents were sent to a specialist for review. You'll hear back soon."),
}

# English version of the type_not_accepted message, built like the Portuguese one in core/rules/document_type.py.
TYPE_NAMES_EN = {
    "bank_statement": "bank statements",
    "tax_return": "income tax returns",
    "inss_benefit": "INSS benefit statements",
}
TYPE_FIX_EN = "Please send your pay stubs for the last 3 months."


def type_message_en(types):
    types = list(dict.fromkeys(types))
    named = [TYPE_NAMES_EN[t] for t in types if t in TYPE_NAMES_EN]
    if len(named) < len(types):
        problem = "This type of document is not accepted." if len(types) == 1 else \
            "These types of document are not accepted."
    else:
        names = " and ".join(named)
        problem = f"{names[0].upper()}{names[1:]} are not accepted."
    return f"{problem} {TYPE_FIX_EN}"

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
    "A01-S": {"pt": "O mesmo cliente do A01, aprovado com o PDF. Aqui, um dos holerites foi enviado como foto da "
                    "tela: reprovado, com orientação para enviar o PDF.",
              "en": "The same applicant as A01, approved with the PDF. Here, one of the pay stubs was sent as a "
                    "photo of the screen: rejected, with guidance to send the PDF."},
    "D01": {"pt": "Uma fatura de cartão de crédito no lugar dos holerites: o LLM reconhece que não é holerite e o "
                  "motor reprova por tipo não aceito.",
            "en": "A credit card bill instead of pay stubs: the LLM recognizes it isn't a pay stub and the engine "
                  "rejects it as a type not accepted."},
    "N01": {"pt": "Uma conta de luz no lugar dos holerites: reprovada por tipo não aceito, com orientação para enviar "
                  "os holerites.",
            "en": "A utility bill instead of pay stubs: rejected as a type not accepted, with guidance to send the "
                  "pay stubs."},
    "N17": {"pt": "Só um comprovante do INSS: reprovado, com uma mensagem que diz qual documento foi enviado.",
            "en": "Only an INSS benefit statement: rejected, with a message that names the document sent."},
}

# Shorter descriptions for the tour cards, where the full sentence wouldn't fit in 3 lines on a phone.
# The analysis section always shows the full description.
CARD_DESCRIPTIONS = {
    "A17": {"pt": "Aprovado mesmo com um documento de identidade a mais: o que não é holerite é ignorado.",
            "en": "Approved even with an extra identity card: what isn't a pay stub is ignored."},
    "D01": {"pt": "Uma fatura de cartão no lugar dos holerites: reprovada por tipo não aceito.",
            "en": "A credit card bill instead of pay stubs: rejected as a type not accepted."},
    "N12": {"pt": "Um holerite ilegível: nem o OCR nem o LLM conseguem ler. Reprovado, com orientação para reenviar.",
            "en": "An unreadable pay stub: neither the OCR nor the LLM can read it. Rejected, with guidance to resend."},
    "A01-S": {"pt": "Um holerite enviado como foto de tela: reprovado.",
              "en": "A pay stub sent as a screen photo: rejected."},
}

# Card and header title: "<ID> · <short scenario>".
SHORT_TITLES = {
    "A01": ("Caminho feliz (empresa 1)", "Happy path (company 1)"),
    "A02": ("Caminho feliz (empresa 2)", "Happy path (company 2)"),
    "A03": ("Caminho feliz (empresa 3)", "Happy path (company 3)"),
    "A04": ("Adicional de insalubridade", "Unhealthy-conditions premium"),
    "A05": ("Hora extra que não muda a decisão", "Overtime that doesn't change the decision"),
    "A06": ("CPF com pontuação", "CPF with punctuation"),
    "A07": ("CPF só com dígitos", "CPF digits only"),
    "A08": ("Nome sem CPF, com acentos diferentes", "Name without CPF, different accents"),
    "A09": ("Seis holerites enviados", "Six pay stubs sent"),
    "A10": ("Mês de férias", "Vacation month"),
    "A11": ("Holerite de 13º separado", "Separate 13th-salary pay stub"),
    "A12": ("Adiantamento salarial", "Salary advance"),
    "A13": ("Renda em 3,02x a parcela", "Income at 3.02x the installment"),
    "A14": ("Renda em 3,05x a parcela", "Income at 3.05x the installment"),
    "A15": ("Renda em exatamente 3,00x", "Income at exactly 3.00x"),
    "A16": ("Foto torta, mas legível", "Skewed but readable photo"),
    "A17": ("Documento de identidade a mais", "Extra identity card"),
    "N01": ("Conta de luz", "Utility bill"),
    "N02": ("Extrato bancário", "Bank statement"),
    "N03": ("CPF diferente do cadastro", "CPF doesn't match the record"),
    "N04": ("Sem nome e sem CPF", "No name and no CPF"),
    "N05": ("Nome de outra pessoa", "Someone else's name"),
    "N06": ("Fora da janela de 4 meses", "Outside the 4-month window"),
    "N07": ("Mês faltando no meio", "Missing month in the middle"),
    "N08": ("Renda bem abaixo de 3x", "Income well below 3x"),
    "N09": ("Renda em 2,98x a parcela", "Income at 2.98x the installment"),
    "N10": ("Hora extra que mudaria a decisão", "Overtime that would flip the decision"),
    "N11": ("1/3 de férias que mudaria a decisão", "Vacation bonus that would flip the decision"),
    "N12": ("Documento ilegível", "Unreadable document"),
    "N13": ("Print de tela", "Screenshot"),
    "N14": ("Nome abreviado", "Abbreviated name"),
    "N15": ("Totais que não fecham", "Totals that don't add up"),
    "N16": ("Texto tentando instruir o sistema", "Text trying to instruct the system"),
    "N17": ("Comprovante do INSS", "INSS benefit statement"),
    "A01-S": ("Holerite enviado como foto de tela", "Pay stub sent as a screen photo"),
    "D01": ("Fatura de cartão de crédito", "Credit card bill"),
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


def title(case, lang):
    pt, en = SHORT_TITLES[case.case_id]
    return f"{case.case_id} · {pt if lang == 'pt' else en}"


def description(case, lang, card=False):
    """What happens in the case: the tour sentence when there is one, else the scenario."""
    if card and case.case_id in CARD_DESCRIPTIONS:
        return CARD_DESCRIPTIONS[case.case_id][lang]
    if case.case_id in TOUR_TEXT:
        return TOUR_TEXT[case.case_id][lang]
    return SCENARIOS_PT.get(case.case_id, case.scenario) if lang == "pt" else case.scenario
