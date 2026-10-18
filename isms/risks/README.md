# Risks

One Markdown file per risk: `RISK-<NNN>-<slug>.md` from
[`_template.md`](_template.md). Template only — no risks identified yet, which
for a real organisation would itself be the finding.

A risk is something that could go wrong, how bad it would be, what you do about
it, and who owns that decision. Controls treat risks; the SoA
([`../soa/`](../soa/)) records which framework controls you decided are
applicable as a result.

## Keep the register small and honest

Three real risks beat forty invented ones. For a solo developer the honest list
is usually short and unglamorous:

- losing access to the source-control or cloud account (the only person, the
  only owner)
- a credential leaking and being used to reach production data
- a dependency or vendor failing, changing terms, or disappearing
- nobody else being able to operate the system if one person is unavailable
- customer data being lost with no usable backup

Start there rather than with a control library.

## Treatment is a decision, not a score

| Treatment | Means | Written reason required |
| --- | --- | --- |
| `mitigate` | a control reduces it | which control |
| `accept` | knowingly living with it | why, and who accepted it |
| `transfer` | insurance or a vendor | which one |
| `avoid` | stopped doing the thing | what changed |

An `accept` with nobody's name against it is not a decision.

## Scoring, deliberately crude

Three-point scales survive contact with reality better than 1–25 matrices, and
they do not imply precision nobody has.

- likelihood: `low` / `medium` / `high`
- impact: `low` / `medium` / `high`
- record both `inherent` (before controls) and `residual` (after) — and do not
  quietly record only the flattering one

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
treatment: mitigate
controls:
  - soc2-cc6.1
next_review: 2027-04-01
---
```

## Accepting risk

Risk acceptance needs a name against it — including for a solo developer, who is
still the accountable person. An agent may draft an assessment, propose a
treatment, and flag an overdue review. It may not accept a risk on the
organisation's behalf ([`../../VISION.md`](../../VISION.md), principle 5).
