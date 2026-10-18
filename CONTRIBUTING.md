# Contributing

This is early work. Small, well-explained changes are much more useful
than large ones, and there is no roadmap obligation implied by opening an issue.

## Ground rules

- **Simulated data only.** No real company data, credentials, evidence, or
  customer information — ever, in code, fixtures, examples, issues, or commits.
  Fictional entities should use reserved domains (`example.invalid`,
  `example.com`) and clearly synthetic identifiers.
- **Do not copy copyrighted material.** No ISO/IEC standard text, no vendor
  templates, no third-party data models. Cite standards by identifier only.
- **Keep the trust boundary small.** `src/compliator/packager.py` is the component
  auditors are asked to trust. Changes there need reasoning about hashing,
  canonicalisation, and the never-write-empty-evidence rule, not just passing
  tests.
- **No new runtime dependencies** without a specific reason in the pull
  request. The engine currently needs only PyYAML.

## Development

```bash
python3 -m pip install -r requirements.txt
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m compliator collect          # runs against the synthetic fixtures
PYTHONPATH=src python3 -m compliator verify evidence
```

The engine is imported from `src/`, not installed, so `PYTHONPATH=src` is the
whole setup. `make demo`, `make test`, `make clean` wrap the same commands.

Every push to `main` and every pull request runs those commands in GitHub Actions
across Python 3.9, 3.13 and 3.14 (`.github/workflows/ci.yml`) — unit tests, then
the end-to-end collect-and-verify. Nothing is merged on local green alone.

## Reviews

Review comments are advisory: a named human approves documents
([`VISION.md`](VISION.md), principle 5). [`.coderabbit.yaml`](.coderabbit.yaml)
encodes this repository's own rules for the reviewer — read it before arguing
with a comment, because a comment citing "an empty population is an error" is a
constraint from this project, not a taste preference. The configuration leaves
CodeRabbit's request-changes workflow off, so it comments rather than gating the
branch; an explicit `@coderabbitai approve` command exists, but approving a
pull request stays a human action here.

The repository is public and below CodeRabbit's automatic-review threshold (10
stars), so nothing reviews a pull request on its own. Someone comments
`@coderabbitai review` on it. The configuration is written for the day the
repository passes that threshold; the star count is the only lever, and it is
not one worth faking.

## What a change should include

1. A brief explanation of the problem, in the pull request description.
2. Tests for behaviour changes (`tests/`, stdlib `unittest`).
3. Updated docs when the change affects how evidence is produced, verified, or
   interpreted — `README.md` for behaviour and limits, `PLAN.md`/`VISION.md`
   only when the direction genuinely changes.

## Design constraints to respect

These are load-bearing, and tests assert several of them:

- A collection failure writes **no** evidence record and surfaces loudly; it
  never degrades into an empty or stale pass.
- An empty population is an **error**, not a vacuous pass — though as noted in
  `PLAN.md`, distinguishing "no population", "failed enumeration", and
  "legitimately absent resources" is still an open design question.
- Records keep the raw source payload alongside the verdict, and every check
  records the values it observed.
- Verification re-computes hashes; it never trusts stored ones.

## Open questions

Several known-good discussions are listed in `PLAN.md` under the milestone they
belong to. If you want to work on one, open an issue first so the design can be
agreed before code.
