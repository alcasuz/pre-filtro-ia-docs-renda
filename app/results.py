"""Results page: the evaluation reports in evaluation/results/ (content in English)."""

import streamlit as st

import data
from i18n import t

GROUP_TITLES = {"applicants": "group_applicants", "documents": "group_documents", "photos": "group_photos",
                "gates": "group_gates"}


def render():
    lang = st.session_state.lang
    st.header(t("results_title", lang))
    st.caption(t("results_intro", lang))
    st.warning(t("results_photo_note", lang))
    groups = data.result_reports()
    tabs = st.tabs([t(GROUP_TITLES[g], lang) for g in groups])
    for tab, (group, paths) in zip(tabs, groups.items()):
        with tab:
            paths = sorted(paths, key=lambda p: p.name, reverse=True)  # oracle and the latest prompt first
            names = [p.name for p in paths]
            name = st.selectbox(t("report", lang), names, key=f"report_{group}")
            st.markdown(smaller_headings(paths[names.index(name)].read_text(encoding="utf-8")))


def smaller_headings(markdown):
    """Report headings two levels down, so they don't compete with the page title."""
    return "\n".join("##" + line if line.startswith("#") else line for line in markdown.splitlines())
