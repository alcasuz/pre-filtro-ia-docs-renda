# Architecture

> Personal lab. Draft v0.1 (2026-10-24).

## Overview

```mermaid
flowchart TD
    F["Front end (Streamlit)<br/>applicant data, config, documents"] --> OCR
    E["Eval<br/>test set CSVs, default config"] --> OCR
    subgraph N["Shared core"]
        OCR["OCR (Tesseract)<br/>text + confidence"] --> X["Extraction (Gemini)<br/>JSON with classified line items"]
        X <--> C[("Extraction cache")]
        X --> V["JSON validation<br/>format guardrails"]
        V --> M["Rules engine<br/>computes and decides"]
        CFG[("Config<br/>multiplier and tolerances")] --> M
    end
    M --> D["Decision + reasons"]
```

Only the extraction step calls the Gemini API and uses quota. Everything else is local code, at no cost.

## Principles

1. **One core, two entry points.** The front end and the eval call the same code; only the data source changes. The eval numbers measure exactly the system behind the demo.
2. **Parameters as configuration.** The income multiplier, tolerances and similarity thresholds live in a configuration file read by the engine; the front end lets the user change the multiplier (income commitment). `analysis_date` is an input parameter: the front end passes today's date, and the eval passes the fixed date from the applicant record.
3. **Extraction cache.** Each document's JSON is stored per document and prompt version. Changing a rule reruns only the engine, without new API calls.
4. **Independent rules.** Each rule receives the JSON and the applicant record and returns: pass, fail or review, plus the reason.

## Rules engine input contract

The engine (`core/engine.py`) is a pure function: it keeps no state between calls, so the same input always produces the same decision. Everything that depends on time or on the request's history comes from the caller:

| Input | Who provides it | Front end | Eval |
|---|---|---|---|
| Applicant record, including `analysis_date` | caller (`Cliente`) | today's date | fixed date from `applicants.csv` |
| Documents (extraction, including `capture_type` from prompt v3, + OCR confidence) | caller (`Documento` list) | extraction and OCR of the uploaded files | cached extraction (or the ground truth, in oracle mode) + `cache/ocr/confidence.csv` |
| `prior_legibility_failures` | caller (request history) | number of rejections for an unreadable or incomplete document this request already had | always 0 (the test set has no history) |
| Rule parameters | `config/default_rules.yaml` | default file, multiplier editable | default file, version recorded in each report |

The front end owns the request history (e.g., how many times it was rejected for an unreadable or incomplete document) and passes it on every call; the engine never stores it. Requests are not tracked by file hash.

## Risks and design decisions

- **Eval comparability:** results are valid only for the configuration they were measured with. Each eval run records the configuration version.
- **Public demo:** uses only the fictional test set, with cached extractions; it accepts no uploads and makes no API calls. Uploads with real API calls only when running locally.

## Folder structure (proposed)

```
pre-filtro-ia-docs-renda/
├── core/              # shared code
│   ├── ocr.py
│   ├── extraction.py  # Gemini call + JSON schema
│   ├── validation.py  # guardrails
│   ├── rules/         # one rule per file
│   └── engine.py
├── config/
│   └── default_rules.yaml
├── data/              # fictional test set: CSVs and images
├── generation/        # scripts that generate the test set
├── cache/             # stored extractions
├── evaluation/        # runs the eval and computes metrics
├── app/               # Streamlit front end
├── rules.md
├── decisions.md
├── test-scenarios.md
└── architecture.md
```
