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

## Quickstart

Requires Python 3.9+ and PyYAML.

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
  repository currently contains only the *verification engine*, one component
  of that. The ISMS layer is Milestones 2–3 in [`PLAN.md`](PLAN.md).
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
