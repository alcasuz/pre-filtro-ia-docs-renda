# Test set scenarios (v1: pay stub)

> 100% fictional data. Invented names, CPFs, companies and CNPJs; CPFs randomly generated with valid check digits, unrelated to real people. Document content (names, line-item descriptions) stays in Portuguese, as on real Brazilian pay stubs.
> Version: v1.0 (2026-10-24)

## Principles

- **Unit of decision:** applicant. **Unit of extraction:** document (each image).
- **Balance:** ~50% approve, ~50% reject or review. The set is deliberately enriched and is **not** a sample of production traffic.
- **Every path of every rule appears at least once.** Edge cases sit close to the 3× installment threshold.
- **Fixed `analysis_date` per applicant** (premise 2 of the rules).
- **Language:** documents are always in Portuguese. Everything printed on the generated images, field labels included, is in Portuguese (e.g., "CNPJ do empregador", never "Employer CNPJ"), and extracted values are kept exactly as they appear on the document, never translated. English is used only for the data layer: CSV column names, JSON keys and coded values (e.g., `employer_cnpj`, `payslip`, `earning`).

---

## Applicants that should be approved (16)

| ID | Scenario | Rule tested | Why it is in the set |
|---|---|---|---|
| A01 | Happy path: base salary only (company 1) | all | baseline |
| A02 | Happy path: base salary only (company 2, different layout) | all | layout variation |
| A03 | Happy path: base salary only (company 3, different layout) | all | layout variation |
| A04 | Salary + hazard/unhealthy-conditions premium | R5 | fixed pay beyond salary |
| A05 | Salary + overtime; fixed pay passes on its own | R5 | overtime present without changing the decision |
| A06 | CPF formatted as XXX.XXX.XXX-XX | R2 | CPF normalization |
| A07 | CPF digits only (XXXXXXXXXXX) | R2 | CPF normalization |
| A08 | No CPF; name matches the record but with different accents and casing | R2 | similarity ≥ 95% after normalization |
| A09 | Sent 6 pay stubs; the 3 most recent pass | R3 | selection of the 3 most recent |
| A10 | Vacation month: prorated regular pay stub + separate vacation pay stub | R3, R5 | vacation pay added without the 1/3 |
| A11 | Separate 13th-salary pay stub in the same pay period | R3 | 13th salary ignored |
| A12 | Salary advance recorded as a deduction | R5 | deduction doesn't affect gross fixed income |
| A13 | Edge: income = 3.02× the installment | R6 | fragility near the threshold |
| A14 | Edge: income = 3.05× the installment | R6 | fragility near the threshold |
| A15 | Edge: income = exactly 3.00× the installment | R6 | the rule is "≥" |
| A16 | Slightly skewed but readable photo | R7 | don't flag readable documents as unreadable |

## Applicants that should not be approved (16)

### Reject (12)

| ID | Scenario | Rule tested | Decision |
|---|---|---|---|
| N01 | File that is not an income document | R1 | reject |
| N02 | Bank statement (type not accepted in v1) | R1 | reject |
| N03 | CPF doesn't match the record | R2 | reject |
| N04 | No CPF and no name | R2 | reject |
| N05 | No CPF; someone else's name (similarity < 50%) | R2 | reject |
| N06 | Pay stubs outside the 4-month window | R3 | reject |
| N07 | Missing month in the middle (non-consecutive months) | R3 | reject |
| N08 | Income clearly below 3× | R6 | reject |
| N09 | Edge: income = 2.98× the installment | R6 | reject |
| N10 | Overtime flips the decision: fixed income at 2.9×, would exceed 3× with overtime | R5 | reject |
| N11 | 1/3 vacation bonus flips the decision: would only pass by adding the 1/3 | R5 | reject |
| N12 | One of the 3 pay stubs is unreadable (blurred) | R7 | reject with guidance |

### Human review (4)

| ID | Scenario | Rule tested | Decision |
|---|---|---|---|
| N13 | Screenshot of a pay stub | R1 | review |
| N14 | No CPF; abbreviated name (similarity between 50% and 95%) | R2 | review |
| N15 | Totals don't add up (earnings − deductions ≠ net pay, beyond tolerance) | R4 | review |
| N16 | Text on the pay stub trying to instruct the system (prompt injection) | R7 | review |

**Total:** 32 applicants, ~100 images (most applicants send 3 pay stubs).

---

## Data files

### `applicants.csv` (one per applicant)
`applicant_id, name, cpf, installment_amount, analysis_date`

### `documents.csv` (one per image; extraction ground truth)
`file, applicant_id, true_type (payslip / payslip_vacation / payslip_13th / bank_statement / other), pay_period (YYYY-MM), name_on_doc, cpf_on_doc, employer, employer_cnpj, total_earnings, total_deductions, net_pay, degradation (none / skewed / blurred / screenshot), extra_text`

For the eval, `bank_statement` and `other` are both scored as `other`, the LLM's output type for anything that isn't a pay stub.

### `line_items.csv` (one per pay stub line; classification ground truth)
`file, code, description, kind (earning / deduction), amount, counts_as_income (yes / no)`

### `ground_truth.csv` (one per applicant; filled in by hand, without AI)
`applicant_id, scenario, rule_tested, installment_amount, expected_valid_income, expected_decision (approve / reject / review), expected_reason, notes`

Reason codes: `type_not_accepted`, `id_missing`, `cpf_mismatch`, `name_mismatch`, `name_review`, `outside_window`, `non_consecutive_months`, `insufficient_income`, `illegible`, `suspected_fraud`. Approved applicants have an empty reason.
