---
id: SCOPE-001
title: ISMS Scope Statement
owner: security@example.invalid
status: draft
review_cadence: annual
---

# ISMS Scope

> **Template.** Delete this block and the italic prompts, keep the headings.
> Write in plain sentences a new colleague could follow. If a sentence could be
> pasted into any company's document, it is too generic to be useful.

## 1. Organisation

*Who you are, in one paragraph. What the business actually does, how many
people, and how it is run. For the fictional reference company, see Milestone 2
in [`../PLAN.md`](../PLAN.md).*

| Field | Value |
| --- | --- |
| Legal/operating name | _e.g. Acme SaaS Co. (fictional)_ |
| What it does | _e.g. one-person B2B SaaS; invoicing for small agencies_ |
| People | _e.g. 1 founder/engineer, contract accountant_ |
| Locations | _e.g. remote; no offices_ |
| Customers | _e.g. ~40 small businesses; no consumer data_ |

## 2. What is in scope

*List the systems, services, and data the ISMS covers. Be specific — names of
systems, not categories. This list is what your policies and controls must
actually apply to.*

| System / asset | Purpose | Who administers it | Where facts about it come from |
| --- | --- | --- | --- |
| _Source control (GitHub org)_ | _code, review, CI_ | _founder_ | _GitHub API (read-only)_ |
| _Cloud account_ | _hosting the product_ | _founder_ | _cloud provider API (read-only)_ |
| _Production database_ | _customer records_ | _founder_ | _n/a — manual review_ |

## 3. Data categories

*What kinds of data you hold, and how sensitive they are. This drives what may
never be committed or collected raw.*

| Category | Examples | Sensitivity | Where it lives |
| --- | --- | --- | --- |
| _Customer contact data_ | _names, work emails_ | _personal data — never in this repo_ | _prod database_ |
| _Credentials/secrets_ | _API keys, tokens_ | _secret_ | _secret store_ |
| _Synthetic fixtures_ | _`fixtures/*` in this repo_ | _public_ | _this repository_ |

## 4. What is out of scope

*Say what you are deliberately not covering, and why. Exclusions that nobody
wrote down look like gaps; written down, they are decisions.*

- _e.g. the contract accountant's personal laptop — no company data stored on it_
- _e.g. third-party processors' internal controls — relied on via vendor reviews instead_
- _e.g. the marketing website — no customer data_

## 5. Boundaries and responsibilities

*Who is accountable for the ISMS, who approves policies, and who accepts risk.
For a solo developer this may all be one person — say so plainly rather than
inventing a committee. Note explicitly that an agent may draft and maintain but
not approve (see [`../VISION.md`](../VISION.md)).*

| Role | Held by | Accountable for |
| --- | --- | --- |
| ISMS owner | _founder_ | _scope, policy approval, risk acceptance_ |
| Approves policies | _founder_ | _sign-off on `status: approved`_ |
| Accepts risk | _founder_ | _recorded decisions on each risk_ |

## 6. Reference standards

*What you are orienting to, and what you are **not** claiming. Do not paste
standard text — cite identifiers only.*

- Conceptual reference: ISO/IEC 27001:2022 (no certification claimed).
- Customer-driven framing: AICPA Trust Services Criteria, if applicable.
- This scope statement is not an audit deliverable and confers no certification.

## 7. Assumptions and open questions

*Anything you are assuming and have not verified. This is the most useful
section in six months.*

- _e.g. no personal data is stored outside the production database_
- _e.g. single-person operation, so no segregation-of-duties controls_
