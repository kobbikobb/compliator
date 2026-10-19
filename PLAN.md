# Plan

Short, ordered roadmap. One milestone at a time; a milestone is done when its
output is reviewable, not when the code exists. Later milestones will change as
earlier ones teach us something.

## Current state: Milestone 0 — published

Repository public. `compliator init` (Milestone 3 groundwork) and `compliator status` (document completeness + evidence freshness/verification) are shipped; the getting-started flow and README are in place. The core prototype (config, engine, evaluator, packager, verifier, 7 synthetic controls) is working and tested.

## Milestone 1 — Architecture vision

Review and refine `VISION.md` **with the maintainer**: problem statement,
intended users, the boundary between "ISMS as system of record" and "verification
engine", principles, key invariants, security/trust model, and explicit
non-goals. Keep it short enough that a contributor reads it.

Also decide what is genuinely novel here versus existing projects. Read — do not
copy — OSCAL (data model and vocabulary), CISO Assistant, Probo, Comp AI, and
Openlane. Outcome: an agreed vision plus a list of things we deliberately do not
do.

Review alongside it the framework model drafted in
[`isms/frameworks.md`](isms/frameworks.md): framework requirements
versus our controls, the many-to-many mapping, and why the free-text framework
references currently in `config/controls/*.yaml` should become validated
identifiers. No code for it in this milestone.

## Milestone 2 — Fictional company and minimal repository shape

Describe a fictional one-person software startup: what it builds, which systems
it uses, its data categories, assets, stakeholders, and ISMS scope. Add the
minimum Markdown structure (scope, policies, risks, controls, evidence notes) to
represent that company clearly.

## Milestone 3 — Establish a tiny real ISMS

Write a few policies that are relevant and actionable, identify and assess a few
risks, define corresponding controls, document applicability, owners and
assumptions, and capture explicit human review decisions. Applicability means a
statement of applicability: which framework controls apply, why, and which of our
controls covers each one — written from the risk treatment decisions, before the
bulk of the topic policies.

Explicitly **not** in scope: bulk-generating 93 Annex A controls, or claiming
audit readiness from paper artifacts. Outcome: a coherent, tiny ISMS with visible
human accountability.

A new instance starts with `compliator init` and is checked by `compliator status`:
unfinished `TODO`s, an `approved` document with nobody behind it, a review overdue
against its own cadence, a policy citing a control that does not exist, and per
control whether the evidence exists, passed, is current and still verifies. See
[`ENGINE.md`](ENGINE.md).

## Milestone 4 — One end-to-end verification slice

Choose one security control (for example GitHub branch protection) and verify it
against a dedicated throwaway sandbox. Capture enough raw source material and
provenance that someone else can reach an independent verdict. Classify
failures and empty/incomplete populations carefully. Keep a testable, explicitly
synthetic fixture in public; keep anything real out of the repository.

Reuse the existing engine where it fits, including the packager and verifier.
Outcome: one complete control-to-evidence workflow, honestly reported.

## Milestone 5 — Agent-driven maintenance

Introduce minimal agent instructions and repeatable commands for: proposing
policy updates, flagging stale risks, running checks, and creating reviewable
changes. Machine assertions stay deterministic; human approvals stay explicit
and separate. No UI. Outcome: an agent can do maintenance work and a human can
review it as a diff.

## Milestone 6 — Simulated audit and contributor feedback

Generate a minimal review package from the fictional company, then test whether
a person unfamiliar with the code can trace a claim to its evidence and
reproduce the technical result independently. Publish the findings and ask
practitioners for feedback.

Only after that: consider private evidence backends, or broader organizational
features. Outcome: evidence that the approach survives contact with a skeptic.

## Open design questions (kept visible, not pre-emptively solved)

These were raised deliberately during Milestone 0 and should be answered when the
relevant milestone needs them:

- **One control, many checks.** Passing every technical check does not prove the
  organizational control works. How is partial coverage represented honestly?
- **Zero is ambiguous.** "No matches" must not silently pass, but zero resources
  can be legitimate. Distinguish *no population defined*, *enumeration failed*,
  and *legitimately absent resources*.
- **Reproducible ≠ byte-identical.** Timestamps and IDs vary between runs. Define
  which parts of a record are reproducible, and what a re-run comparison
  legitimately checks.
- **Hashing ≠ authentication.** Hashing proves a record was not modified relative
  to a trusted reference. It does not authenticate the collector or prove
  completeness. What supplies those properties, and how is it documented?
- **Raw payloads can contain personal data or secrets.** Capture minimally,
  restrict access, redact where necessary, and document what was redacted and
  why.
- **Human attestations ≠ machine checks.** Attestations need identifiable
  signers and deliberate approval; they should not be presented as if they were
  deterministic verification.
- **Collection provenance.** Record source, identity/permissions used, query or
  scope, pagination/completeness, time, and tool version where applicable.

## Known gaps in the current prototype

- Framework mappings in `config/controls/*.yaml` are **illustrative placeholders**
  and have not been checked against SOC 2 TSC or ISO/IEC 27001:2022 Annex A.
- Records are only as trustworthy as the manifest they ship with; there is no
  external notarisation, and `LATEST.json` is trusted for staleness.
- **Automated review is manual.** The repository sits below CodeRabbit's ten-star
  threshold, so the review bot starts only when someone asks it to
  (`@coderabbitai review`). No configuration changes that; popularity does.
  Source: <https://docs.coderabbit.ai/management/plans>.
- No retention, immutability, access control, scheduling, or remediation
  workflow — by design, for now.
- `compliator init` reports whether a document is **present**; `compliator status`
  reads back whether it is finished — `TODO`s gone, `approved` backed by an
  `approved_by`, reviews inside their cadence, policy-to-control links that
  resolve, and evidence that is current and verifies. What neither can do is judge
  content: whether a rating is honest, or whether the prose means what it says,
  still needs a human. A traceability report across the whole framework mapping is
  the obvious next slice.
