# Compliator

**Repo-native compliance evidence: verifiable records, deterministic checks, no
platform required.**

This repository contains `compliator`, an evidence-verification engine — the
first concrete component of a planned **agent-first ISMS** (see
[`VISION.md`](VISION.md), [`PLAN.md`](PLAN.md)). Everything here runs offline on
synthetic data describing a fictional company. There are no credentials, no
network calls, and no real evidence.

> **Status: early prototype.** The engine works end to end on fixtures and is
> covered by tests. It has never collected from a real system of record and has
> never been seen by an auditor. Framework mappings in the example controls are
> placeholders. Do not use this to claim compliance.

## The idea in one line

The evidence artifact is the product; the tool is disposable. Anyone should be
able to re-derive the verdict from the record without running this application.

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

- **Raw evidence retained.** Storage shape is not reducible to a verdict.
- **Observed values per check.** What was tested, not just whether it passed.
- **Explicit population accounting.** Population and size recorded; empty
  population is an error, never a vacuous pass.
- **Reproducible verdicts.** Canonical JSON, sorted keys; same facts + same
  config ⇒ same record apart from timestamp.
- **Thin collectors, no hidden control judgment.** All assertion logic lives in
  one evaluator, driven by YAML.
- **Manual evidence with provenance.** Human forms flow through the same
  pipeline as machine facts.
- **Exact policy/check version pinning.** Every record carries the hash of the
  control definition that produced it.
- **Fail loud.** A broken source is exit code 2, a loud banner, and *no record*.

## Why not just use a compliance platform?

This is not an argument that platforms are worthless. It is an experiment in a
different trade-off: instead of trusting a vendor's summary, make the evidence
itself independently checkable, and keep it in git where it can be reviewed like
code. The two approaches produce the same underlying evidence for an auditor;
the difference is inspectability and where it lives. See
[`VISION.md`](VISION.md) for the intended direction, including the parts that are
explicitly *not* built.

## Prerequisites

| Need | Why | Notes |
| --- | --- | --- |
| Python 3.9+ | runs the engine | developed on 3.14; stdlib only, except… |
| PyYAML ≥ 6.0 | parses control/source config | `python3 -m pip install -r requirements.txt` |
| git | evidence and ISMS documents are reviewed as diffs | — |
| `gh` CLI | optional | only for creating PRs / talking to GitHub later |

Nothing else. Today there is **no network access, no credentials, no cloud
account, and no database** — everything runs against the synthetic fixtures in
`fixtures/` and `manual/`.

When real sources arrive (Milestone 4 in [`PLAN.md`](PLAN.md)), they will need
**read-only credentials**: a token scoped to *read* the facts being checked,
never one that can change them. Those credentials live outside the repository
(environment variables or a secret store) and are never committed — see
[`SECURITY.md`](SECURITY.md).

## Getting started from scratch

```bash
git clone https://github.com/kobbikobb/compliator.git
cd compliator
python3 -m pip install -r requirements.txt
```

Confirm it works before writing anything of your own:

```bash
python3 -m compliator list                 # the 7 example controls and their checks
python3 -m compliator collect              # collect them all against synthetic fixtures
python3 -m compliator verify evidence       # re-verify every record's hashes
python3 -m unittest discover -s tests -v    # 42 tests
```

You should end with 7 passing controls, 7 verified records, and a green test
suite. If that is not what you see, stop and fix it first — nothing below means
anything if the engine does not run.

Then, when you start on your own organization's documents, this is the order
that works: **scope → policies → risks → controls → sources → evidence.** Each
step gives the next one something to reference.

## What to populate first

The ISMS is a small set of human-readable documents plus structured config. Add
them in this order.

