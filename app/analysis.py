"""Main page: case gallery and guided tour, documents, extraction, rule trail and decision."""

from decimal import Decimal

import streamlit as st
from PIL import Image

import data
from i18n import (CLIENT_MESSAGES, DECISION, DECISION_SHORT, EXTRACTION_FIELDS, REASONS, RULES, STATUS,
                  TOUR_TEXT, TYPE_MESSAGE_EN, TYPE_NAME_EN_DEFAULT, TYPE_NAMES_EN, label, scenario, t)

CARDS_PER_ROW = 4
GALLERY_PER_ROW = 6
THUMB_WIDTH = 480


@st.cache_resource
def cases():
    return data.load_cases()


@st.cache_data
def thumbnail(path):
    """Top of the document, cropped to 4:3, so every card has the same shape."""
    with Image.open(path) as img:
        img = img.convert("RGB")
        img = img.crop((0, 0, img.width, min(img.height, int(img.width * 0.75))))
        img.thumbnail((THUMB_WIDTH, THUMB_WIDTH))
        return img


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


def table(columns, **kwargs):
    """Dataframe tall enough to show every row, without an inner scroll bar."""
    rows = len(next(iter(columns.values()), []))
    st.dataframe(columns, hide_index=True, width="stretch", height=38 + 35 * rows, **kwargs)


def number(value, lang, places=2):
    text = f"{value:.{places}f}"
    return text.replace(".", ",") if lang == "pt" else text


# ---------------------------------------------------------------------------
# Case selection
# ---------------------------------------------------------------------------

def selected_case(all_cases):
    requested = st.query_params.get("case")
    if requested in all_cases:
        st.session_state.case = requested
    case_id = st.session_state.setdefault("case", data.DEFAULT_CASE)
    st.query_params["case"] = case_id
    return case_id


def select(case_id):
    st.session_state.case = case_id
    st.query_params["case"] = case_id


def card_title(case, lang):
    return t("photo_case_title", lang) if case.is_demo_build else f"{case.case_id} · {case.applicant.name}"


def card(case, lang, current, key_prefix, text=None):
    with st.container(border=True):
        st.image(thumbnail(str(case.documents[0].image)), width="stretch")
        st.markdown(f"**{card_title(case, lang)}**")
        if case.is_demo_build:
            st.caption(f"🧪 {t('demo_badge', lang)}")
        st.caption(text or scenario(case, lang))
        chosen = case.case_id == current
        st.button(t("opened", lang) if chosen else t("open", lang), key=f"{key_prefix}_{case.case_id}",
                  type="primary" if chosen else "secondary", width="stretch", on_click=select, args=(case.case_id,))


def grid(items, per_row):
    for start in range(0, len(items), per_row):
        columns = st.columns(per_row)
        for column, item in zip(columns, items[start:start + per_row]):
            with column:
                item()


def tour(all_cases, current, lang):
    st.subheader(t("tour_title", lang))
    if current in data.TOUR:
        step = data.TOUR.index(current)
        left, middle, right = st.columns([1, 2, 1], vertical_alignment="center")
        left.button(t("previous", lang), disabled=step == 0, width="stretch", key="tour_prev",
                    on_click=select, args=(data.TOUR[max(step - 1, 0)],))
        middle.markdown(f"<div style='text-align:center'><b>{t('tour_step', lang, n=step + 1, total=len(data.TOUR))}"
                        f"</b></div>", unsafe_allow_html=True)
        right.button(t("next", lang), disabled=step == len(data.TOUR) - 1, width="stretch", key="tour_next",
                     on_click=select, args=(data.TOUR[min(step + 1, len(data.TOUR) - 1)],))
    # Wide screens: a grid. Narrow screens: one row that scrolls sideways (CSS in RESPONSIVE_CSS).
    with st.container(key="tour_wide"):
        grid([lambda c=c: card(all_cases[c], lang, current, "tourw", TOUR_TEXT[c][lang]) for c in data.TOUR],
             CARDS_PER_ROW)
    with st.container(key="tour_narrow"):
        # The carousel starts at the open case, so it is the first card on screen.
        start = data.TOUR.index(current) if current in data.TOUR else 0
        order = data.TOUR[start:] + data.TOUR[:start]
        grid([lambda c=c: card(all_cases[c], lang, current, "tourn", TOUR_TEXT[c][lang]) for c in order],
             len(order))
    applicants = [c for c in all_cases if c != data.PHOTO_CASE]
    with st.expander(t("all_cases", lang, n=len(applicants))):
        grid([lambda c=c: card(all_cases[c], lang, current, "all") for c in applicants + [data.PHOTO_CASE]],
             GALLERY_PER_ROW)


# ---------------------------------------------------------------------------
# Blocks: document, extraction, rules, decision
# ---------------------------------------------------------------------------

def document_label(doc, lang):
    return f"{doc.file} ({t('photo_label', lang)})" if doc.is_photo else doc.file


def show_document(doc):
    st.image(str(doc.image), width="stretch")


