---
id: POL-AREA-NNN
title: 
owner: 
status: draft
review_cadence: annual
---

# <Policy title>

> **Template.** Keep the headings that apply and delete the rest. Replace every
> prompt with something specific to this organisation. Do not leave any
> placeholder text in a policy you intend to approve.

## Purpose

*One or two sentences. What risk or obligation does this policy address? Link the
risk: `Treats RISK-003`.*

## Scope

*Who and what this applies to. Reference the systems from
[`../scope/README.md`](../scope/README.md) by name rather than restating them.*

## Policy statements

*The rules, as a short numbered list. Each one should be something a reader could
be audited against, or an explicit statement that it is judgement-based.*

1. _e.g. All production changes are merged through a pull request with at least
   one approval before merge._
2. _e.g. Administrative access to production requires multi-factor
   authentication._
3. _e.g. Access is reviewed when someone leaves the organisation._

## Responsibilities

| Who | Does |
| --- | --- |
| _Owner role_ | _maintains this policy, approves changes_ |
| _Everyone_ | _follows it, reports suspected breaches to the owner_ |

## How this is evidenced

*Be explicit and do not overclaim. For each statement above: either name the
control that checks it, or state that it is manually reviewed.*

| Statement | Control | How it is checked |
| --- | --- | --- |
| _1_ | `soc2-cc8.1` | _automated: branch protection + deployed PRs_ |
| _2_ | `soc2-cc6.1` | _automated: admin MFA configuration_ |
| _3_ | — | _manual: HR roster review (`manual/`), not machine-checked_ |

## Exceptions

*Anything currently not done, or done differently, with the reason and who
accepted it. An honest exceptions section is worth more than a clean-looking
policy that nobody follows.*

- _None._

## Review

*Cadence, and what triggers an out-of-cycle review (a new system, an incident, a
customer requirement).*

## Revision history

| Date | Change | By |
| --- | --- | --- |
| _YYYY-MM-DD_ | _initial draft_ | |
