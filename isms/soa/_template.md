---
id: SOA-001
framework: iso_27001_2022
title: Statement of Applicability
owner: security@example.invalid
status: draft
review_cadence: annual
last_reviewed:
approved_by:
---

# Statement of Applicability — ISO/IEC 27001:2022

> **Template.** One row per Annex A control. Replace the prompts; do not leave
> placeholders. Cite identifiers only — no standard text.

## How this was produced

*One short paragraph: risk assessment and treatment on <date>, reviewed by
<name>. This document records the applicability decisions resulting from that
treatment, plus controls included for other reasons (legal, contractual,
customer requirement, baseline practice).*

## Applicability

*Delete rows for controls you have not considered yet — but then the document is
incomplete, so do not mark `status: approved` while any row is missing.*

| Requirement | Applies | Justification | Status | Our control | Evidence |
| --- | --- | --- | --- | --- | --- |
| `A.5.1` | yes | *basis: legal/contractual/baseline* | implemented | `soc2-cc1.5`-style id or `—` | *how it is evidenced, or "policy assertion, not machine-checked"* |
| `A.8.32` | yes | *treats RISK-004: unreviewed changes reaching production* | implemented | `soc2-cc8.1` | *evidence/<control-id>/ records, or manual forms* |
| `A.7.4` | no | *no physical site; all infrastructure is provider-managed (see `../scope/README.md`)* | — | — | — |

Status values: `implemented` · `partial` · `not_implemented` · `not_applicable`.

## Exclusions

*Every "no" above, collected with its reason. This is the section an auditor
reads to check you thought about it rather than skipping it.*

| Requirement | Reason for exclusion | Decided by | Date |
| --- | --- | --- | --- |
| `A.7.4` | *no physical site under our control* | | |

## Included for reasons other than risk

*Controls that apply because a law, a contract, a customer, or good practice says
so — not because a risk assessment produced them. Auditors expect this section;
pretending every control traces to a risk is a red flag.*

| Requirement | Reason | Our control |
| --- | --- | --- |
| | *e.g. required by customer contract* | |

## Sources of the requirement list

*Where the identifiers above come from, and which version. Never a copy of the
standard itself.*

- Framework reference: ISO/IEC 27001:2022, Annex A (93 controls, 4 themes).
- Identifier list maintained by: *whoever maintains your catalog*.

## Review

*Cadence, and triggers for an out-of-cycle review: a new risk, a retired control,
a scope change, a new customer requirement.*

## Revision history

| Date | Change | By |
| --- | --- | --- |
| | *initial draft* | |
