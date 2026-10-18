---
id: RISK-NNN
title: 
owner: 
status: open
likelihood: medium
impact: medium
inherent: medium
residual: medium
treatment: mitigate
next_review: 
---

# <Risk title>

> **Template.** Keep it to a page. Replace every prompt; a risk entry with
> placeholders is worse than no entry, because it looks like work was done.

## What could happen

*The scenario in plain language, not a category name. "Someone gets into the
cloud account and deletes production data" beats "unauthorised access".*

## Why it matters

*The consequence: to customers, to the business, to the ability to keep
operating. If the honest answer is "it would be annoying but recoverable", say
that — it changes the treatment.*

## How it could happen

*The plausible paths. For a small team this is usually short: a leaked
credential, a phished password, a lost laptop, one person being unavailable.*

## Existing controls

*What already reduces this, whether or not it is machine-checked. Name the
control id where one exists, and link the policy or process where one does not.*

| Control | Kind | Covers which path? |
| --- | --- | --- |
| `soc2-cc6.1` | automated | _stolen password without MFA_ |
| _Vendor review process_ | manual (`manual/`) | _provider failure_ |

## Treatment

*One of `mitigate` / `accept` / `transfer` / `avoid`, with the reasoning.
If accepted, who accepted it and when. If mitigated, what still remains open
after the controls — that gap is the residual risk, and it is the honest part.*

## Residual risk

*What is left after treatment, in one or two sentences, using the same
likelihood/impact words as the front matter. Do not describe it as "low" if the
underlying scenario is unchanged; say what is actually different now.*

## Decision record

| Date | Decision | By | Reason |
| --- | --- | --- | --- |
| _YYYY-MM-DD_ | _treated with MFA + vendor review_ | | |
