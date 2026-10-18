# The ISMS documents

This directory holds the human-readable part of the ISMS: what is in scope, the
policies you commit to, and the risks you are managing. The machine-checkable
part — controls, sources, evidence — lives in `config/` and `evidence/`.

## Status: templates, not content

Everything in here is a **template with conventions**. There is no real
organization behind it and no policies have been written yet. The example
organisation is fictional and synthetic (see [`../PLAN.md`](../PLAN.md),
Milestone 2). Do not read anything here as a working security programme.

## Order to populate

Add these one at a time, in this order. Each one references the previous.

| # | File | One line | Template |
| --- | --- | --- | --- |
| 1 | `docs/scope.md` | What the ISMS covers, and what it deliberately does not | [`scope.md`](scope.md) |
| 2 | `docs/policies/<name>.md` | A rule you commit to, with an owner and a review cadence | [`policies/README.md`](policies/README.md) |
| 3 | `docs/risks/<risk-id>.md` | Something that could go wrong, and how you treat it | [`risks/README.md`](risks/README.md) |
| 4 | `config/controls/<control-id>.yaml` | The claim that implements a policy or treats a risk, with its checks | [`../README.md`](../README.md#adding-a-control-config-only) |

Rule of thumb: if you cannot say which control implements a policy, the policy
is aspiration. And a control with no checks is not being verified — the engine
refuses an empty `checks` list, so describe such a control in the policy as
"manual, not machine-checked" and point at the human record, rather than
inventing a check that does not mean anything.

## Conventions

- **Markdown** for anything a human reads and approves. Structured metadata
  (front matter, small YAML) only where a machine genuinely needs to read it —
  see [`../VISION.md`](../VISION.md), principle 2.
- **One file per policy, one file per risk.** Reviews then show up as readable
  diffs against a single document.
- **Front matter is narrow.** A few keys, listed in each template. If you want to
  add a key, ask whether anything actually reads it.
- **Identifiers are stable and obvious.** Policies `POL-<AREA>-<NNN>`
  (`POL-ACCESS-001`), risks `RISK-<NNN>`, controls `soc2-cc8.1` /
  `iso-a.8.32`-style ids matching the filename in `config/controls/`. Renaming an
  id breaks the trace from policy to evidence, so treat ids as permanent.
- **Every document has a named owner and a review date.** An unattributed
  document is not evidence of anything.
- **`status:` is honest.** `draft` means nobody has approved it. Do not mark
  something `approved` until a named human actually approved it — see
  [`../VISION.md`](../VISION.md) principle 5: agents draft, humans approve.
- **Simulated data only.** The repository is public; see
  [`../SECURITY.md`](../SECURITY.md).

## Front matter fields, at a glance

```yaml
---
id: POL-ACCESS-001          # stable, never reused
title: Access Control Policy
owner: security@example.invalid   # a named person or role that exists
status: draft               # draft | approved | retired
review_cadence: annual      # annual | semiannual | quarterly
last_reviewed: 2026-10-01   # omit until actually reviewed
approved_by:                # omit until a human approves it
controls:                   # control ids in config/controls/
  - soc2-cc6.1
  - soc2-cc8.1
---
```

These keys are a starting convention, not a validated schema. Milestone 1
reviews this directory's shape; expect to change it before writing much.

## Provenance for manual evidence

Human attestations that the engine collects live in `manual/` as YAML, not here.
A policy is a *rule*; a filled-in acknowledgment form is *evidence that someone
followed it*. The templates in `docs/` describe the rule; the engine's manual
sources record the attestation, with an identifiable signer and a date.
