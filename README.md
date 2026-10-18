# Compliator

**Repo-native compliance evidence: verifiable records, deterministic checks, no
platform required.**

A small experiment in running an ISMS out of a git repository. The documents —
scope, policies, risks, applicability — are Markdown you review like code. The
evidence is verifiable: anyone can re-derive a verdict from a record without
running this application.

> **Status: early prototype.** The evidence engine works end to end on synthetic
> fixtures and is covered by tests. It has never collected from a real system of
> record and has never been seen by an auditor. The ISMS documents are templates
> with no real content. Framework references are illustrative placeholders. Do
> not use any of this to claim compliance.

## The idea in one line

The evidence artifact is the product; the tool is disposable.

## Two halves, and you only need one to start

| | Lives in | Needs software? |
| --- | --- | --- |
| **ISMS documents** — scope, policies, risks, statement of applicability | [`isms/`](isms/) | No. Markdown in git. |
| **Verification engine** — declares checks and packages verifiable evidence | [`compliator/`](compliator/) | Yes. Python, one dependency. |

You can keep an ISMS in this repository without ever installing the engine, and
start collecting evidence later for whichever controls are machine-checkable.

## Four concepts

| Concept | Meaning |
| --- | --- |
| **Control** | The security claim or obligation being evaluated. |
| **Source** | A system of record providing observed facts (here: a mock GitHub org). |
| **Check** | A declared assertion over those facts, evaluated deterministically. |
| **Record** | A reproducible evidence package: the configuration used, observed values, the raw source payload, the verdict, and integrity metadata. |

Flow: **fetch facts → evaluate checks → package record → verify integrity and
re-evaluate.**

## How it works

```
config/controls/*.yaml ─┐
                        ├─► engine ─► plugin pulls raw facts ─► evaluate checks
config/sources.yaml ────┘                                            │
                                                                     ▼
                        evidence/<control>/<collection>/  ◄── packager (trust boundary)
                          evidence.json   verdict + observed values + provenance
                          raw/*.json      exact payload the facts came from
                          MANIFEST.json   sha256 of every file
                        evidence/<control>/LATEST.json  (moved only on success)
```

Properties the design holds onto:

- **Raw evidence retained.** The storage shape cannot be reduced to a verdict.
- **Observed values per check.** What was tested, not just whether it passed.
- **Explicit population accounting.** Population and size recorded; an empty
  population is an error, never a vacuous pass.
- **Reproducible verdicts.** Canonical JSON, sorted keys; same facts + same
  config ⇒ same record apart from the timestamp.
- **Thin collectors, no hidden control judgment.** All assertion logic lives in
  one evaluator, driven by YAML.
- **Manual evidence with provenance.** Human forms flow through the same pipeline
  as machine facts.
- **Exact policy/check version pinning.** Every record carries the hash of the
  control definition that produced it.
- **Fail loud.** A broken source is exit code 2, a loud banner, and *no record*.

## Why not just use a compliance platform?

This is not an argument that platforms are worthless. It is an experiment in a
different trade-off: instead of trusting a vendor's summary, make the evidence
itself independently checkable, and keep it in git where it can be reviewed like
code. Both approaches produce the same underlying evidence for an auditor; the
difference is inspectability and where it lives. See [`VISION.md`](VISION.md) for
the direction, including the parts that are explicitly *not* built.

## Getting started

Start with the ISMS documents. No installation, no commands — they are Markdown
files you edit and commit.

### Order to populate

Each step gives the next one something to reference.

| # | Document | Where |
| --- | --- | --- |
| 0 | **Scope** — organisation, systems, data, boundaries, exclusions | [`isms/scope/`](isms/scope/) |
| 1 | **Information Security Policy** (`POL-001`) — the commitment | [`isms/policies/`](isms/policies/) |
| 2 | **Risk Management Policy** (`POL-002`) — how you handle risk | [`isms/policies/`](isms/policies/) |
| 3 | **Risks** — assessed and treated, `RISK-001`… | [`isms/risks/`](isms/risks/) |
| 4 | **Statement of Applicability** — which framework controls apply, and why | [`isms/soa/`](isms/soa/) |
| 5 | **The rest of the policies** (`POL-003`…) — only the ones the SoA calls for | [`isms/policies/`](isms/policies/) |
| 6 | **Controls** — the machine-checkable claims | [`config/controls/`](config/controls/) |

Two things this order is doing, because they are easy to get wrong:

- **Risks and the SoA come before the topic policies.** Assessing risk tells you
  which controls apply; the SoA records that decision; only then do you know which
  policies you actually need. Write forty policies first and you will find twelve
  were never applicable — the usual failure mode.
- **Scope is document #0, not `POL-000`.** Scope says *what is covered*; a policy
  says *what you must do*. Living outside the boundary is a definition; breaking a
  policy is a violation. They are evidenced differently. See
  [`isms/scope/README.md`](isms/scope/README.md).

The full conventions, and the recommended numbering of the policies (which is
also the order to write them in), are in [`isms/README.md`](isms/README.md) and
[`isms/policies/README.md`](isms/policies/README.md).

### Where frameworks fit

A framework is external and fixed; your controls are yours. The mapping is
many-to-many — one control can satisfy requirements in several frameworks — and
the statement of applicability is where applicability gets decided. That model,
including where the current free-text framework references in the control configs
should go instead, is written up in
[`isms/frameworks/README.md`](isms/frameworks/README.md).

## Running the engine

Optional, and independent of the documents above.

```bash
python3 -m pip install -r requirements.txt
python3 -m compliator collect              # against the synthetic fixtures
python3 -m compliator verify evidence
python3 -m unittest discover -s tests -v
```

Prerequisites, flags, exit codes, the failure paths worth trying, what a record
contains, and how to add a control or a source are all in
[`compliator/README.md`](compliator/README.md).

## How this differs from an ISMS (and from certification)

- **Not an ISMS, yet.** An ISMS is the organizational system of record — scope,
  policies, risks, controls, owners, reviews, exceptions, decisions. This
  repository has the *verification engine* (which works) and *templates* for the
  documents (which are placeholders, per Milestones 2–3 in [`PLAN.md`](PLAN.md)).
- **Not a compliance platform.** No hosted service, no dashboard, no integrations.
- **Not certification, and not evidence of compliance.** Nothing here is reviewed
  by an auditor or a compliance professional. A passing record means one declared
  check held against one captured set of facts at one point in time.
- **Not authoritative mappings.** Framework references in
  `config/controls/*.yaml` are illustrative placeholders, not validated against
  SOC 2 TSC or ISO/IEC 27001:2022 Annex A. Standards are cited by identifier
  only; no copyrighted standard text is redistributed.

## Layout

```
isms/                        the ISMS documents (templates) - see isms/README.md
  scope/                     what is in scope
  policies/                  what you must do
  risks/                     what could go wrong
  soa/                       which framework controls apply, and why
  frameworks/                how frameworks relate to policies and controls
config/sources.yaml          named sources, each mapping to one plugin
config/controls/*.yaml       one file per control: metadata + declarative checks
fixtures/                    synthetic GitHub org, cloud account, HR roster, vendors
manual/                      synthetic human-filled forms
compliator/                  the engine - see compliator/README.md
evidence/<control-id>/       generated output (gitignored)
tests/                       stdlib unittest suite
VISION.md · PLAN.md · SECURITY.md · CONTRIBUTING.md
```

## Limitations

Honest list; more in [`PLAN.md`](PLAN.md) under open design questions.

- **Synthetic data only, by design.** `fixtures/` and `manual/` are hand-written
  stand-ins. No real collection, credentials, or network access exists yet.
- **Integrity, not authenticity.** Hashing shows a record was not modified
  relative to its manifest. It does not authenticate the collector, prove
  completeness, or prove the population was enumerated honestly. `LATEST.json`
  can be rewritten by anyone with write access; append-only storage and review
  are what would supply that, and neither is built.
- **A passing check is not a working control.** One control may need several
  technical checks, and technical checks cannot demonstrate that an
  organizational control is effective. Partial coverage is not yet represented.
- **Empty versus absent is unresolved.** Zero results are refused as an error; the
  distinction between no population, failed enumeration, and legitimately absent
  resources is a tracked open question, not a solved one.
- **Human attestations** name their signer in the forms, but the signing step
  itself is not cryptographically verified.
- **No retention, immutability, access control, scheduling, remediation workflow,
  UI, or database.** Deliberately absent for now.
- **Not reviewed by a compliance professional or auditor.**

## License

Apache-2.0 — see [`LICENSE`](LICENSE). Third-party names and standards
identifiers are referenced for description only; no third-party standard text is
included.

## Security

Do not put real evidence, credentials, or sensitive data in this repository — see
[`SECURITY.md`](SECURITY.md).