def show_extraction(doc, lang):
    e = doc.extraction
    rows = []
    for key in ("document_type", "capture_type", "pay_period", "name_on_doc", "cpf_on_doc"):
        rows.append((label(EXTRACTION_FIELDS, key, lang), e.get(key) if e.get(key) is not None else "null"))
    for key in ("total_earnings", "total_deductions", "net_pay"):
        rows.append((label(EXTRACTION_FIELDS, key, lang), money(e[key], lang) if e[key] is not None else "null"))
    fraud = t("yes", lang) + (f" — {e['fraud_reason']}" if e.get("fraud_reason") else "") \
        if e["fraud_suspected"] else t("no", lang)
    rows.append((label(EXTRACTION_FIELDS, "fraud_suspected", lang), fraud))
    rows.append((label(EXTRACTION_FIELDS, "ocr_words", lang),
                 "—" if doc.document.ocr_words is None else str(doc.document.ocr_words)))
    st.markdown(f"**{t('extraction_title', lang)}**")
    table({t("field", lang): [r[0] for r in rows], t("value", lang): [str(r[1]) for r in rows]})
    st.markdown(f"**{t('earnings_lines', lang)}**")
    if not e["earnings_lines"]:
        st.caption(t("no_lines", lang))
        return
    table({
        t("description", lang): [l["description"] for l in e["earnings_lines"]],
        t("amount", lang): [money(l["amount"], lang).removeprefix("R$ ") for l in e["earnings_lines"]],
        t("income", lang): [t("counts", lang) if l["counts_as_income"] else t("doesnt_count", lang)
                            for l in e["earnings_lines"]],
    })


def rule_detail(r, lang):
    d = r.details
    pt = lang == "pt"
    if r.rule == "legibility":
        criterion = d.get("criterion")
        words = d.get("ocr_words")
        base = (f"OCR: {words} palavras" if pt else f"OCR: {words} words") if words is not None else "OCR: —"
        if criterion == "cpf_check_digits":
            return base + ("; CPF com dígitos verificadores inválidos" if pt else "; CPF fails its check digits")
        if criterion == "ocr_and_llm_empty":
            return base + ("; o LLM não leu nada nem identificou o documento" if pt
                           else "; the LLM read nothing and couldn't identify the document")
        return base
    if r.rule == "document_type":
        ignored = d.get("ignored") or []
        if r.status == "reject":
            return ", ".join(ignored)
        return (f"ignorados: {', '.join(ignored)}" if pt else f"ignored: {', '.join(ignored)}") if ignored else ""
    if r.rule == "screen_capture":
        return d.get("capture_type", "")
    if r.rule == "completeness":
        missing = d.get("missing") or []
        return (("faltando: " if pt else "missing: ") + ", ".join(missing)) if missing else ""
    if r.rule == "identification":
        if d.get("basis") == "cpf":
            return "CPF " + ("confere" if r.status == "pass" else "diferente") if pt else \
                "CPF " + ("matches" if r.status == "pass" else "differs")
        if d.get("basis") == "name":
            return (f"similaridade do nome: {number(d['similarity'] * 100, lang, 1)}%" if pt
                    else f"name similarity: {number(d['similarity'] * 100, lang, 1)}%")
        return ""
    if r.rule == "time_window":
        return (("meses: " if pt else "months: ") + (", ".join(d.get("months_used") or []) or "—"))
    if r.rule == "income":
        if d.get("valid_income") is None:
            return ""
        return (f"{money(d['valid_income'], lang)} vs {money(d['minimum_income'], lang)} "
                f"({number(d['ratio'], lang)}x {'a parcela' if pt else 'the installment'})")
    if r.rule == "consistency":
        if not d.get("evaluated"):
            return ""
        return (f"diferença de {money(d['difference'], lang)}" if pt else f"difference of {money(d['difference'], lang)}")
    if r.rule == "fraud" and d.get("flagged"):
        note = (" (documento ignorado)" if pt else " (ignored document)") if d.get("ignored_document") else ""
        return (d.get("fraud_reason") or "") + note
    return ""


def show_rules(decision, lang):
    st.markdown(f"**{t('rules_title', lang)}**")
    table({
        t("rule", lang): [label(RULES, r.rule, lang) for r in decision.results],
        t("file", lang): [r.file or "—" for r in decision.results],
        t("status", lang): [label(STATUS, r.status, lang) for r in decision.results],
        t("reason", lang): [label(REASONS, r.reason, lang) if r.reason else "" for r in decision.results],
        t("detail", lang): [rule_detail(r, lang) for r in decision.results],
    })


