# Compliator — the software

The engine that turns declared checks into verifiable evidence records. Optional:
the ISMS documents in [`isms/`](isms/) work perfectly well without it.

Everything here runs against synthetic fixtures. No network, no credentials, no
cloud account, no database.

## Prerequisites

| Need | Why | Notes |
| --- | --- | --- |
| Python 3.9+ | runs the engine | 3.9, 3.13 and 3.14 run the suite in CI; stdlib only, except… |
| PyYAML ≥ 6.0 | parses control/source config | `python3 -m pip install -r requirements.txt` |
| git | evidence and ISMS documents are reviewed as diffs | — |
| `gh` CLI | optional | for PR workflow |


When real sources arrive (Milestone 4 in [`PLAN.md`](PLAN.md)) they will
need **read-only credentials**: a token scoped to *read* the facts being checked,
never one that can change them. Those live outside the repository (environment
variables or a secret store) and are never committed — see
[`SECURITY.md`](SECURITY.md).

## Install and run

```bash
make install   # creates .venv and installs PyYAML into it
make help      # every target, one line each
make           # same as make next

make list      # configured controls and their checks
make demo      # collect from the synthetic fixtures, then verify every record
make status    # is what exists still true? (`make check` fails on findings)
make framework # declare framework(s); FRAMEWORK=... skips the menu
make init      # scaffold the ISMS documents, one at a time
make test      # the test suite
```

There is no install step for the engine itself — the package is imported from
`src/`, and the Makefile carries `PYTHONPATH=src` for you. Targets use `.venv/`
when it exists and the system `python3` otherwise; `.venv` is what keeps the
install working on systems where pip refuses to touch the system Python
(PEP 668).

You should see 7 passing controls, 7 verified records, and a green test suite. If
not, fix that before writing your own controls — nothing below means anything if
the engine does not run.

Flags:

```bash
PYTHONPATH=src python3 -m compliator collect --control soc2-cc8.1           # one control
PYTHONPATH=src python3 -m compliator collect --as-of 2026-10-17             # date for age checks
PYTHONPATH=src python3 -m compliator collect --simulate-failure github_org  # demo the fail-loud path
PYTHONPATH=src python3 -m compliator verify evidence/soc2-cc8.1/<collection-id>
```

Exit codes: `0` all passing · `1` a control failed its checks (findings-grade
evidence, still written) · `2` a collection error (nothing written for that
control).

## Scaffolding a new instance

The other half of the repository — the ISMS documents — can be started from
nothing, so a new instance is not a blank page:

```bash
PYTHONPATH=src python3 -m compliator init                    # one document at a time
PYTHONPATH=src python3 -m compliator init --dry-run          # print the plan, write nothing
PYTHONPATH=src python3 -m compliator init --answers a.yaml   # non-interactive, for CI or a script
PYTHONPATH=src python3 -m compliator init --target ../acme   # some other instance root
PYTHONPATH=src python3 -m compliator init --framework soc2   # skip the framework question
PYTHONPATH=src python3 -m compliator framework --set both    # declare frameworks, write their SoA
PYTHONPATH=src python3 -m compliator next                    # the one thing to do now; always exits 0
```

`next` runs the same checks as `status` in build order and prints the first unmet one with the command to run. A framework already declared (or implied by its SoA file) is not asked about again.

`init` scans the target for the documents an ISMS needs, prints which are present
and which are missing — that report is also the answer to "are we set up yet?" —
and then offers each missing one with a single question. Declining everything is
a valid answer and not an error.

Three rules it holds to:

- **Skeletons, not content.** Correct location, correct front matter, the
  headings, and a `TODO` wherever a fact about your organisation belongs. It
  never invents a policy statement, a risk rating, or an applicability decision.
- **Never overwrites.** A file that exists is reported and left alone. There is
  no force flag.
- **Never approves.** `approved_by` is omitted and `status` is `draft` (or `open`
  for a risk). Only a named human approves a document — VISION.md, principle 5.

The answers file takes `organization`, `what_it_does`, `owner`, `frameworks`
(`iso_27001_2022`, `soc2`, `both`, `none`), `policies` (`minimal`, `all`, `none`,
or a list of numbers), `risk_title`, `profile` (true/false answers to the
questions below), and a `create` map to veto individual items.
Unknown keys are an error rather than a typo that quietly does nothing.

**Default statements.** POL-001 and POL-003 are written with generic statements,
each prefixed `CONFIRM:`. `init` asks three questions (identity provider,
contractors, customer data; `profile:` in the answers file) to choose which apply.
`status` and `next` count a `CONFIRM:` like a `TODO`, so a policy cannot look
finished until its owner has checked each statement against what the
organisation does and removed the marker. Other policies keep their `TODO` skeleton.

Exit codes: `0` wrote what you asked (or there was nothing to do) · `2` refused:
unreadable answers file, unknown framework, a non-interactive run with no
answers, or no terminal to ask on.

## Is it still true?

`init` answers "are we set up?" by counting files. `status` answers the harder
question — is what exists still true — and it is the command to run in a daily or
CI check:

