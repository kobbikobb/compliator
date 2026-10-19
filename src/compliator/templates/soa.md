# Statement of Applicability — $framework_title

> **Draft skeleton** from `compliator init`. This is the join between an external
> framework and your own controls, and an auditor reads it first. It decides
> which topic policies you actually need, so it is written after risk treatment
> and before the bulk of the policies.

Rules for filling it in:

- **Justify inclusion *and* exclusion.** "Not applicable" without a reason is the
  classic nonconformity.
- **One row per framework control, no more, no less.** A missing row is a gap you
  cannot see, so do not mark this `status: approved` while a row is missing.
- **Identifiers only** (`TODO: A.n`), with your own one-line summary. Never paste
  standard text — see `../SECURITY.md`.

## How this was produced

TODO: the risk assessment and treatment that led to these decisions — on what
date, and who did it.

## Applicability

TODO: replace the single example row with one row per control in the framework.
Rows are decisions; add them as you make them rather than filling the table in
bulk.

| Requirement | Applies | Justification | Status | Our control | Evidence |
| --- | --- | --- | --- | --- | --- |
| TODO | TODO | TODO | `not_implemented` | — | — |

Status values: `implemented` · `partial` · `not_implemented` · `not_applicable`.

## Exclusions

TODO: anything you decided does not apply, and why. This is the section an
auditor samples hardest.

## Revision history

| Date | Change | By |
| --- | --- | --- |
| $date | created from the template by `compliator init` | |
