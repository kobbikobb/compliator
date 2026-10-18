# Risks

One Markdown file per risk, in this directory. A risk is something that could go
wrong, how bad it would be, what you do about it, and who owns that decision.
Controls treat risks; evidence shows the controls hold.

## Status: template

`_template.md` is a template. No risks have been identified yet — which,
for a real organisation, would itself be the finding.

## Filename and id

`RISK-<NNN>.md` with the same id in the front matter. Ids are permanent: reviews,
decisions, and control links all reference them.

## Keep the register small and honest

A register with three real risks beats one with forty invented ones. For a solo
developer, the honest list usually looks like: losing access to the source
control account, a credential leaking, a dependency or vendor failing, and losing
the only person who knows how things work. Start there rather than with a
template library.

## Treatment is a decision, not a score

Every risk gets one of these, and for the first three, a written reason:

| Treatment | Means | Written reason required |
| --- | --- | --- |
| `mitigate` | a control reduces it | which control |
| `accept` | knowingly living with it | why, and who accepted it |
| `transfer` | insurance or a vendor | which one |
| `avoid` | stopped doing the thing | what changed |

An `accept` with no named person behind it is not a decision.

## Scoring, kept deliberately crude

Use likelihood and impact on a three-point scale and say what the words mean for
you. Three-point scales survive contact with reality better than 1–25 matrices,
and they do not imply precision nobody has.

- likelihood: `low` / `medium` / `high`
- impact: `low` / `medium` / `high`
- `inherent` = before controls; `residual` = after. Record both, and do not
  quietly record only the flattering one.

## Front matter

```yaml
---
id: RISK-001
title: Loss of access to the source control organisation
owner: security@example.invalid
status: open                  # open | treated | accepted | closed
likelihood: medium
impact: high
inherent: high
residual: medium
treatment: mitigate           # mitigate | accept | transfer | avoid
controls:
  - soc2-cc6.1
next_review: 2027-04-01
---
```

See [`_template.md`](_template.md) for the body, and
[`../README.md`](../README.md) for shared conventions.

## Accepting risk

Risk acceptance is a human decision and needs a name against it — including for
a solo developer, who is still the accountable person. An agent may draft an
assessment, propose a treatment, and flag that a review is overdue. It may not
accept a risk on the organisation's behalf. See [`../../VISION.md`](../../VISION.md),
principle 5.