| # | Document | Where | Status |
| --- | --- | --- | --- |
| 1 | **Scope** — what the ISMS covers: organisation, systems, data, boundaries, exclusions | `docs/scope.md` | template ready |
| 2 | **Policies** — the rules you commit to, one file each, with an owner and review cadence | `docs/policies/*.md` | template ready |
| 3 | **Risks** — what could go wrong, how bad, how you treat it, who owns it | `docs/risks/*.md` | template ready |
| 4 | **Controls** — the claims you make about how a risk is handled, each with declarative checks | `config/controls/*.yaml` | **works today** (7 examples) |
| 5 | **Sources** — the systems of record your checks read facts from | `config/sources.yaml` | works today against fixtures only |
| 6 | **Manual evidence** — human attestations (acknowledgments, sign-offs) | `manual/*.yaml` | works today |
| 7 | **Evidence** — generated records that bind claims to observed facts | `evidence/` (gitignored) | works today |

Conventions, templates, and worked-through instructions for 1–3 are in
[`docs/README.md`](docs/README.md). 4–7 are the engine's own files and are
documented in the sections below.

### How the pieces reference each other

```
docs/scope.md          ← what is in scope
docs/policies/*.md     ← a policy names the controls that implement it
docs/risks/*.md        ← a risk names the controls that treat it
        │
        ▼
config/controls/*.yaml ← the control: statement, owner, cadence, and its checks
        │
        ▼
config/sources.yaml    ← which system of record each control reads from
        │
        ▼
evidence/<control>/    ← the collected record: observed values + raw payload + hashes
```

The link is by **control id** (`soc2-cc8.1`): a policy or risk references the
id, the control config uses it as its filename and `control.id`. That is what
lets someone trace a claim in a policy down to the payload it was tested
against.

Start with one policy, one risk, one control. Three files that are honest are
worth more than a full set nobody has read.

## Running the engine

```bash
python3 -m pip install -r requirements.txt

python3 -m compliator list                 # show configured controls and checks
python3 -m compliator collect              # collect everything (synthetic fixtures)
python3 -m compliator verify evidence      # re-verify every record's hashes
python3 -m unittest discover -s tests -v   # test suite
```

`make demo`, `make test`, `make clean` wrap the same commands.

Useful flags:

```bash
python3 -m compliator collect --control soc2-cc8.1           # one control
python3 -m compliator collect --as-of 2026-10-17             # date for age checks
python3 -m compliator collect --simulate-failure github_org  # demo the fail-loud path
python3 -m compliator verify evidence/soc2-cc8.1/<collection-id>
```

Exit codes: `0` all passing · `1` a control failed its checks (findings-grade
evidence, still written) · `2` a collection error (nothing written for that
control).

### Try the failure paths

Both are the point of the project, so they are worth a minute:

```bash
# a source that cannot be collected: loud, exit 2, no record written
python3 -m compliator collect --simulate-failure github_org

# a failing control: record written, exit 1
#   edit fixtures/github_org.json and set "push_protection": false on any repo
python3 -m compliator collect
```

## What an auditor gets

Per control, per collection: `evidence.json` (statement, frameworks, each check
with observed values, provenance, raw payload hash, verdict), `raw/<source>.json`
(untouched payload), `MANIFEST.json` (hashes + the verification command), and a
`LATEST.json` pointer that only moves on success.

Verification is re-computation, not trust: `python -m compliator verify` walks
the manifest, re-hashes every file, and confirms the record still binds the raw
payload it claims. Record integrity is the property the engine actually
provides; the tests tamper with a raw file and with `evidence.json` and assert
both are detected.

## How this differs from an ISMS (and from certification)

- **Not an ISMS.** An ISMS is the organizational system of record — scope,
  policies, risks, controls, owners, reviews, exceptions, decisions. This
  repository contains the *verification engine* (which works), plus skeleton
  guidance and templates for the ISMS documents in [`docs/`](docs/README.md)
  (which are placeholders to be written, per Milestones 2–3 in
  [`PLAN.md`](PLAN.md)). The templates are conventions, not content.
