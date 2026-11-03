"""Results page: a plain-language dashboard of how the demo's model did on the test set.

Every metric is a question someone without context would ask, its answer and one line of context. The numbers
come from the JSON summaries the evaluation scripts write next to their (English) markdown reports.
"""

import html

import streamlit as st

import data
from i18n import DEFECTS, EXTRACTION_FIELDS, label, t

SOURCE_URL = "https://github.com/alcasuz/pre-filtro-ia-docs-renda/tree/main/evaluation/results"
FIELDS = ("document_type", "pay_period", "name_on_doc", "cpf_on_doc", "total_earnings", "total_deductions", "net_pay")


def decimal(value, lang, places=1):
    text = f"{value:.{places}f}"
    return text.replace(".", ",") if lang == "pt" else text


def percent(right, total, lang):
    return f"{decimal(100 * right / total, lang, 0)}%" if total else "—"


def tiles(summaries, lang):
    """[(question, value, context, short label)] for the cards at the top; also used by the analysis page."""
    out = []
    applicants, documents, photos = (summaries.get(k) for k in ("applicants", "documents", "photos"))
    if applicants:
        right, total = applicants["right_decision"]
        out.append((t("tile_decision_q", lang), t("tile_decision_v", lang, right=right, total=total),
                    t("tile_decision_c", lang), t("tile_decision_short", lang)))
        wrong, good = applicants["false_negatives"]
        out.append((t("tile_good_q", lang), t("tile_good_none", lang) if wrong == 0 else f"{wrong}",
                    t("tile_good_c", lang, total=good), t("tile_good_short", lang)))
    if documents and documents["api"]["latency_p50_s"] is not None:
        api = documents["api"]
        out.append((t("tile_time_q", lang), t("tile_time_v", lang, p50=decimal(api["latency_p50_s"], lang)),
                    t("tile_time_c", lang, p90=decimal(api["latency_p90_s"], lang)), t("tile_time_short", lang)))
    if photos and photos["decision"]["current_rules"]:
        right, total = photos["decision"]["current_rules"]
        out.append((t("tile_photo_q", lang), t("of_n", lang, right=right, total=total), t("tile_photo_c", lang),
                    t("tile_photo_short", lang)))
    return out


def headline_metrics(lang):
    """[(short label, value, question)] for the proof strip at the top of the analysis page."""
    return [(short, value, question) for question, value, _, short in tiles(data.summaries(), lang)]


def bar(name, right, total, lang, note=""):
    width = 100 * right / total if total else 0
    note = f'<span class="m-note">{html.escape(note)}</span>' if note else ""
    return (f'<div class="m-row" title="{html.escape(name)}: {right}/{total}">'
            f'<div class="m-head"><span class="m-label">{html.escape(name)}{note}</span>'
            f'<span class="m-value">{html.escape(t("of_n", lang, right=right, total=total))}'
            f' <span class="m-pct">· {percent(right, total, lang)}</span></span></div>'
            f'<div class="m-track"><div class="m-fill" style="width:{width:.1f}%"></div></div></div>')


def panel(title_text, intro, body, foot="", wide=False):
    foot = f'<p class="p-foot">{foot}</p>' if foot else ""
    return (f'<section class="p-card{" p-wide" if wide else ""}"><h3>{html.escape(title_text)}</h3><p class="p-intro">{html.escape(intro)}</p>'
            f'{body}{foot}</section>')


def classes_panel(applicants, lang):
    body = "".join(bar(t(f"class_{c}", lang), *applicants["per_class"][c], lang) for c in ("approve", "reject", "review"))
    right, total = applicants["right_reason"]
    return panel(t("classes_title", lang), t("classes_intro", lang), body,
                 html.escape(t("classes_reason", lang, right=right, total=total)))


def fields_panel(documents, lang):
    body = "".join(bar(label(EXTRACTION_FIELDS, f, lang), *documents["fields"][f], lang) for f in FIELDS
                   if f in documents["fields"])
    lines = documents["earnings_lines"]
    found, expected = lines["found"]
    right = lines["counts_as_income_right"][0]
    foot = [t("lines_all_right", lang, n=expected) if found == expected == right
            else t("lines_some", lang, found=found, total=expected, right=right)]
    fraud = documents["fraud"]
    if fraud["detected"] + fraud["missed"]:
        alarms = fraud["false_alarms"]
        foot.append(t("fraud_line", lang, detected=fraud["detected"], total=fraud["detected"] + fraud["missed"],
                      alarms=t(f"false_alarms_{alarms if alarms < 2 else 'n'}", lang, n=alarms)))
    return panel(t("fields_title", lang),
                 t("fields_intro", lang, scored=documents["scored"], stubs=documents["pay_stubs"]), body,
                 "<br>".join(html.escape(f) for f in foot))


