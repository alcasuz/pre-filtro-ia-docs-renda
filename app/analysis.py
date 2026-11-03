"""Main page: what the product does, the guided tour, then the case: result, what the AI read, what the rules
decided and what the analyst sees."""

import html
from collections import Counter
from decimal import Decimal

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

import data
import results
from i18n import (CAPTURE_TYPES, CLIENT_MESSAGES, COUNT_WORDS, DECISION_SHORT, DOC_TYPES, EXTRACTION_FIELDS, REASONS,
                  RULE_QUESTIONS, STATUS, description, label, month_name, t, title, type_message_en)

GITHUB_URL = "https://github.com/alcasuz/pre-filtro-ia-docs-renda"
LINKEDIN_URL = "https://www.linkedin.com/in/suzane-lima"

CARDS_PER_ROW = 4
GALLERY_PER_ROW = 6
THUMB_WIDTH = 480


@st.cache_resource
def cases():
    return data.load_cases()


@st.cache_data
def thumbnail(path):
    """Top of the document on a fixed 4:3 canvas, so every card has the same shape."""
    with Image.open(path) as img:
        img = img.convert("RGB")
        img = img.crop((0, 0, img.width, min(img.height, int(img.width * 0.75))))
        img.thumbnail((THUMB_WIDTH, THUMB_WIDTH * 3 // 4))
        canvas = Image.new("RGB", (THUMB_WIDTH, THUMB_WIDTH * 3 // 4), "white")
        canvas.paste(img, ((canvas.width - img.width) // 2, 0))
        return canvas


def money(value, lang):
    if value is None:
        return "—"
    text = f"{Decimal(value):,.2f}"
    if lang == "pt":
        text = text.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {text}"


def md(text):
    """Escapes the dollar sign, which Streamlit markdown reads as a math delimiter (R$ 1,00 ... R$ 2,00)."""
    return text.replace("$", "\\$")


def capitalized(text):
    return text[:1].upper() + text[1:]


def number(value, lang, places=2):
    text = f"{value:.{places}f}"
    return text.replace(".", ",") if lang == "pt" else text


def joined(items, lang):
    """'a, b e c' / 'a, b and c'."""
    items = list(items)
    if len(items) < 2:
        return "".join(items)
    return f"{', '.join(items[:-1])} {'e' if lang == 'pt' else 'and'} {items[-1]}"


# ---------------------------------------------------------------------------
# Status: one color and one icon shape per status, so reject and review never rely on hue alone
# ---------------------------------------------------------------------------

STATUS_STYLE = {
    "pass": ("green", ":material/check_circle:"),
    "reject": ("red", ":material/cancel:"),
    "review": ("orange", ":material/warning:"),
    "na": ("gray", ":material/remove:"),
}
DECISION_STATUS = {"approve": "pass", "reject": "reject", "review": "review"}
SEVERITY = ("reject", "review", "na", "pass")


def badge(status, text):
    color, icon = STATUS_STYLE[status]
    return f":{color}-badge[{icon} {text}]"


def decision_badge(decision, lang):
    return badge(DECISION_STATUS[decision], capitalized(label(DECISION_SHORT, decision, lang)))


# ---------------------------------------------------------------------------
# Top of the page: what the product does and the proof
# ---------------------------------------------------------------------------

def hero(lang):
    steps = "".join(f'<li><span class="step-n">{n}</span><div><b>{html.escape(t(f"step{n}_title", lang))}</b>'
                    f'<p>{html.escape(t(f"step{n}_text", lang))}</p></div></li>' for n in (1, 2, 3))
    kpis = "".join(f'<div title="{html.escape(help_text)}"><span class="kpi-value">{html.escape(value)}</span>'
                   f'<span class="kpi-label">{html.escape(name)}</span></div>'
                   for name, value, help_text in results.headline_metrics(lang))
    proof = (f'<div class="proof"><span class="proof-title">{html.escape(t("proof_title", lang))} · '
             f'{html.escape(data.MODEL)}</span><div class="proof-grid">{kpis}</div></div>') if kpis else ""
    st.html(f"""
<div class="hero">
  <span class="hero-badge">{html.escape(t("hero_badge", lang))}</span>
  <h1 class="hero-title">{html.escape(t("app_title", lang))}</h1>
  <p class="hero-lede">{html.escape(t("hero_lede", lang))}</p>
  <p class="hero-problem">{html.escape(t("hero_problem", lang))}</p>
  <ol class="steps">{steps}</ol>
  {proof}
</div>""")
    st.button(t("start_tour", lang), type="primary", icon=":material/arrow_downward:", on_click=scroll_to,
              args=("tour_anchor",))


# ---------------------------------------------------------------------------
# Case selection and the guided tour
# ---------------------------------------------------------------------------

def selected_case(all_cases):
    requested = data.CASE_ALIASES.get(st.query_params.get("case"), st.query_params.get("case"))
    if requested in all_cases:
        st.session_state.case = requested
    case_id = st.session_state.setdefault("case", data.DEFAULT_CASE)
    st.query_params["case"] = case_id
    return case_id


def scroll_to(anchor):
    st.session_state.scroll_to = anchor


def select(case_id):
    st.session_state.case = case_id
    st.query_params["case"] = case_id
    scroll_to("analysis_anchor")


# Fixed heights (title: 2 lines, description: 3 lines, name: 1 line) keep every card the same size;
# longer text ends in an ellipsis. The full description is shown in the analysis section.
CARD_TEXT = """
<div class="card-title">{title}</div>
<div class="card-desc">{description}</div>
<div class="card-name">{name}</div>
"""


def card(case, lang, current, key_prefix):
    chosen = case.case_id == current
    with st.container(border=True, key=f"{key_prefix}_{case.case_id}" + ("_current" if chosen else "")):
        st.image(thumbnail(str(case.documents[0].image)), width="stretch")
        st.markdown(decision_badge(case.expected_decision, lang))
        st.markdown(CARD_TEXT.format(title=html.escape(title(case, lang)),
                                     description=html.escape(description(case, lang, card=True)),
                                     name=html.escape(case.applicant.name)), unsafe_allow_html=True)
        st.button(t("opened", lang) if chosen else t("view_case", lang), key=f"{key_prefix}_open_{case.case_id}",
                  width="stretch", disabled=chosen, on_click=select, args=(case.case_id,))


def grid(items, per_row):
    for start in range(0, len(items), per_row):
        columns = st.columns(per_row)
        for column, item in zip(columns, items[start:start + per_row]):
            with column:
                item()


def tour(all_cases, current, lang):
    st.container(key="tour_anchor", height=1, border=False)
    st.subheader(t("tour_title", lang), anchor=False)
    st.caption(t("tour_intro", lang))
    if current in data.TOUR:
        step = data.TOUR.index(current)
        st.progress((step + 1) / len(data.TOUR), text=t("tour_step", lang, n=step + 1, total=len(data.TOUR)))
        left, _, right = st.columns([1, 2, 1])
        left.button(t("previous", lang), disabled=step == 0, width="stretch", key="tour_prev",
                    on_click=select, args=(data.TOUR[max(step - 1, 0)],))
        right.button(t("next", lang), disabled=step == len(data.TOUR) - 1, width="stretch", key="tour_next",
                     on_click=select, args=(data.TOUR[min(step + 1, len(data.TOUR) - 1)],))
    # Wide screens: a grid. Narrow screens: one row that scrolls sideways (CSS in PAGE_CSS).
    with st.container(key="tour_wide"):
        grid([lambda c=c: card(all_cases[c], lang, current, "tourw") for c in data.TOUR], CARDS_PER_ROW)
    with st.container(key="tour_narrow"):
        # The carousel starts at the open case, so it is the first card on screen.
        start = data.TOUR.index(current) if current in data.TOUR else 0
        order = data.TOUR[start:] + data.TOUR[:start]
        grid([lambda c=c: card(all_cases[c], lang, current, "tourn") for c in order], len(order))
    applicants = [c for c in all_cases if not all_cases[c].is_demo_build]
    built = [c for c in all_cases if all_cases[c].is_demo_build]
    with st.expander(t("all_cases", lang, n=len(applicants))):
        chosen = st.pills(t("all_cases", lang, n=len(applicants)), ["all", "approve", "reject", "review"],
                          default="all", key="gallery_filter", label_visibility="collapsed",
                          format_func=lambda d: t("filter_all", lang) if d == "all"
                          else capitalized(label(DECISION_SHORT, d, lang)))
        shown = [c for c in applicants + built if chosen in (None, "all") or all_cases[c].expected_decision == chosen]
        grid([lambda c=c: card(all_cases[c], lang, current, "all") for c in shown], GALLERY_PER_ROW)


# ---------------------------------------------------------------------------
# 1. What the AI read: document and extraction
# ---------------------------------------------------------------------------

def document_names(case, lang):
    """{file: name a person understands}: 'Holerite de julho/2026', or 'Documento 2 · não identificado'."""
    names = {}
    for n, doc in enumerate(case.documents, 1):
        e = doc.extraction
        kind = label(DOC_TYPES, e.get("document_type"), lang) if e.get("document_type") else None
        period = e.get("pay_period")
        if kind and period and e["document_type"].startswith("payslip"):
            name = f"{kind} de {month_name(period, lang)}" if lang == "pt" else f"{kind}, {month_name(period, lang)}"
        else:
            name = t("document_n", lang, n=n) + (f" · {kind.lower()}" if kind else "")
        if doc.is_photo:
            name += f" ({t('photo_label', lang)})"
        if name in names.values():
            name += f" · {t('document_n', lang, n=n)}"
        names[doc.file] = name
    return names


def show_document(doc):
    st.image(str(doc.image), width="stretch")


def show_extraction(doc, lang):
    """The extracted fields in three groups, then the earnings lines, as cards rather than a spreadsheet."""
    e = doc.extraction

    def value(v):
        if v in (None, ""):
            return f'<span class="x-missing">{html.escape(t("not_found", lang))}</span>'
        return html.escape(str(v))

    def group(title_key, rows, strong=None):
        items = "".join(f'<div class="x-row{" x-strong" if key == strong else ""}">'
                        f'<dt>{html.escape(label(EXTRACTION_FIELDS, key, lang))}</dt><dd>{value(v)}</dd></div>'
                        for key, v in rows)
        return f'<section class="x-card"><h4>{html.escape(t(title_key, lang))}</h4><dl>{items}</dl></section>'

    amount = lambda key: money(e[key], lang) if e.get(key) is not None else None  # noqa: E731
    fraud = t("yes", lang) + (f" — {e['fraud_reason']}" if e.get("fraud_reason") else "") \
        if e.get("fraud_suspected") else t("no", lang)
    cards = [
        group("group_who", [("pay_period", month_name(e.get("pay_period"), lang) if e.get("pay_period") else None),
                            ("name_on_doc", e.get("name_on_doc")), ("cpf_on_doc", e.get("cpf_on_doc"))]),
        group("group_values", [("total_earnings", amount("total_earnings")),
                               ("total_deductions", amount("total_deductions")), ("net_pay", amount("net_pay"))],
              strong="net_pay"),
        group("group_capture", [
            ("document_type", label(DOC_TYPES, e["document_type"], lang) if e.get("document_type") else None),
            ("capture_type", label(CAPTURE_TYPES, e["capture_type"], lang) if e.get("capture_type") else None),
            ("fraud_suspected", fraud)]),
    ]
    if e["earnings_lines"]:
        lines = "".join(
            f'<li><span class="x-desc">{html.escape(line["description"])}</span>'
            f'<span class="x-amt">{html.escape(money(line["amount"], lang))}</span>'
            f'<span class="x-chip {"ok" if line["counts_as_income"] else "no"}">'
            f'{html.escape(t("counts" if line["counts_as_income"] else "doesnt_count", lang))}</span></li>'
            for line in e["earnings_lines"])
        body = f'<ul class="x-lines">{lines}</ul>'
    else:
        body = f'<p class="x-missing">{html.escape(t("no_lines", lang))}</p>'
    cards.append(f'<section class="x-card"><h4>{html.escape(t("earnings_lines", lang))}</h4>{body}</section>')
    st.html(f'<p class="x-title">{html.escape(t("extraction_title", lang))}</p><div class="x-cards">{"".join(cards)}</div>')


# ---------------------------------------------------------------------------
# 2. What the rules decided, in plain language
# ---------------------------------------------------------------------------

def rule_status(r):
    """A rule that had no data to check (e.g. totals missing) is shown as not evaluated, not as passed."""
    return "na" if r.details.get("evaluated") is False else r.status


def answer(r, names, lang):
    """The rule's answer to its question, for someone who has never read rules.md."""
    pt = lang == "pt"
    d, status = r.details, rule_status(r)
    person = " Uma pessoa vai analisar." if pt else " A person will review it."

    if r.rule == "legibility":
        if status == "pass":
            return "Sim, o texto foi lido sem problemas." if pt else "Yes, the text was read without problems."
        if d.get("criterion") == "cpf_check_digits":
            text = ("Não com segurança: o CPF lido é inválido, sinal de leitura errada." if pt
                    else "Not reliably: the CPF read is invalid, a sign of a misread.")
        else:
            text = ("Não: a imagem está ilegível (desfocada, escura ou cortada)." if pt
                    else "No: the image is unreadable (blurred, dark or cropped).")
        return text + (person if r.reason == "too_many_attempts" else "")

    if r.rule == "document_type":
        if status == "reject":
            return "Não: nenhum dos documentos enviados é holerite." if pt else "No: none of the documents sent is a pay stub."
        ignored = d.get("ignored") or []
        if not ignored:
            return "Sim." if pt else "Yes."
        which = joined((names.get(f, f) for f in ignored), lang)
        if pt:
            return (f"Sim. Um documento que não é holerite foi ignorado ({which})." if len(ignored) == 1
                    else f"Sim. {len(ignored)} documentos que não são holerite foram ignorados ({which}).")
        return (f"Yes. One document that isn't a pay stub was ignored ({which})." if len(ignored) == 1
                else f"Yes. {len(ignored)} documents that aren't pay stubs were ignored ({which}).")

    if r.rule == "screen_capture":
        if status == "na":
            return "Não foi possível saber." if pt else "Couldn't tell."
        capture = label(CAPTURE_TYPES, d.get("capture_type"), lang).lower()
        if status == "pass":
            return f"Não: {capture}." if pt else f"No: {capture}."
        return (f"Sim: {capture}. Fotos e prints de tela não são aceitos." if pt
                else f"Yes: {capture}. Photos and screenshots of a screen are not accepted.")

    if r.rule == "completeness":
        if status == "pass":
            return ("Sim: tem a competência, os três totais e as linhas de provento." if pt
                    else "Yes: it has the pay period, the three totals and the earnings lines.")
        missing = [t("earnings_lines", lang).lower() if m == "earnings_lines" else label(EXTRACTION_FIELDS, m, lang).lower()
                   for m in d.get("missing") or []]
        text = f"Não: falta {joined(missing, lang)}." if pt else f"No: {joined(missing, lang)} missing."
        return text + (person if r.reason == "too_many_attempts" else "")

    if r.rule == "identification":
        if d.get("basis") == "cpf":
            if status == "pass":
                return "Sim: o CPF confere com o cadastro." if pt else "Yes: the CPF matches the record."
            return "Não: o CPF é de outra pessoa." if pt else "No: the CPF belongs to someone else."
        if d.get("basis") == "name":
            pct = number(d["similarity"] * 100, lang, 0)
            if status == "pass":
                return (f"Sim: o documento não tem CPF, mas o nome confere ({pct}% de semelhança)." if pt
                        else f"Yes: there's no CPF, but the name matches ({pct}% similar).")
            if status == "review":
                return (f"Talvez: o documento não tem CPF e o nome é parecido ({pct}% de semelhança)." + person if pt
                        else f"Maybe: there's no CPF and the name is similar ({pct}% similar)." + person)
            return (f"Não: o nome é de outra pessoa ({pct}% de semelhança)." if pt
                    else f"No: the name belongs to someone else ({pct}% similar).")
        return ("Não dá para saber: o documento não tem nome nem CPF." if pt
                else "Can't tell: the document has no name and no CPF.")

    if r.rule == "time_window":
        months = joined((month_name(m, lang) for m in d.get("months_used") or []), lang) or ("nenhum" if pt else "none")
        if status == "pass":
            return f"Sim: {months}." if pt else f"Yes: {months}."
        if r.reason == "non_consecutive_months":
            return f"Não: falta um mês no meio ({months})." if pt else f"No: a month is missing in between ({months})."
        return (f"Não: faltam holerites dos últimos 3 meses (válidos: {months})." if pt
                else f"No: pay stubs for the last 3 months are missing (valid: {months}).")

    if r.rule == "income":
        if d.get("valid_income") is None:
            return "Não foi possível calcular a renda." if pt else "The income couldn't be computed."
        income, minimum = money(d["valid_income"], lang), money(d["minimum_income"], lang)
        if status == "pass":
            return (f"Sim: média de {income} por mês; o mínimo é {minimum}." if pt
                    else f"Yes: an average of {income} a month; the minimum is {minimum}.")
        return (f"Não: média de {income} por mês, abaixo do mínimo de {minimum}." if pt
                else f"No: an average of {income} a month, below the minimum of {minimum}.")

    if r.rule == "consistency":
        if status == "na":
            return "Não avaliada: faltam totais no documento." if pt else "Not evaluated: totals are missing."
        if status == "pass":
            return ("Sim: vencimentos menos descontos dá o líquido." if pt
                    else "Yes: earnings minus deductions equals net pay.")
        diff = money(d["difference"], lang)
        return (f"Não: a conta não fecha por {diff}." + person if pt else f"No: it's off by {diff}." + person)

    if r.rule == "fraud":
        reason = d.get("fraud_reason") or ""
        if status == "review":
            return f"Sim: {reason}." + person if pt else f"Yes: {reason}." + person
        if d.get("flagged"):
            return (f"Um sinal foi registrado num documento ignorado: {reason}." if pt
                    else f"A sign was recorded on an ignored document: {reason}.")
        return "Não." if pt else "No."

    return label(STATUS, status, lang)


def rule_groups(decision):
    """[(rule, status, results)] in engine order; a rule takes the worst status among its documents."""
    groups = {}
    for r in decision.results:
        groups.setdefault(r.rule, []).append(r)
    out = []
    for rule, results_ in groups.items():
        statuses = {rule_status(r) for r in results_} - {"na"} or {"na"}
        out.append((rule, min(statuses, key=SEVERITY.index), results_))
    return out


def decisive_rule(decision):
    """The rule behind the main reason, if any."""
    return next((r.rule for r in decision.results if decision.main_reason and r.reason == decision.main_reason), None)


def rule_counts(groups, lang):
    counts = Counter(status for _, status, _ in groups)
    parts = [f"{counts[s]} {COUNT_WORDS[s][lang][counts[s] != 1]}" for s in SEVERITY if counts[s]]
    return f"{t('rules_word', lang)}: " + " · ".join(parts)


def answer_lines(results_, names, lang, only_failing):
    """One line per document; several documents that all got the same answer collapse into one line.

    A single document keeps its name, so the reader knows which one failed."""
    shown = [r for r in results_ if not only_failing or rule_status(r) != "pass"]
    answers = [(names.get(r.file) if r.file else None, answer(r, names, lang)) for r in shown]
    if len(answers) == 1 and answers[0][0]:
        return f"**{md(answers[0][0])}:** {md(answers[0][1])}"
    if len({a for _, a in answers}) == 1:
        return md(answers[0][1])
    return "\n".join(f"- **{md(name)}:** {md(a)}" if name else f"- {md(a)}" for name, a in answers)


def show_rules(groups, decisive, names, lang):
    attention = sorted((g for g in groups if g[1] != "pass"), key=lambda g: (g[0] != decisive, SEVERITY.index(g[1])))
    passed = [g for g in groups if g[1] == "pass"]
    for rule, status, results_ in attention:
        key = f"rule_{rule}" + (f"_decisive_{status}" if rule == decisive else "")
        with st.container(border=True, key=key):
            color, icon = STATUS_STYLE[status]
            heading = f":{color}[{icon}] **{label(RULE_QUESTIONS, rule, lang)}**"
            if rule == decisive:
                heading += f" {badge(status, t('decisive', lang))}"
            st.markdown(heading)
            st.markdown(answer_lines(results_, names, lang, only_failing=True))
    if passed:
        with st.expander(t("rules_passed", lang, n=len(passed)), expanded=not attention):
            for rule, status, results_ in passed:
                color, icon = STATUS_STYLE[status]
                st.markdown(f":{color}[{icon}] **{label(RULE_QUESTIONS, rule, lang)}** "
                            f"{answer_lines(results_, names, lang, only_failing=False)}")


# ---------------------------------------------------------------------------
# Result card (with the message to the applicant) and 3. what the analyst sees
# ---------------------------------------------------------------------------

def client_message(case, decision):
    """(Portuguese, English) message to the applicant."""
    if decision.decision == "approve":
        return CLIENT_MESSAGES["approve"]
    if decision.decision == "review":
        return CLIENT_MESSAGES["review"]
    if decision.main_reason == "type_not_accepted":
        result = next(r for r in decision.results if r.rule == "document_type")
        types = {d.file: d.document.document_type for d in case.documents}
        return result.details["message"], type_message_en(types.get(f) for f in result.details["ignored"])
    if decision.main_reason == "insufficient_income":
        income = next((r for r in decision.results if r.rule == "income"), None)
        d = income.details if income else {}
        if d.get("valid_income") is not None:
            pt, en = CLIENT_MESSAGES["insufficient_income_values"]
            values = lambda lang: {"income": money(d["valid_income"], lang), "months": len(d["months"]),  # noqa: E731
                                   "installment": money(case.applicant.installment_amount, lang),
                                   "minimum": money(d["minimum_income"], lang)}
            return pt.format(**values("pt")), en.format(**values("en"))
    return CLIENT_MESSAGES.get(decision.main_reason, CLIENT_MESSAGES["review"])


def show_client_message(case, decision, lang):
    """Only the selected language; in English, the Portuguese the applicant actually receives goes underneath."""
    pt_text, en_text = client_message(case, decision)
    with st.container(border=True, key="client_msg"):
        st.caption(t("client_message", lang))
        st.markdown(md(pt_text if lang == "pt" else en_text))
        if lang == "en":
            st.caption(md(t("original_pt", lang, text=pt_text)))


def result_card(case, decision, groups, lang):
    color, icon = STATUS_STYLE[DECISION_STATUS[decision.decision]]
    with st.container(border=True, key=f"result_{decision.decision}"):
        left, right = st.columns([3, 2], gap="large")
        with left:
            st.markdown(f"### :{color}[{icon} {capitalized(label(DECISION_SHORT, decision.decision, lang))}]")
            if decision.main_reason:
                st.markdown(f"**{md(capitalized(label(REASONS, decision.main_reason, lang)))}**")
            else:
                st.markdown(t("approve_next", lang))
            st.caption(rule_counts(groups, lang))
            with st.popover(t("policy_sim", lang), icon=":material/tune:"):
                st.number_input(t("multiplier", lang), min_value=2.0, max_value=4.0, step=0.1, format="%.1f",
                                key="multiplier", help=t("multiplier_help", lang))
        with right:
            show_client_message(case, decision, lang)


def show_analyst_view(case, decision, lang):
    income = next((r for r in decision.results if r.rule == "income"), None)
    lines = [
        f"- {t('main_reason', lang)}: {label(REASONS, decision.main_reason, lang) if decision.main_reason else t('none', lang)}",
        f"- {t('all_reasons', lang)}: "
        + (", ".join(label(REASONS, r, lang) for r in decision.reasons) if decision.reasons else t("none", lang)),
    ]
    if income and income.details.get("valid_income") is not None:
        lines.append(f"- {t('valid_income', lang, n=len(income.details['months']))}: "
                     f"{money(income.details['valid_income'], lang)} · {t('minimum_income', lang)}: "
                     f"{money(income.details['minimum_income'], lang)}")
    lines.append(f"- {t('months_used', lang)}: "
                 f"{joined((month_name(m, lang) for m in decision.months_used), lang) or '—'}")
    lines.append(f"- {t('fraud_flag', lang)}: " + ("; ".join(decision.fraud_reasons) if decision.fraud_flag
                                                    else t("no_fraud", lang)))
    st.markdown(md("\n".join(lines)))

    if case.original_documents:
        original = data.decide(case.applicant, case.original_documents, st.session_state.multiplier)
        st.markdown(f"**{t('comparison_title', lang)}**")
        left, right = st.columns(2)
        for column, heading, d in ((left, t("with_pdf", lang), original), (right, t("with_photo", lang), decision)):
            reason = f" · {label(REASONS, d.main_reason, lang)}" if d.main_reason else ""
            with column.container(border=True):
                st.caption(heading)
                st.markdown(f"{decision_badge(d.decision, lang)}{md(reason)}")


def featured_document(case, decision):
    """Index of the document that drove the main reason; for approvals, the first pay stub."""
    files = [d.file for d in case.documents]
    reason = decision.main_reason
    if reason:
        for r in decision.results:
            if r.reason == reason and r.file in files:
                return files.index(r.file)
        if reason == "type_not_accepted":
            ignored = next(r for r in decision.results if r.rule == "document_type").details.get("ignored") or []
            if ignored and ignored[0] in files:
                return files.index(ignored[0])
        if reason == "insufficient_income":
            # The pay stub with an earnings line that doesn't count (overtime, vacation bonus...), if any.
            for i, d in enumerate(case.documents):
                if any(not line.counts_as_income for line in d.document.earnings_lines):
                    return i
    return next((i for i, d in enumerate(case.documents) if d.document.document_type.startswith("payslip")), 0)


def call_to_action(lang):
    with st.container(border=True):
        st.markdown(f"**{t('cta_title', lang)}**")
        st.caption(t("cta_text", lang))
        left, right = st.columns(2)
        left.link_button(t("cta_github", lang), GITHUB_URL, width="stretch")
        right.link_button(t("cta_linkedin", lang), LINKEDIN_URL, width="stretch")


# Scrolls the page to an anchor (the tour or the analysis) after a click. The component's iframe shares the
# app's origin, so the script can reach the page; it waits until the anchor is rendered.
SCROLL_SCRIPT = """
<script>
  // {nonce}
  const go = (tries) => {{
    const anchor = window.parent.document.querySelector('.st-key-{anchor}');
    if (anchor) {{ anchor.scrollIntoView({{behavior: 'smooth', block: 'start'}}); }}
    else if (tries < 50) {{ setTimeout(() => go(tries + 1), 100); }}
  }};
  setTimeout(() => go(0), 150);
</script>
"""


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

# Colors are the theme's (.streamlit/config.toml): ink blue #1D4F91, text #17222B and #55636E, surface #F2F5F8,
# border #DDE2E6, and the status colors.
PAGE_CSS = """
<style>
.hero { padding: .5rem 0 0; }
.hero-badge { display: inline-block; font-size: .78rem; font-weight: 600; letter-spacing: .03em; color: #1D4F91;
              background: #E8EFF8; border-radius: 999px; padding: 3px 10px; }
.hero-title { font-size: 2.4rem; line-height: 1.15; font-weight: 700; color: #17222B; margin: .7rem 0 .6rem;
              padding: 0; text-wrap: balance; }
.hero-lede { font-size: 1.2rem; line-height: 1.5; color: #17222B; max-width: 46rem; margin: 0 0 .4rem; }
.hero-problem { color: #55636E; max-width: 46rem; margin: 0; }
.hero ol.steps { list-style: none; padding: 0 !important; margin: 1.5rem 0 0 !important; display: grid;
                 grid-template-columns: repeat(3, 1fr); gap: 12px; }
.hero ol.steps li { display: flex; gap: 12px; background: #F2F5F8; border-radius: 10px; padding: 16px;
                    margin: 0 !important; }
.x-lines, .x-lines li { padding-left: 0 !important; margin-left: 0 !important; }
.step-n { flex: none; width: 28px; height: 28px; border-radius: 50%; background: #1D4F91; color: #FFFFFF;
          display: grid; place-items: center; font-weight: 700; font-size: .9rem; }
.steps b { display: block; margin-bottom: 4px; color: #17222B; }
.steps p { margin: 0; font-size: .9rem; line-height: 1.45; color: #55636E; }
.proof { margin-top: 12px; border: 1px solid #DDE2E6; border-radius: 10px; padding: 14px 16px; }
.proof-title { font-size: .76rem; text-transform: uppercase; letter-spacing: .06em; color: #55636E; font-weight: 600; }
.proof-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 8px; }
.kpi-value { display: block; font-size: 1.5rem; font-weight: 700; color: #17222B; font-variant-numeric: tabular-nums; }
.kpi-label { font-size: .85rem; color: #55636E; }

.card-title, .card-desc { display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden; }
.card-title { font-size: 1.05rem; font-weight: 700; line-height: 1.3; height: 2.6em; -webkit-line-clamp: 2;
              margin-bottom: .35rem; }
.card-desc { font-size: .88rem; line-height: 1.4; height: 4.2em; -webkit-line-clamp: 3; margin-bottom: .35rem; }
.card-name { font-size: .78rem; color: #55636E; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
[class*="st-key-tour"][class*="_current"], [class*="st-key-all_"][class*="_current"] {
  box-shadow: 0 0 0 2px #1D4F91; }

.x-title { font-weight: 600; margin: 0 0 8px; color: #17222B; }
.x-cards { display: flex; flex-direction: column; gap: 12px; }
.x-card { border: 1px solid #DDE2E6; border-radius: 10px; padding: 12px 16px 14px; background: #FFFFFF; }
.x-card h4 { margin: 0 0 8px; padding: 0; font-size: .74rem; text-transform: uppercase; letter-spacing: .06em;
             color: #55636E; font-weight: 600; }
.x-card dl { margin: 0; display: flex; flex-direction: column; gap: 6px; }
.x-row { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; }
.x-row dt { color: #55636E; font-size: .9rem; font-weight: 400; }
.x-row dd { margin: 0; text-align: right; font-weight: 500; color: #17222B; font-variant-numeric: tabular-nums;
            min-width: 0; overflow-wrap: anywhere; }
.x-strong { border-top: 1px solid #DDE2E6; padding-top: 6px; }
.x-strong dd { font-size: 1.1rem; font-weight: 700; }
.x-missing { color: #5F6B74; font-style: italic; font-weight: 400; margin: 0; }
.x-lines { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.x-lines li { display: grid; grid-template-columns: 1fr auto; gap: 3px 12px; margin: 0; }
.x-desc { font-size: .9rem; color: #17222B; }
.x-amt { text-align: right; font-weight: 600; color: #17222B; font-variant-numeric: tabular-nums; }
.x-chip { grid-column: 1 / -1; justify-self: start; font-size: .74rem; font-weight: 600; border-radius: 999px;
          padding: 1px 8px; }
.x-chip.ok { background: #E4F3EA; color: #17703F; }
.x-chip.no { background: #ECEFF1; color: #5F6B74; }

@media (min-width: 761px) { .st-key-doc_picker { max-width: 440px; } }
.st-key-analysis_anchor, .st-key-tour_anchor { scroll-margin-top: 4.5rem; }  /* clears the fixed top bar */
.st-key-result_approve { box-shadow: inset 5px 0 0 #17703F; }
.st-key-result_reject { box-shadow: inset 5px 0 0 #B42318; }
.st-key-result_review { box-shadow: inset 5px 0 0 #8A5A00; }
[class*="_decisive_reject"] { box-shadow: inset 4px 0 0 #B42318; }
[class*="_decisive_review"] { box-shadow: inset 4px 0 0 #8A5A00; }
.st-key-client_msg { background: #F2F5F8; }

.st-key-tour_narrow { display: none; }
@media (max-width: 760px) {
  .hero-title { font-size: 1.8rem; }
  .hero-lede { font-size: 1.05rem; }
  .steps { grid-template-columns: 1fr; }
  .proof-grid { grid-template-columns: repeat(2, 1fr); }
  .st-key-tour_wide { display: none; }
  .st-key-tour_narrow { display: block; }
  .st-key-tour_narrow [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important; overflow-x: auto; scroll-snap-type: x mandatory; padding-bottom: 6px;
  }
  .st-key-tour_narrow [data-testid="stColumn"] {
    flex: 0 0 78% !important; min-width: 78% !important; scroll-snap-align: start;
  }
}
</style>
"""


def render():
    lang = st.session_state.lang
    all_cases = cases()
    current = selected_case(all_cases)
    st.html(PAGE_CSS)
    hero(lang)
    tour(all_cases, current, lang)
    st.divider()

    case = all_cases[current]
    names = document_names(case, lang)
    st.container(key="analysis_anchor", height=1, border=False)
    st.header(title(case, lang), anchor=False)
    st.markdown(description(case, lang))
    a = case.applicant
    st.caption(md(f"{t('applicant', lang)}: {a.name} · CPF {a.cpf[:3]}.{a.cpf[3:6]}.{a.cpf[6:9]}-{a.cpf[9:]} · "
               f"{t('installment', lang)}: {money(a.installment_amount, lang)} · "
               f"{t('analysis_date', lang)}: {a.analysis_date.strftime('%d/%m/%Y' if lang == 'pt' else '%Y-%m-%d')} · "
               f"{t('expected', lang)}: {label(DECISION_SHORT, case.expected_decision, lang)}"
               + (f" ({label(REASONS, case.expected_reason, lang)})" if case.expected_reason else "")))

    st.session_state.setdefault("multiplier", data.default_multiplier())
    decision = data.decide(case.applicant, case.documents, st.session_state.multiplier)
    groups = rule_groups(decision)
    result_card(case, decision, groups, lang)

    st.subheader(t("section_read", lang), anchor=False)
    st.caption(t("section_read_note", lang))
    featured = featured_document(case, decision)
    options = [featured] + [i for i in range(len(case.documents)) if i != featured]
    with st.container(key="doc_picker"):
        index = st.selectbox(t("document_picker", lang), options, key=f"doc_{current}_{featured}",
                             format_func=lambda i: names[case.documents[i].file])
    doc = case.documents[index]
    left, right = st.columns([3, 2], gap="large")
    with left:
        show_document(doc)
    with right:
        show_extraction(doc, lang)

    st.subheader(t("section_rules", lang), anchor=False)
    st.caption(t("section_rules_note", lang))
    show_rules(groups, decisive_rule(decision), names, lang)

    st.subheader(t("section_analyst", lang), anchor=False)
    show_analyst_view(case, decision, lang)

    call_to_action(lang)

    anchor = st.session_state.pop("scroll_to", None)
    if anchor:
        st.session_state.scroll_nonce = st.session_state.get("scroll_nonce", 0) + 1
        components.html(SCROLL_SCRIPT.format(nonce=st.session_state.scroll_nonce, anchor=anchor), height=0)
