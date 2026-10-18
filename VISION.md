# Vision (draft — not settled architecture)

This is an early draft, written to be argued with. It says what we are aiming
at and, more usefully, what we are refusing to build. Milestone 1 is where it
gets reviewed properly.

## Problem

A small team that needs to demonstrate security practice has two bad options.
Buy a compliance platform: a closed service that connects to your systems,
renders a green check, and stores a summary you cannot inspect — trustworthy
largely because it is familiar. Or assemble it by hand: spreadsheets, screenshots,
a policy folder that rots, and a scramble before every audit.

Both produce evidence that is hard to *verify* and easy to *perform*.

## Intended users

First: a solo developer or very small team running a real SaaS product, who
wants an ISMS and evidence they can actually defend, maintained at low cost and
largely by agents. Later, maybe, small teams who want to keep evidence in their
own storage rather than a vendor's.

## The two layers

**The ISMS is the system of record.** Scope, policies, risks, controls,
applicability, owners, reviews, exceptions, decisions — and the links to
evidence. Human-readable Markdown, with narrowly scoped structured metadata only
where a machine genuinely needs it, all tracked and reviewed in git.

**The verification engine is one component.** It answers a narrow question
well: *given this declared check and this system of record, does the observed
fact support the claim, and can someone else re-derive that verdict?* It does
not know what a policy is, does not decide what matters, and does not approve
anything.

## Principles

1. **The evidence artifact is the product; the tool is disposable.** Anyone
   should be able to re-derive the verdict from the record without running our
   application.
2. **Git is the initial source of truth.** Everything is reviewable as a diff.
3. **Thin collectors, no hidden judgment.** Collectors fetch facts; checks
   declare assertions; one evaluator applies them. Control logic never hides
   inside a plugin.
4. **Fail loud, never fail empty.** A broken source is an error, visibly, with
   no record written. Zero results never silently pass.
5. **Agents operate; humans approve.** Agents draft, maintain, assess,
   orchestrate, and propose corrections. They do not accept risk, approve
   policies, or sign off — and must never appear to.
6. **Manual evidence carries provenance.** A human attestation is first-class
   evidence, with an identifiable signer — and is never dressed up as a
   deterministic check.
7. **Synthetic and public by default; real evidence stays out.** The repository
   is public. Sensitive evidence lives in private storage, minimised and
   redacted where necessary.
8. **No unnecessary platform.** No frontend, database, multi-tenancy, or workflow
   engine until a real vertical slice demonstrates the need.
9. **Standards-aware, not standards-pretending.** ISO/IEC 27001:2022 is the
   initial conceptual reference. We cite identifiers, we do not redistribute
   copyrighted standard text, and nothing here confers certification.

## Key invariants

- A record never exists without its raw source payload or a justified, labelled
  snapshot of it.
- Every check records the values it observed, not only pass/fail.
- Populations and their sizes are explicit; emptiness is classified, not
  ignored.
- Verification re-computes hashes rather than trusting stored ones.
- The exact control definition used is pinned to the record.

## What "verifiable" does and does not mean

A record can be shown to be unmodified relative to its manifest, and a check can
be re-evaluated from the retained facts. That is real, and it is the whole point
of the engine. It is **not** proof that collection was honest or complete, that
the collector held the right permissions, or that a passing technical check means
the organizational control is effective. Those need review, access control, and
append-only storage — and the documentation must say so plainly.

## Non-goals (for now)

Certification; a hosted service; multi-tenant anything; a UI; replacing a
security programme with generated documents; bulk control libraries; real
customer or employer data in any form; and any claim that a green record equals
compliance.
