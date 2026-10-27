# AI pre-screening for proof-of-income documents

**English** · [Português](README.pt-BR.md)

A pre-screening tool that reads Brazilian pay stubs (*holerites*), extracts their data with an LLM and applies credit rules in code to approve, reject or route each case to human review.

> **Personal AI product lab.** Not a production product. All data, rules and documents are fictional. Built to practice, end to end, what an AI PM needs to master: prompting, structured output, evals, guardrails, cost and latency.

**Status:** work in progress. Rules, architecture and the test set (data and images) are done, and the Gemini smoke test has passed; extraction and evals are under way.

---

## The problem

In lending operations, every proof of income has to be checked before a contract is signed. When that check is 100% manual:

- every document costs analyst time, including the ones that never had a chance (unreadable photo, wrong file, someone else's document);
- the customer waits hours for an answer and, when rejected, often doesn't know what to fix;
- the document step becomes a bottleneck between the intent to borrow and the signed contract.

This project explores a product question: **how much of that check can be resolved automatically and safely, and where does a human remain essential?**

## Why build it: the value proposition

| Side | Value hypothesis | How to measure | Measurable in this lab? |
|---|---|---|---|
| **Operations** | Less analysis time and cost: cases that could never pass are resolved before they reach an analyst | % of cases resolved without a human; % of AI approvals reversed by the human reviewer | Partially (rates on the test set) |
| **Customer experience** | An answer in seconds instead of hours, with the reason for rejection and what to fix | Latency per document; % of rejections with actionable guidance | Yes (latency and reasons) |
| **Business** | A shorter contracting step and higher conversion to a signed contract | Duration of the document step; conversion to signed contract | No: requires real traffic; stays a hypothesis |

The right-hand column is intentional: a lab proves whether the machine works, not its impact on conversion. That distinction defines what this project can and cannot claim.

## How it works

```mermaid
flowchart TD
    F["Front end (Streamlit)<br/>applicant data, income multiplier, documents"] --> OCR
    E["Eval<br/>fictional test set"] --> OCR
    subgraph N["Shared core"]
        OCR["OCR (Tesseract)<br/>text + confidence"] --> X["Extraction (Gemini)<br/>JSON with classified line items"]
        X <--> C[("Extraction cache")]
        X --> V["JSON validation<br/>guardrails"]
        V --> M["Rules engine<br/>computes and decides"]
        CFG[("Config<br/>multiplier and tolerances")] --> M
    end
    M --> D["Approve → human review<br/>Reject → reason + guidance<br/>Suspected fraud → human review"]
```

**Core principle: the LLM reads, the code decides.** The model extracts and classifies every line item on the pay stub (e.g. "base salary: counts as income"; "overtime: doesn't count"). Every calculation and every decision lives in deterministic code. Why:

- LLMs make arithmetic mistakes and shouldn't make credit decisions on their own;
- the decision is auditable: you can explain exactly why a customer was rejected;
- when something goes wrong, you can tell whether it was a reading error (the LLM) or a rule error (the code).

Details in [`architecture.md`](architecture.md) and the full rule set in [`rules.md`](rules.md).

## Key product decisions

Every decision, with its rationale and the alternatives discarded, is logged in [`decisions.md`](decisions.md). The most relevant:

1. **Prompting + a rules engine instead of fine-tuning or RAG.** The rules are few, stable and fit in the prompt; fine-tuning would require a dataset labeled line by line and retraining for every rule change.
2. **v1 covers pay stubs only.** Bank statements have an open problem (telling the income of someone who sells as an individual apart from a one-off transfer) and were moved to v2. Any other file is rejected with a single, actionable message: "we currently accept pay stubs only".
3. **Humans review approvals, not rejections.** This focuses analysts where the credit risk is, but makes the **false negative** (rejecting someone who should pass) the critical error, because nobody reviews it. That's why automatic rejection only happens with high certainty.
4. **Legibility measured by OCR confidence, not by the LLM's self-assessment.** A stable numeric signal can be calibrated; the model's opinion about its own reading can't.
5. **Public demo without uploads.** The demo uses only fictional documents with cached extractions: zero cost, no risk of receiving real documents, and instant responses.

## How I evaluate it

The eval runs at two levels:

- **Document:** did the LLM read it correctly? Accuracy per field (pay period, tax ID, amounts) and per classified line item.
- **Applicant:** is the final decision right? Confusion matrix across approve, reject and human review.

**Test set:** 32 fictional applicants (~100 pay stubs generated by code), with ~50% that should be approved and ~50% that shouldn't. The set is deliberately enriched: every path of every rule appears at least once, including edge cases (income at 2.98× and 3.02× the installment), overtime that would flip the decision, an unreadable document, a mismatched name and a pay stub containing a prompt injection. The expected decisions were labeled by hand. Scenarios in [`test-scenarios.md`](test-scenarios.md).

**Why overall accuracy isn't enough:** in a set where 75% of applicants should be approved, a system that approves everyone scores 75%. Metrics are reported per class, with the false negative rate front and center.

## Results

> In progress. The numbers below will come from the evals run in this repository.

| Metric | OCR + LLM | LLM reading the image |
|---|---|---|
| Accuracy per classified line item | — | — |
| Accuracy of extracted amounts | — | — |
| Final decision accuracy | — | — |
| False negative rate | — | — |
| Average latency per document | — | — |
| Tokens per document | — | — |

## Known limitations

- Small, synthetic test set: the numbers show how the system behaves in the tested scenarios, not its performance on real documents.
- Vacation pay issued before the pay period can inflate one month and deflate another; in v1, the pay period printed on the document prevails.
- Pay stubs only in v1; bank statements, social security benefits, tax returns and owner's draw are mapped in [`rules.md`](rules.md) as backlog.

## What I'd do differently

> To be written at the end of the project.

## Stack

Python · Gemini API (free tier, Flash models) · Tesseract OCR · Streamlit · Claude Code

## How to run

> Partial: covers what exists today (test set generation, OCR, extraction, rules engine and evals). The Streamlit demo will be added when it is built.

**Requirements:** Python 3.15 (official installer from python.org), Tesseract OCR with the Portuguese model and, only for the extraction step, a Gemini API key.

**Installing Tesseract on an Intel Mac without Homebrew (MacPorts):**

1. Install MacPorts with the official `.pkg` for your macOS version from https://www.macports.org/install.php (the Xcode Command Line Tools must be installed).
2. In a new terminal:
   ```bash
   sudo port selfupdate
   sudo port install tesseract tesseract-por
   tesseract --list-langs     # must list "por"
   ```

Versions used to calibrate the legibility threshold: **Tesseract 5.5.3** (Leptonica 1.87.0), Portuguese model from the **`tesseract-por` 4.1.0** port (standard `tessdata` family), page segmentation `--psm 3`. OCR confidence changes with the Tesseract version or the language model, so the threshold in `config/default_rules.yaml` must be recalibrated if either changes. `core/ocr.py` finds the binary on the `PATH` or in `/opt/local/bin`; set `TESSERACT_CMD` to use another location.

```bash
# 1. Create the virtual environment and install the pinned dependencies
python3.15 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Gemini API key (only needed for calls to the API)
cp .env.example .env    # then fill in GEMINI_API_KEY= in .env; it is git-ignored

# 3. Regenerate the test set (no API calls; fixed seed, reproducible)
.venv/bin/python generation/generate_data.py     # data/*.csv + an ok/failed check per applicant
.venv/bin/python generation/generate_images.py   # data/images/*.png + data/images/_sample.png

# 4. OCR legibility signal (local, no API calls)
.venv/bin/python -m core.ocr                     # writes cache/ocr/confidence.csv

# 5. Extraction with Gemini (uses quota; cached per prompt version and model)
.venv/bin/python evaluation/extract.py --prompt extraction_v2 --model gemini-3.5-flash-lite --min-interval 4 --all

# 6. Tests and evals (local, no API calls)
.venv/bin/python -m pytest
.venv/bin/python evaluation/score_documents.py --prompt extraction_v2 --model gemini-3.5-flash-lite
.venv/bin/python evaluation/score_applicants.py --source oracle
.venv/bin/python evaluation/score_applicants.py --source cache --model gemini-3.5-flash-lite
```

The test set, the OCR confidences and the extractions are already committed, so steps 3 to 5 are optional: tests and evals run offline from the repository. The images use macOS system fonts; on another system they may differ slightly.

---

**About me:** Suzane Lima, Product Manager with a background in fintech, credit and growth. [LinkedIn](https://www.linkedin.com/in/suzane-lima)
