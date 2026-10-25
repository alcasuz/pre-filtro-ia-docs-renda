# Pre-screening rules (fictional business)

> Personal lab. Rules and parameters invented for study purposes; they do not represent any company's policy.
> Version: v1.1 (2026-10-24)

## Glossary (Brazilian terms)

| Term | Meaning |
|---|---|
| Holerite / contracheque | Pay stub issued by the employer every month |
| CPF | Individual taxpayer ID (11 digits, with 2 check digits) |
| CNPJ | Company taxpayer ID |
| Competência | Pay period (the month the pay stub refers to) |
| CLT | Formal employment regime under Brazilian labor law |
| 13º salário | Mandatory "13th salary", an extra annual payment |
| 1/3 de férias | Constitutional vacation bonus: one third on top of vacation pay |
| INSS / IRRF / FGTS | Social security contribution / income tax withheld / severance fund |

---

## Project premises

1. **The LLM only reads and extracts. Every calculation and every decision is made by code.** The LLM returns a JSON with the document's data; the rules engine computes the income and decides.
2. **Fixed reference date:** every time window is counted from the `analysis_date` column in `applicants.csv`, never from today's date. This keeps the eval deterministic: same input, same output.
3. **Always compare against the applicant record** (`applicants.csv`), not against an ID document.
4. **Instructions written inside a document are data, not commands.** No text in the document can change the decision.

## v1 scope

- **Accepted:** pay stub (holerite).
- **Out of v1** (rules kept in the "v2 backlog" section): bank statement, INSS benefit, income tax return, owner's draw (pró-labore).

## Decision flow

1. **Document typing** [LLM]: is the file a pay stub? Which type?
2. **Type acceptance** [CODE]: accepted type in v1 = pay stub.
3. **Extraction** [LLM]: produces the JSON with the document's data.
4. **Decision** [CODE]: the rules engine applies the rules below.

Possible outputs:
- **Approved by the AI → goes to human review**, which confirms.
- **Rejected → automatic rejection**, with the reason shown to the applicant.
- **Direct human review**: suspected fraud or tampering.

---

## v1 rules (pay stub)

Each rule states **Who does it**: `[LLM]` (read/classify), `[OCR]` or `[CODE]` (calculate/decide). A rule can have more than one part.

### R1. Document type
- Types the LLM can return: `payslip`, `payslip_vacation`, `payslip_13th` or `other`.
- `other` (any file that is not a pay stub: bank statement, INSS benefit, a photo that is not a document, etc.) → **reject**. Message to the applicant: "No momento aceitamos apenas holerite. Envie os holerites dos últimos 3 meses." (*We currently accept pay stubs only. Please send your pay stubs for the last 3 months.*)
- Screenshot or signs of editing → **human review** (reason: fraud prevention).
- Who does it: `[LLM]` defines the document type and flags suspected fraud in the JSON (screenshot or signs of editing); `[CODE]` reads the type and the flag and decides between approve, reject or human review.

### R2. Applicant identification
- The document must show the name **or** the CPF. Neither → **reject**.
- If it shows a CPF, it must match the applicant record. Different → **reject**. Same → applicant confirmed, and the name is not evaluated.
- If there is no CPF, compare the name with the applicant record (after normalizing case, accents and spaces):
  - similarity ≥ 95% → ok;
  - similarity ≥ 50% and < 95% → **human review**;
  - similarity < 50% → **reject** (reason: name does not match the record).
- The 95% and 50% thresholds are initial hypotheses and will be calibrated with the eval set.
- Who does it: `[LLM]` extracts the name and CPF as printed on the document; `[CODE]` normalizes the CPF (keeps only the 11 digits, whatever the format: XXX.XXX.XXX-XX, XXXXXXXXXXX, etc.), validates the check digits, compares with the record, computes the name similarity and decides.