def client_message(case, decision):
    """(Portuguese, English) message to the applicant."""
    if decision.decision == "approve":
        return CLIENT_MESSAGES["approve"]
    if decision.decision == "review":
        return CLIENT_MESSAGES["review"]
    if decision.main_reason == "type_not_accepted":
        result = next(r for r in decision.results if r.rule == "document_type")
        types = {d.file: d.document.document_type for d in case.documents}
        names = list(dict.fromkeys(TYPE_NAMES_EN.get(types.get(f), TYPE_NAME_EN_DEFAULT)
                                   for f in result.details["ignored"]))
        return result.details["message"], TYPE_MESSAGE_EN.format(type=" and ".join(names))
    return CLIENT_MESSAGES.get(decision.main_reason, CLIENT_MESSAGES["review"])


def decision_banner(decision, lang):
    text = label(DECISION, decision.decision, lang)
    if decision.main_reason:
        text += f" · {label(REASONS, decision.main_reason, lang)}"
    {"approve": st.success, "reject": st.error, "review": st.warning}[decision.decision](md(f"**{text}**"))


def show_decision(case, decision, lang, stacked):
    st.markdown(f"**{t('client_view', lang)}**")
    pt_text, en_text = client_message(case, decision)
    if stacked:
        st.info(md(f"🇧🇷 {pt_text}"))
        st.caption(md(f"{t('translation', lang)}: {en_text}"))
    else:
        left, right = st.columns(2)
        left.info(md(f"🇧🇷 {pt_text}"))
        right.info(md(f"🇬🇧 {en_text}"))

    st.markdown(f"**{t('analyst_view', lang)}**")
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
    lines.append(f"- {t('months_used', lang)}: {', '.join(decision.months_used) or '—'}")
    lines.append(f"- {t('fraud_flag', lang)}: " + ("; ".join(decision.fraud_reasons) if decision.fraud_flag
                                                    else t("no_fraud", lang)))
    st.markdown(md("\n".join(lines)))

    if case.is_demo_build:
        original = data.decide(case.applicant, case.original_documents, st.session_state.multiplier)
        st.markdown(f"**{t('comparison_title', lang)}**")
        left, right = st.columns(2)
        for column, title, d in ((left, t("with_pdf", lang), original), (right, t("with_photo", lang), decision)):
            reason = f" ({label(REASONS, d.main_reason, lang)})" if d.main_reason else ""
            icon = {"approve": "✅", "reject": "❌", "review": "🟡"}[d.decision]
            with column.container(border=True):
                st.caption(title)
                st.markdown(f"{icon} **{label(DECISION_SHORT, d.decision, lang)}**{reason}")


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

RESPONSIVE_CSS = """
<style>
.st-key-narrow_layout, .st-key-tour_narrow { display: none; }
@media (max-width: 760px) {
  .st-key-wide_layout, .st-key-tour_wide { display: none; }
  .st-key-narrow_layout, .st-key-tour_narrow { display: block; }
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
    st.markdown(RESPONSIVE_CSS, unsafe_allow_html=True)
    st.caption(t("app_subtitle", lang))

    tour(all_cases, current, lang)
    st.divider()

    case = all_cases[current]
    st.subheader(card_title(case, lang))
    if case.is_demo_build:
        st.caption(f"🧪 {t('demo_badge', lang)}")
    st.markdown(scenario(case, lang))
    a = case.applicant
    st.caption(md(f"{t('applicant', lang)}: {a.name} · CPF {a.cpf[:3]}.{a.cpf[3:6]}.{a.cpf[6:9]}-{a.cpf[9:]} · "
               f"{t('installment', lang)}: {money(a.installment_amount, lang)} · "
               f"{t('analysis_date', lang)}: {a.analysis_date.strftime('%d/%m/%Y' if lang == 'pt' else '%Y-%m-%d')} · "
               f"{t('expected', lang)}: {label(DECISION_SHORT, case.expected_decision, lang)}"
               + (f" ({case.expected_reason})" if case.expected_reason else "")))

    st.session_state.setdefault("multiplier", data.default_multiplier())
    st.number_input(t("multiplier", lang), min_value=2.0, max_value=4.0, step=0.1, format="%.1f",
                    key="multiplier", help=t("multiplier_help", lang))
    decision = data.decide(case.applicant, case.documents, st.session_state.multiplier)
    decision_banner(decision, lang)

    options = list(range(len(case.documents)))
    index = st.selectbox(t("document_picker", lang), options, key=f"doc_{current}",
                         format_func=lambda i: document_label(case.documents[i], lang))
    doc = case.documents[index]

    with st.container(key="wide_layout"):
        left, right = st.columns([3, 2])
        with left:
            show_document(doc)
        with right:
            show_extraction(doc, lang)
        show_rules(decision, lang)
        st.markdown(f"### {t('decision_title', lang)}")
        show_decision(case, decision, lang, stacked=False)

    with st.container(key="narrow_layout"):
        tabs = st.tabs([t("tab_document", lang), t("tab_extraction", lang), t("tab_rules", lang),
                        t("tab_decision", lang)])
        with tabs[0]:
            show_document(doc)
        with tabs[1]:
            show_extraction(doc, lang)
        with tabs[2]:
            show_rules(decision, lang)
        with tabs[3]:
            show_decision(case, decision, lang, stacked=True)