- **Not a compliance platform.** No hosted service, no dashboard, no
  integrations.
- **Not certification, and not evidence of compliance.** Nothing here is
  reviewed by an auditor or a compliance professional. A passing record means
  one declared check held against one captured set of facts at one point in
  time.
- **Not authoritative mappings.** The `frameworks:` strings in
  `config/controls/*.yaml` are illustrative placeholders, not validated against
  SOC 2 TSC or ISO/IEC 27001:2022 Annex A. Project names and standard
  identifiers are referenced nominatively; no copyrighted standard text is
  redistributed.

## Layout

```
docs/                        the ISMS documents (scope, policies, risks) - see docs/README.md
config/sources.yaml          named sources, each mapping to one plugin
config/controls/*.yaml       one file per control: metadata + declarative checks
fixtures/                    synthetic GitHub org, cloud account, HR roster, vendors
manual/                      synthetic human-filled forms
compliator/
  engine.py                  runner: freshness → pull → evaluate → package
  evaluate.py                assertion operators (the only control logic)
  config.py                  strict validation, before anything is collected
  packager.py                TRUST BOUNDARY: canonical JSON, hashing, pointer rules
  verify.py                  independent re-verification of a record
  plugins/                   one thin module per source type
evidence/<control-id>/       generated output (gitignored; committed examples: none)
tests/                       stdlib unittest suite
VISION.md · PLAN.md · SECURITY.md · CONTRIBUTING.md
```

## Adding a control (config only)

```yaml
control:
  id: soc2-cc6.6
  title: ...
  statement: >
    ...
  owner: security@example.invalid
  frequency: 1d             # evidence older than this is flagged stale
  frameworks:               # illustrative placeholders, see above
    soc2: "CC6.6 - ..."
    iso_27001: "A.8.16 - ..."
source: github_org          # must exist in config/sources.yaml
checks:
  - description: ...
    population:             # optional; omit for a single value at a path
      path: repos
      where: {environment: production}
    must:
      path: branch_protection.main.enforce_admins
      op: all_equal
      value: true
```

Operators — population: `all_equal`, `none_equal`, `exists`, `date_within_days`,
`min_gte`, `count_gte`; scalar: `equals`, `gte`, `exists`, `count_gte`. Misuse
(unknown op, population op without a population, dangling source, duplicate id)
is a hard error before collection starts.

A new *source* needs one module in `compliator/plugins/` plus one entry in
`config/sources.yaml`. Plugins only fetch and normalise facts — never judge.

## Limitations

Honest list; more in [`PLAN.md`](PLAN.md) under open design questions.

- **Synthetic data only, by design.** `fixtures/` and `manual/` are hand-written
  stand-ins. No real collection, credentials, or network access exists yet.
- **Integrity, not authenticity.** Hashing shows a record was not modified
  relative to its manifest. It does not authenticate the collector, prove
  completeness, or prove the population was enumerated honestly. `LATEST.json`
  can be rewritten by anyone with write access; append-only storage and review
  are what would supply that, and are not built.
- **A passing check is not a working control.** One control may need several
  technical checks, and technical checks cannot demonstrate that an
  organizational control is effective. Partial coverage is not yet represented.
- **Empty vs. absent is unresolved.** Zero results are refused as an error; the
  distinction between no population, failed enumeration, and legitimately absent
  resources is a tracked open question, not a solved one.
- **Human attestations** have identifiable signers in the forms, but the signing
  step itself is not cryptographically verified.
- **No retention, immutability, access control, scheduling, remediation
  workflow, UI, or database.** Deliberately absent for now.
- **Not reviewed by a compliance professional or auditor.**

## License

Apache-2.0 — see [`LICENSE`](LICENSE). Third-party names and standards
identifiers are referenced for description only; no third-party standard text is
included.

## Security

Do not put real evidence, credentials, or sensitive data in this repository —
see [`SECURITY.md`](SECURITY.md).