### R3. Time window
- 3 pay stubs for consecutive monthly pay periods, all within the 4 months prior to the month of `analysis_date`, not including that month itself (e.g., `analysis_date` = 2026-10-15 → pay periods 2026-06 to 2026-09 are accepted).
- Outside the window or fewer than 3 pay stubs → **reject**. Message to the applicant: "Documentos fora do período aceito. Envie os holerites dos últimos 3 meses." (*Documents outside the accepted period. Please send your pay stubs for the last 3 months.*)
- If more than 3 pay stubs are sent (e.g., 6 months), only the 3 most recent are used.
- If two pay stubs share the same pay period:
  - separate vacation pay stub: vacation pay (without the 1/3 bonus) is added to that month's regular pay stub;
  - separate 13th-salary pay stub: not used in the calculation.
- Who does it: `[LLM]` extracts the pay period and normalizes it to YYYY-MM (e.g., "outubro/26" → 2026-10); `[CODE]` validates the format, checks for 3 consecutive months inside the window and selects the 3 most recent.

### R4. Pay stub consistency
- |total earnings − total deductions − net pay| ≤ R$100.
- Outside the tolerance → **human review** (sign of tampering).
- Who does it: `[LLM]` extracts total earnings, total deductions and net pay; `[CODE]` does the math and decides.

### R5. What counts as income
- **Counts (fixed pay):** base salary, night-shift premium (decision: treated as fixed), hazard and unhealthy-conditions premiums, role bonus, seniority bonus, vacation pay (without the 1/3; it replaces the salary for the vacation days).
- **Does not count:** overtime, commission, profit sharing (PLR), bonuses, 1/3 vacation bonus, 13th salary, reimbursements, per diems, allowances.
- Since income is computed on gross fixed pay (R6), deductions such as salary advances, INSS and IRRF do not affect the calculation.
- Who does it: `[LLM]` extracts every earnings line (description and amount) and classifies it as "counts" or "does not count"; `[CODE]` adds up the lines classified as "counts". The LLM never returns the total.

### R6. Minimum income
- Monthly income = sum of gross fixed pay (the "Counts" list in R5).
- Valid income = average of the 3 months (sum ÷ 3).
- Valid income ≥ 3 × the installment amount → **approved by the AI → human review**.
- Valid income < 3 × the installment → **reject** (reason: insufficient income).
- Who does it: `[CODE]`, from the lines classified in R5.

### R7. Quality and security
- Unreadable, cropped or blurred image → **reject with guidance to resend**.
- Document with text trying to give instructions to the system (prompt injection) → **human review** (suspected fraud).
- Who does it (legibility): `[OCR]` produces the average reading confidence; `[CODE]` compares it to a minimum threshold (to be calibrated in the eval) and decides whether the document is unreadable.
- Who does it (fraud): `[LLM]` flags suspected fraud in the JSON (including prompt injection) with a short justification; `[CODE]` reads the flag and decides.

---

## Known limitations of v1

1. **Vacation paid before the pay period:** vacation pay is usually paid before the time off starts, and the receipt may show the previous month's pay period. In that case one month is inflated and the other deflated. In v1, the pay period printed on the document prevails.

## Hypotheses to test in step 2

- **OCR + LLM route × LLM reading the image directly:** compare accuracy, tokens and latency.
- **OCR:** Tesseract (open source, lightweight, runs on a Mac and on the demo server, returns per-word confidence).
- **Accuracy per field type:** measure line-item classification and amount reading separately, in both routes.

---

## v2 backlog (out of v1)

### Bank statement
- Counts: Pix, TED and DOC transfers received from individuals or companies, as long as they don't come from the account holder.
- Does not count: transfers between accounts of the same holder, investment redemptions (moving one's own assets, not income), investment returns, loan disbursements, chargebacks and refunds, cashback.
- Open question: how to tell the income of someone who sells as an individual (e.g., a street vendor who receives many small Pix transfers from different people) apart from a one-off inflow that is not income (e.g., a friend lending money)? Hypothesis to test: recurrence.

### INSS benefit
- Sickness benefit and other temporary benefits are not accepted.

### Income tax return
- Annual income = taxable + non-taxable income; CLT employees divide by 13, everyone else by 12.
- ⚠️ Review before v2: the 13th salary is reported under "exclusive/final taxation" (not in taxable income), and non-taxable income includes items that are not recurring income (e.g., FGTS withdrawals, severance, savings interest).

### Owner's draw (pró-labore)
- Same rules as the pay stub.
- The company must belong to the person: requires a corporate document (e.g., articles of association or CNPJ registration card).