```bash
PYTHONPATH=src python3 -m compliator status                    # this repository, today
PYTHONPATH=src python3 -m compliator status --target ../acme   # another instance
PYTHONPATH=src python3 -m compliator status --as-of 2027-01-01 # age against a given date
PYTHONPATH=src python3 -m compliator status --config-dir config --evidence-dir evidence
```

It reads two halves and reports findings under three levels:

- **Documents** — front matter that is missing, unparseable, or has no `owner`;
  a document claiming `status: approved` with no `approved_by`; `approved` with
  `TODO`s still in it (unfinished work presented as done); a review overdue
  against the document's own `review_cadence`; no scope statement, no policies,
  or no risks recorded at all; and any `controls:` reference that no control in
  `config/controls/` defines, because a broken trace is the one thing a
  compliance repository cannot afford.
- **Evidence** — per control: whether a record exists, whether its latest result
  passed, whether it has aged past the control's `frequency_days`, and whether
  the record still verifies (hashes re-checked, so a hand-edited record is an
  error, not a passing check).

Levels are **error** (a claim contradicted by the files), **warning** (a
judgement call, and normal in a young instance), and **note** (worth knowing;
does not affect the exit code). Exit codes: `0` nothing to report · `1` errors
or warnings (a note-only run is `0`) · `2` could not run.

The evidence half shares one honesty rule with the engine: a check that did not
run is never a pass. If the control configuration cannot be loaded there are no
controls to check against, so that is itself a finding — a *missing* config is a
warning, because a documents-only instance is a legitimate way to start, while a
config that is there and will not parse (or one you asked for by name that is not
there) is an error. `LATEST.json` is likewise not taken at face value: it sits
outside the hashed record, so the record gets the last word on its own result.

It is read-only by construction: it writes nothing, fixes nothing, and has no
option that could change an instance. A scaffolded instance exits `1` on purpose
— the `TODO`s are the work.

## Try the failure paths

The failure paths are the point of the project, so they are worth a minute:

```bash
# a source that cannot be collected: loud, exit 2, no record written
PYTHONPATH=src python3 -m compliator collect --simulate-failure github_org

# a failing control: record written, exit 1
#   edit fixtures/github_org.json and set "push_protection": false on any repo
PYTHONPATH=src python3 -m compliator collect

# evidence that has aged out: exit 1, naming the control and the cadence
PYTHONPATH=src python3 -m compliator status --as-of 2027-01-01
```

## What the engine produces

Per control, per collection: `evidence.json` (statement, frameworks, each check
with its observed values, provenance, raw payload hash, verdict),
`raw/<source>.json` (untouched payload), `MANIFEST.json` (the schema id plus a
SHA-256 for every file), and a `LATEST.json` pointer that only moves on success.

Verification is re-computation, not trust: `PYTHONPATH=src python3 -m compliator
verify` walks the manifest, re-hashes every file, and confirms the record still
binds the raw payload it claims. It also refuses a record whose `schema` it does
not recognise, and reports when a record was written by a different engine
version than the one verifying it. Record integrity is the property the engine
actually provides; the tests tamper with a raw file and with `evidence.json` and
assert both are detected.

## Properties the design holds onto

These are why the storage shape and the runner look the way they do, and several
are asserted by tests:

- **Raw evidence retained** — the storage shape cannot be reduced to a verdict.
- **Observed values per check**, not just whether it passed.
- **Explicit population accounting** — an empty population is an error, never a
  vacuous pass.
- **Reproducible verdicts** — deterministic JSON, sorted keys; same facts + same
  config ⇒ same record apart from the timestamp.
- **Thin collectors, no hidden judgment** — all assertion logic lives in one
  evaluator, driven by YAML.
- **Manual evidence with provenance** — human forms flow through the same
  pipeline as machine facts.
- **Exact policy/check version pinning** — every record carries the hash of the
  control definition that produced it.
- **Fail loud** — a broken source is exit code 2, a loud banner, and *no record*.

## Adding a control

```yaml
control:
  id: soc2-cc6.6
  title: ...
  statement: >
    ...
  owner: security@example.invalid
  frequency: 1d             # evidence older than this is flagged stale
  mappings:                 # ids must exist in frameworks/<framework>.yaml
    soc2: [CC6.1]
    iso_27001_2022: [A.8.5]

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

`frameworks/<id>.yaml` lists a framework's requirement ids with our own one-line
summaries (no standard text). An unknown framework or id fails the load. A
catalog marked `complete: true` lets `status` and `next` report declared
requirements that no control maps to; the catalogs shipped here are partial, so
they report nothing. The old free-text `frameworks:` mapping still loads.

Operators — population: `all_equal`, `exists`, `date_within_days`,
`min_gte`, `count_gte`; scalar: `equals`, `gte`, `exists`, `count_gte`. Misuse
(unknown op, population op with no population, dangling source, duplicate id) is
a hard error before collection starts.

## Adding a source

One thin module in `src/compliator/plugins/` (subclass `SourcePlugin`; `fetch()`
returns a JSON-safe mapping) plus one entry in `config/sources.yaml`. Plugins
only fetch and normalise facts — never judge.

## Limitations

See the top-level [`README.md`](README.md) for the full list, including the
one that matters most: hashing proves a record was not modified relative to its
manifest. It does not authenticate the collector, prove completeness, or show
that a passing check means an organizational control is effective.
