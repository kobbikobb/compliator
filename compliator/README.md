# Compliator — the software

The engine that turns declared checks into verifiable evidence records. Optional:
the ISMS documents at the repository root work perfectly well without it.

Everything here runs against synthetic fixtures. No network, no credentials, no
cloud account, no database.

## Prerequisites

| Need | Why | Notes |
| --- | --- | --- |
| Python 3.9+ | runs the engine | developed on 3.14; stdlib only, except… |
| PyYAML ≥ 6.0 | parses control/source config | `python3 -m pip install -r requirements.txt` |
| git | evidence and ISMS documents are reviewed as diffs | — |
| `gh` CLI | optional | only for creating PRs / talking to GitHub later |

When real sources arrive (Milestone 4 in [`../PLAN.md`](../PLAN.md)) they will
need **read-only credentials**: a token scoped to *read* the facts being checked,
never one that can change them. Those live outside the repository (environment
variables or a secret store) and are never committed — see
[`../SECURITY.md`](../SECURITY.md).

## Install and run

```bash
python3 -m pip install -r requirements.txt

python3 -m compliator list                 # configured controls and their checks
python3 -m compliator collect              # collect everything (synthetic fixtures)
python3 -m compliator verify evidence      # re-verify every record's hashes
python3 -m unittest discover -s tests -v   # the test suite
```

`make demo`, `make test`, `make clean` from the repository root wrap the same
commands.

You should see 7 passing controls, 7 verified records, and a green test suite. If
not, fix that before writing your own controls — nothing below means anything if
the engine does not run.

Flags:

```bash
python3 -m compliator collect --control soc2-cc8.1           # one control
python3 -m compliator collect --as-of 2026-10-17             # date for age checks
python3 -m compliator collect --simulate-failure github_org  # demo the fail-loud path
python3 -m compliator verify evidence/soc2-cc8.1/<collection-id>
```

Exit codes: `0` all passing · `1` a control failed its checks (findings-grade
evidence, still written) · `2` a collection error (nothing written for that
control).

## Try the failure paths

Both are the point of the project, so they are worth a minute:

```bash
# a source that cannot be collected: loud, exit 2, no record written
python3 -m compliator collect --simulate-failure github_org

# a failing control: record written, exit 1
#   edit fixtures/github_org.json and set "push_protection": false on any repo
python3 -m compliator collect
```

## What the engine produces

Per control, per collection: `evidence.json` (statement, frameworks, each check
with its observed values, provenance, raw payload hash, verdict),
`raw/<source>.json` (untouched payload), `MANIFEST.json` (hashes plus the
verification command), and a `LATEST.json` pointer that only moves on success.

Verification is re-computation, not trust: `python -m compliator verify` walks the
manifest, re-hashes every file, and confirms the record still binds the raw
payload it claims. Record integrity is the property the engine actually provides;
the tests tamper with a raw file and with `evidence.json` and assert both are
detected.

## Adding a control

```yaml
control:
  id: soc2-cc6.6
  title: ...
  statement: >
    ...
  owner: security@example.invalid
  frequency: 1d             # evidence older than this is flagged stale
  frameworks:               # free text today; see ../frameworks.md
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
(unknown op, population op with no population, dangling source, duplicate id) is
a hard error before collection starts.

## Adding a source

One thin module in `compliator/plugins/` (subclass `SourcePlugin`; `fetch()`
returns a JSON-safe mapping) plus one entry in `config/sources.yaml`. Plugins
only fetch and normalise facts — never judge.

## Limitations

See the top-level [`../README.md`](../README.md) for the full list, including the
one that matters most: hashing proves a record was not modified relative to its
manifest. It does not authenticate the collector, prove completeness, or show
that a passing check means an organizational control is effective.
