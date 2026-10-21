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
  deterministic serialisation, and the never-write-empty-evidence rule, not just
  passing tests.
- **No new runtime dependencies** without a specific reason in the pull
  request. The engine currently needs only PyYAML.
- **No banned vocabulary.** Marketing adjectives and AI-slop fillers fail CI
  in both file contents and file names. The list is
  [`scripts/slop-words.txt`](scripts/slop-words.txt); `make check-words` runs
  the gate locally. The list changes by pull request, never by exception.

## Development

```bash
make install   # creates .venv, installs PyYAML into it
make install-dev  # adds ruff, mypy, coverage, bandit, pip-audit
make ci        # lint, types, coverage floor, security scan: what CI gates on
make format    # apply ruff fixes and formatting
make test      # unit test suite
make demo      # collect from the synthetic fixtures, then verify every record
```

Plain `make` lists every target with a one-line description — nothing here
needs copying out of this file.

The engine is imported from `src/`, not installed, so the Makefile carries
`PYTHONPATH=src` for you.

Every push to `main` and every pull request runs those commands in GitHub Actions
across Python 3.9 to 3.14 (plus lint, types, coverage, security, CodeQL and workflow lint jobs) (`.github/workflows/ci.yml`) — unit tests, then
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

## The documents under `isms/`

Written once here so each folder's README can stay about its own subject. These
are the conventions the repository already follows; `compliator init` writes new
documents to match them.

- **Markdown, with narrow front matter.** A few keys that something actually
  reads. Structured metadata only where a machine needs it.
- **One file per policy, one per risk.** Reviews then show up as a readable diff
  against a single document.
- **Stable ids.** `SCOPE-001`, `POL-001`, `RISK-001`, `SOA-001`; controls use
  their own scheme (`soc2-cc8.1`). An id is permanent: the trace from a policy to
  the evidence that proves it runs through ids, so renaming one breaks history.
  Numbering encodes sequence, not importance — see
  [`isms/policies/README.md`](isms/policies/README.md).
- **Every document has a named owner and a review date.** An unattributed
  document is not evidence of anything.
- **`status:` is honest.** `draft` means nobody has approved it. Agents draft and
  propose; a named human approves ([`VISION.md`](VISION.md), principle 5).
- **No copyrighted standard text.** Reference requirements by identifier
  (`A.8.32`, `CC8.1`) with your own one-line summary. Never paste Annex A or TSC
  text into this repository.
- **Manual forms live in [`manual/`](manual/), not in `isms/`.** A policy is the
  rule; a signed form is evidence the rule was followed.

## Design constraints to respect

These are load-bearing, and tests assert several of them. The full list lives
in [`ENGINE.md`](ENGINE.md), "Properties the design holds onto" — read it
before changing how evidence is written, verified, or stored. One nuance it
does not settle: distinguishing "no population", "failed enumeration", and
"legitimately absent resources" is still an open design question (`PLAN.md`).

## Open questions

Several known-good discussions are listed in `PLAN.md` under the milestone they
belong to. If you want to work on one, open an issue first so the design can be
agreed before code.
