# Compliator

**Repo-native compliance evidence: verifiable records, deterministic checks, no
platform required.**

An ISMS kept in a git repository. The documents — scope, policies, risks,
applicability — are Markdown you review like code. The evidence is verifiable:
anyone can re-derive a verdict from a record without running this application.

**The evidence artifact is the product; the tool is disposable.**

## Try it

```bash
python3 -m pip install -r requirements.txt          # PyYAML - the only dependency

PYTHONPATH=src python3 -m compliator init --dry-run # what would this instance need?
PYTHONPATH=src python3 -m compliator init           # write the skeletons, one document at a time
PYTHONPATH=src python3 -m compliator status         # is any of it still true?
make demo                                           # collect + verify against the synthetic fixtures
```

`init` scans for the documents an ISMS needs, reports which are missing, and
offers each one. What it writes is a skeleton — the right location, correct front
matter, the headings, and a `TODO` wherever a fact about your organisation
belongs. It never overwrites a file, and never sets `status: approved`: a named
human approves. Flags, exit codes and the `--answers` file are in
[`ENGINE.md`](ENGINE.md).

`status` reads the result back and reports whether it is still true: unfilled
`TODO`s, a document claiming `approved` with nobody behind it, reviews overdue
against their own cadence, a policy citing a control that does not exist, and per
control whether the evidence exists, passed, is current, and still verifies.
Read-only, and exit `1` on errors or warnings, so it can gate CI.

## Two halves, and you only need one to start

| | Lives in | Needs software? |
| --- | --- | --- |
| **ISMS documents** — scope, policies, risks, statement of applicability | [`isms/`](isms/) | No. Markdown in git. |
| **Verification engine** — declares checks and packages verifiable evidence | [`src/compliator/`](src/compliator/) | Yes. Python, one dependency. |

An ISMS here needs no engine at all: add evidence later, for whichever controls
are machine-checkable.

## What the engine does

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

Properties the design holds onto, in outline — raw evidence retained rather than
reduced to a verdict, explicit population accounting (an empty population is an
error, never a vacuous pass), verdicts reproducible from the record alone, and a
broken source failing loudly with no record written. The rest of them, and what
each one costs, are in [`ENGINE.md`](ENGINE.md).

## The documents

Written in dependency order — **scope → `POL-001` → `POL-002` → risks → statement
of applicability → the rest of the policies → controls** — because each step
gives the next one something to reference, and because the two mistakes here are
both orderings. Risk assessment decides which controls apply and the SoA records
that decision, so writing forty policies first leaves you with a dozen that were
never applicable. And scope is document #0 rather than `POL-000`: scope says
*what is covered*, a policy says *what you must do*, and the two are evidenced
differently.

`init` walks exactly that order. The policy numbering, which is also the order to
write them in, is in [`isms/policies/README.md`](isms/policies/README.md); the
conventions the documents follow are in [`CONTRIBUTING.md`](CONTRIBUTING.md).

**Where frameworks fit.** A framework is external and fixed; your controls are
yours, and the mapping is many-to-many — one control can satisfy requirements in
several frameworks. The statement of applicability is where applicability gets
decided, which is why ISO/IEC 27001 gets one and SOC 2 does not. See
[`isms/frameworks.md`](isms/frameworks.md).

## Running the engine

```bash
PYTHONPATH=src python3 -m compliator list             # configured controls and their checks
PYTHONPATH=src python3 -m compliator collect          # collect everything (synthetic fixtures)
PYTHONPATH=src python3 -m compliator verify evidence  # re-verify every record's hashes
PYTHONPATH=src python3 -m unittest discover -s tests  # the test suite
```

Prerequisites, flags, exit codes, the failure paths worth trying, what a record
contains, and how to add a control or a source are all in [`ENGINE.md`](ENGINE.md).
CI runs the suite and the end-to-end demo on Python 3.9, 3.13 and 3.14.

## What this is not

- **Not an ISMS, yet.** The engine works; the documents are drafts and templates
  (Milestones 2–3 in [`PLAN.md`](PLAN.md)).
- **Not a compliance platform**, which is the trade-off rather than a criticism:
  instead of trusting a vendor's summary, make the evidence itself independently
  checkable and keep it in git, where it is reviewed like code. Same underlying
  evidence for an auditor; different inspectability. See [`VISION.md`](VISION.md).
- **Not certification, and not evidence of compliance.** Nothing here has been
  reviewed by an auditor or a compliance professional. A passing record means one
  declared check held against one captured set of facts at one point in time.
- **Not authoritative mappings.** Framework references in `config/controls/*.yaml`
  are illustrative placeholders. Standards are cited by identifier only; no
  copyrighted standard text is redistributed.

## Layout

```
isms/                        the documents: scope, policies, risks, applicability
config/                      sources.yaml + one file per control (metadata + checks)
fixtures/  manual/           synthetic facts, and synthetic human-filled forms
src/compliator/              the engine package - see ENGINE.md
evidence/<control-id>/       generated output (gitignored)
tests/                       stdlib unittest suite
ENGINE.md · VISION.md · PLAN.md · SECURITY.md · CONTRIBUTING.md
```

## Limitations

Honest list, with detail in [`PLAN.md`](PLAN.md).

- **Synthetic data only.** `fixtures/` and `manual/` are hand-written stand-ins.
- **Integrity, not authenticity.** Hashing shows a record was not modified
  relative to its manifest; it does not authenticate the collector or prove the
  population was enumerated honestly. `LATEST.json` can be rewritten by anyone
  with write access.
- **A passing check is not a working control.** One control may need several
  checks, and no check can demonstrate that an organizational control is effective.
- **Empty versus absent is unresolved** — a tracked open question, not a solved one.
- **`init` writes drafts, and `status` only checks what a file can show.** It
  reads `TODO` markers, front matter and record hashes; it cannot tell whether a
  rating is honest or whether prose means what it says.
- **Attestations are not cryptographically signed**, and there is no retention,
  immutability, access control, scheduling, or remediation workflow.
- **Not reviewed by a compliance professional or auditor.**

## License

Apache-2.0 — see [`LICENSE`](LICENSE). Third-party names and standards
identifiers are referenced for description only; no third-party standard text is
included.

## Security

Do not put real evidence, credentials, or sensitive data in this repository — see
[`SECURITY.md`](SECURITY.md).
