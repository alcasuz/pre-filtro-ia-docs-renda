"""Streamlit demo of the income document pre-screening (fictional data, cached extractions).

Run locally: .venv/bin/streamlit run app/streamlit_app.py
"""

import streamlit as st

import analysis
import results
from i18n import DEFAULT_LANG, LANGS, t

st.set_page_config(page_title="Pré-filtro de renda · demo", page_icon="📄", layout="wide")


def current_lang():
    requested = st.query_params.get("lang")
    if requested in LANGS:
        st.session_state.lang = requested
    lang = st.session_state.setdefault("lang", DEFAULT_LANG)
    st.query_params["lang"] = lang
    return lang


def language_bar(lang):
    st.markdown("<style>.st-key-lang_bar {align-items: flex-end;}</style>", unsafe_allow_html=True)
    with st.container(key="lang_bar"):
        choice = st.segmented_control(t("language", lang), ["PT", "EN"], default=lang.upper(),
                                      label_visibility="collapsed", key="lang_choice")
    if choice and choice.lower() != lang:
        st.session_state.lang = choice.lower()
        st.query_params["lang"] = choice.lower()
        st.rerun()


lang = current_lang()
page = st.navigation([
    st.Page(analysis.render, title=t("page_analysis", lang), url_path="analysis", default=True),
    st.Page(results.render, title=t("page_results", lang), url_path="results"),
], position="top")
language_bar(lang)
st.title(t("app_title", lang))
page.run()

st.divider()
st.caption(f"{t('footer', lang)} · [GitHub](https://github.com/alcasuz/pre-filtro-ia-docs-renda) · "
           "[LinkedIn](https://www.linkedin.com/in/suzane-lima)")
