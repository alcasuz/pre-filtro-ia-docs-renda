# CLAUDE.md

## Project
AI pre-screening for Brazilian proof-of-income documents (pay stubs): an LLM reads the document,
deterministic rules in code decide approve, reject or human review, and the applicant learns what to fix.
Personal AI PM lab: prompts, structured output, evals, guardrails, cost and latency. Demo: https://pre-filtro-renda.streamlit.app/

## Fixed rules
- Data is 100% fictional: invented people, CPFs, companies, banks and CNPJs. Never use a real company, bank or person.
- The Gemini API key lives only in `.env` (ignored by git). Never print, log or commit it; check `git status` before every commit.
- Commit or push only when asked.
- Everything written to the repository is in English; document content (names, line items, labels) stays in Portuguese.

## How we work
- Before writing code, explain the plan and why; wait for approval.
- Show results before committing; never estimate a number that isn't in a report or log.

## Decision log
- Whenever we make a relevant product or technical decision (library, model, data format, rule, architecture), propose a new line for decisions.md in this format:
  | YYYY-MM-DD | decision | rationale | alternatives discarded |
- Show me the line and wait for my approval before writing it.
- Append only; never edit or delete existing lines.

## Folder structure
- `core/`: shared engine. `engine.py` runs the rules in order; `rules/` has one rule per file
  (legibility, document_type, screen_capture, completeness, identification, time_window, income,
  consistency, fraud, name_similarity); `models.py` data classes; `inputs.py` LLM JSON to `Documento`;
  `config.py` loads the YAML; `ocr.py` Tesseract word count.
- `config/default_rules.yaml`: rule parameters (multiplier, tolerances, thresholds).
- `prompts/extraction_v1..v4.txt`: extraction prompts (v4 is current).
- `data/`: fictional test set (applicants, documents, line_items, ground_truth, photos CSVs) and `images/` (v2 = phone photos).
- `generation/`: scripts that generate the test set, images and non-payslip documents (fixed seed).
- `evaluation/`: `extract.py` (Gemini calls, cached), `score_documents.py`, `score_applicants.py`,
  `score_photos.py`, `compare_gates.py`; reports in `results/`.
- `cache/`: LLM extractions per prompt and model, OCR word counts, API logs (`_log.csv`).
- `app/`: Streamlit demo (reads caches, calls `core/engine.py`; no API, no OCR, no uploads); own `requirements.txt`.
- `tests/`: unit tests for rules and engine (`pytest`).
- `rules.md`, `test-scenarios.md`, `architecture.md`, `decisions.md`, `README*.md`: product docs.

# Compact instructions
When compacting, preserve:
- the current step of the task and what is waiting for my approval;
- files changed and not yet committed or pushed;
- results of the last eval run (applicants, documents, photos), with the report file names;
- open items and pending decisions (including proposed decisions.md lines).
