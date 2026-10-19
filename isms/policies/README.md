# Policies

One Markdown file per policy, in this directory: `POL-<NNN>-<slug>.md` from
[`src/compliator/templates/policy.md`](../../src/compliator/templates/policy.md)
— the same skeleton `compliator init` writes. Templates only — no policies exist
yet.

A policy is a rule you commit to. Controls (`config/controls/*.yaml`) are the
claims that implement it, and evidence is the proof they hold.

## Which order, and which numbers

Numbering encodes the **sequence you should write them in**, not importance.
Steps 3–4 in the table below are the risk work that sits between policy #2 and
policy #3 (see the order in [`../../README.md`](../../README.md)) — that gap is deliberate.

| # | File | What it says | Checkable? |
| --- | --- | --- | --- |
| 1 | `POL-001-information-security.md` | The commitment: what we protect, who owns it, that we review it | partly |
| 2 | `POL-002-risk-management.md` | How we identify, assess, treat, and accept risk | no |
| — | *risks assessed → SoA written* | | |
| 3 | `POL-003-access-control.md` | Identities, MFA, least privilege, joiners/movers/leavers | yes |
| 4 | `POL-004-change-management.md` | Reviewed changes, tests, separation of environments | yes |
| 5 | `POL-005-acceptable-use.md` | What people may do with company systems and data | partly |
| 6 | `POL-006-logging-monitoring.md` | What is logged, retention, who reviews it | yes |
| 7 | `POL-007-incident-response.md` | How incidents are reported, triaged, resolved, learned from | partly |
| 8 | `POL-008-backup-continuity.md` | Backups, restore testing, what happens when things break | yes |
| 9 | `POL-009-supplier-management.md` | Assessing and reviewing vendors and processors | partly |
| 10 | `POL-010-data-protection.md` | Data classification, encryption, retention, deletion | yes |
| 11 | `POL-011-hr-security.md` | Onboarding, offboarding, screening, training | partly |
| 12 | `POL-012-physical-security.md` | Only if there is somewhere physical to protect | no |

Adjust to reality: a solo developer typically needs 1, 2, the risk work, then
3, 4, 6, 7, 8, and a short version of 10 — and can honestly leave 5, 9, 11, 12
out, or fold them in elsewhere. Fewer, true policies beat a full set nobody
follows.

Process documents that are *not* policies, and belong later (Milestone 3+ in
[`../../PLAN.md`](../../PLAN.md)): control of documented information, internal
audit, management review, nonconformity and corrective action.

## Two kinds of statement, and they are not equal

- **Verifiable** — "every production change is merged through a reviewed pull
  request." Can have a control with checks reading a system of record.
- **Judgemental** — "we consider security when selecting vendors." Real, but not
  machine-checkable. Say so, and point at the human record (a review form in
  `manual/`) instead of inventing a check that means nothing.

Do not dress the second kind up as the first. It is the fastest way to make a
whole evidence set worthless.

## Minimum bar for a policy worth keeping

1. **Actionable** — a reader can tell whether they are following it.
2. **Owned** — a named person or role that exists.
3. **Reviewed on a stated cadence**, with `last_reviewed` filled in only when a
   review actually happened.
4. **Linked** to controls where one exists, or an explicit note that it is
   human-reviewed only.
5. **Short.** A page beats five. If it needs five, it is probably two policies.

## Front matter

```yaml
---
id: POL-003
title: Access Control Policy
owner: security@example.invalid
status: draft                 # draft | approved | retired
review_cadence: annual        # annual | semiannual | quarterly
last_reviewed: 2026-10-01     # omit until reviewed
approved_by:                  # omit until a human approves; agents cannot fill this
controls:                     # ids from config/controls/
  - soc2-cc6.1
---
```

## Approvals

Setting `status: approved` and filling `approved_by` is a human act. An agent may
draft a policy, propose an update, and flag that a review is due. It may not
approve one, and a change that flips `status` to `approved` with no named human
behind it should be rejected in review — [`../../VISION.md`](../../VISION.md),
principle 5.
