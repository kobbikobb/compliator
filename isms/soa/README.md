# Statement of Applicability

One document per framework that needs one: `SOA-<framework-id>.md`, built from
[`_template.md`](_template.md). Template only — no SoA has been written.

## What this is

The SoA lists the framework's controls, and for each one: whether it applies to
you, why, whether it is implemented, and which of your controls covers it.

It is the **join between an external framework and your own controls**. It is
also the single most important document in an ISO/IEC 27001 evidence set,
because it is what an auditor reads first — it tells them which controls to
sample and why the missing ones are missing.

## It is not a policy

A policy is a rule you commit to. The SoA is a *decision* about which of someone
else's requirements apply to you, with justification. Policies implement the
decisions the SoA records.

## Where it sits in the sequence

After risks, before topic policies:

```
scope → POL-001 → POL-002 (risk management) → risks assessed
      → risk treatment → SoA → the rest of the policies
```

The order is the whole point. The treatment decisions from your risks determine
which controls are applicable; the SoA records that; the topic policies
implement it. Do the SoA first and you write only the policies you need. Do it
last and you write forty, then discover twelve were never applicable.

Two wrinkles worth knowing:

- The SoA needs updating whenever a risk treatment changes, a control is
  retired, or scope moves. It is living, not a one-time deliverable.
- ISO/IEC 27001 requires a SoA; SOC 2 has no equivalent (you choose the Trust
  Services Criteria and describe the system instead). So this folder is
  framework-specific — leave it empty if the framework you are working to does
  not need one.

## Rules

- **Justification for inclusion *and* exclusion.** "Not applicable" without a
  reason is the classic nonconformity.
- **One row per framework control, no more, no less.** A missing row is a gap
  you cannot see.
- **Reference identifiers only.** `A.8.32`, `CC8.1` — with your own one-line
  summary. Never paste standard text ([`../../SECURITY.md`](../../SECURITY.md)).
- **Pin the framework version.** `iso_27001_2022`, not `iso_27001`: a revision
  must not silently reinterpret an old decision.
- **Implementation status is honest.** `not_implemented` and `partial` are
  normal and useful; `implemented` with no covering control is a claim, not a
  fact.
