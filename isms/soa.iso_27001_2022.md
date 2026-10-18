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

*The join between an external framework and your own controls.* One row per
framework control: does it apply, why, is it implemented, and which of your
controls covers it. It is the document an auditor reads **first** — it tells them
which controls to sample and why the missing ones are missing — and it decides
which topic policies you actually need, so it is written after risk treatment and
before the bulk of the policies.

**Not a policy.** A policy is a rule you commit to; the SoA is a *decision* about
which of someone else's requirements apply to you, with justification. Policies
implement the decisions this file records.

**Framework-specific, and the filename pins the version.** ISO/IEC 27001 requires
an SoA; SOC 2 has no equivalent (you choose Trust Services Criteria and describe
the system). `iso_27001_2022`, not `iso_27001` — a revision must not silently
reinterpret an old decision. A second framework needs its own file.

**Living, not a deliverable.** It changes when a risk treatment changes, a control
is retired, or scope moves.

Rules for filling it in:

- **Justify inclusion *and* exclusion.** "Not applicable" without a reason is the
  classic nonconformity.
- **One row per framework control, no more, no less.** A missing row is a gap you
  cannot see, so do not mark this `status: approved` while a row is missing.
- **Identifiers only.** `A.8.32`, `CC8.1`, with your own one-line summary. Never
  paste standard text ([`../SECURITY.md`](../SECURITY.md)).
- **Status is honest.** `not_implemented` and `partial` are normal and useful;
  `implemented` with no covering control is a claim, not a fact.

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
| `A.7.4` | no | *no physical site; all infrastructure is provider-managed (see `scope.md`)* | — | — | — |

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