def photos_panel(photos, lang):
    defects = sorted(photos["by_defect"].items(), key=lambda kv: kv[1]["right"][0] / max(kv[1]["right"][1], 1))
    body = "".join(bar(label(DEFECTS, d, lang), *v["right"], lang,
                       note=t("photo_count_1" if v["photos"] == 1 else "photo_count_n", lang, n=v["photos"]))
                   for d, v in defects)
    return panel(t("photos_title", lang), t("photos_intro", lang, readable=photos["readable"]),
                 f'<div class="m-columns">{body}</div>', html.escape(t("results_photo_note", lang)), wide=True)


# Colors are the theme's (.streamlit/config.toml); bars use the ink blue, one hue for one measure.
DASHBOARD_CSS = """
<style>
.r-intro { color: #55636E; max-width: 46rem; margin: 0 0 4px; }
.r-tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 8px 0 4px; }
.r-tile { border: 1px solid #DDE2E6; border-radius: 10px; padding: 16px; background: #FFFFFF;
          display: flex; flex-direction: column; gap: 4px; }
.r-q { font-size: .88rem; font-weight: 600; color: #17222B; }
.r-v { font-size: 2rem; line-height: 1.15; font-weight: 700; color: #1D4F91; font-variant-numeric: tabular-nums; }
.r-c { font-size: .85rem; line-height: 1.45; color: #55636E; }
.r-alert { border: 1px solid #8A5A00; background: #FDF1D8; color: #8A5A00; border-radius: 10px; padding: 10px 14px;
           font-weight: 600; margin-top: 8px; }
.r-panels { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 12px; }
.p-card { border: 1px solid #DDE2E6; border-radius: 10px; padding: 16px 18px; background: #FFFFFF; }
.p-wide { grid-column: 1 / -1; }
.m-columns { display: grid; grid-template-columns: repeat(2, 1fr); column-gap: 32px; }
.p-card h3 { margin: 0 0 4px; padding: 0; font-size: 1.05rem; font-weight: 700; color: #17222B; }
.p-intro { margin: 0 0 14px; font-size: .86rem; line-height: 1.45; color: #55636E; }
.p-foot { margin: 14px 0 0; padding-top: 10px; border-top: 1px solid #DDE2E6; font-size: .86rem; line-height: 1.5;
          color: #17222B; }
.m-row { display: flex; flex-direction: column; gap: 5px; margin-bottom: 11px; }
.m-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.m-label { font-size: .9rem; color: #17222B; }
.m-note { margin-left: 6px; font-size: .78rem; color: #55636E; }
.m-value { font-size: .88rem; font-weight: 600; color: #17222B; font-variant-numeric: tabular-nums; white-space: nowrap; }
.m-pct { font-weight: 400; color: #55636E; }
.m-track { height: 8px; border-radius: 4px; background: #ECEFF1; overflow: hidden; }
.m-fill { height: 100%; border-radius: 4px; background: #1D4F91; }
.r-source { margin-top: 16px; font-size: .82rem; }
.r-source a { color: #55636E; }
@media (max-width: 760px) {
  .r-tiles { grid-template-columns: repeat(2, 1fr); }
  .r-panels, .m-columns { grid-template-columns: 1fr; }
  .r-v { font-size: 1.6rem; }
}
</style>
"""


def render():
    lang = st.session_state.lang
    st.html(DASHBOARD_CSS)
    st.title(t("results_title", lang), anchor=False)
    summaries = data.summaries()
    if not summaries:
        st.info(t("results_missing", lang))
        return
    applicants, documents, photos = (summaries.get(k) for k in ("applicants", "documents", "photos"))
    st.html(f'<p class="r-intro">{html.escape(t("results_intro", lang, applicants=applicants["applicants"] if applicants else "—", documents=documents["documents"] if documents else "—", photos=photos["photos"] if photos else "—"))}</p>')

    cards = "".join(f'<div class="r-tile"><span class="r-q">{html.escape(q)}</span><span class="r-v">{html.escape(v)}'
                    f'</span><span class="r-c">{html.escape(c)}</span></div>' for q, v, c, _ in tiles(summaries, lang))
    invented = documents["invented_fields"] if documents else 0
    alert = f'<div class="r-alert">{html.escape(t("invented_alert", lang, n=invented))}</div>' if invented else ""
    panels = [p for p in (classes_panel(applicants, lang) if applicants else "",
                          fields_panel(documents, lang) if documents else "",
                          photos_panel(photos, lang) if photos else "") if p]
    st.html(f'<div class="r-tiles">{cards}</div>{alert}<div class="r-panels">{"".join(panels)}</div>'
            f'<p class="r-source"><a href="{SOURCE_URL}" target="_blank" rel="noopener">'
            f'{html.escape(t("source_files", lang))}</a></p>')
