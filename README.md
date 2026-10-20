# Compliator

**Repo-native compliance evidence: verifiable records, deterministic checks, no
platform required.**

An ISMS kept in a git repository. The documents — scope, policies, risks,
applicability — are Markdown you review like code. The evidence is verifiable:
anyone can re-derive a verdict from a record without running this application.
**The evidence artifact is the product; the tool is disposable.**

## Try it

```bash
make install   # create .venv and install PyYAML into it
make           # name the one thing to do now (same as `make next`)

make framework # declare ISO/IEC 27001, SOC 2, or both
make init      # scaffold the ISMS documents, one at a time
make status    # every gap; `make check` fails on any
make demo      # collect + verify against the synthetic fixtures
```

Run `make` after each step; it names what to do next. `init` never
overwrites and never approves — a named human does. `status` is read-only and
exits `1` on errors or warnings, so it can gate CI (`make check`). Flags, exit
codes and the `--answers` file are in [`ENGINE.md`](ENGINE.md).

## Two halves, and you only need one to start

| | Lives in | Needs software? |
| --- | --- | --- |
| **ISMS documents** — scope, policies, risks, statement of applicability | [`isms/`](isms/) | No. Markdown in git. |
| **Verification engine** — declares checks and packages verifiable evidence | [`src/compliator/`](src/compliator/) | Yes. Python, one dependency. |

The engine reads `config/controls/*.yaml`, pulls raw facts through plugins,
evaluates checks, and packages each collection: `evidence.json` (verdict,
observed values, provenance), the raw payload, a SHA-256 manifest, and a
`LATEST.json` that moves only on success. An empty population is an error; a
broken source fails loudly and writes no record. The full property list and
how to add a control: [`ENGINE.md`](ENGINE.md).

## Layout

```
isms/                        scope, policies, risks, applicability
config/                      sources.yaml + one file per control
fixtures/  manual/           synthetic facts, synthetic human-filled forms
src/compliator/              the engine - see ENGINE.md
evidence/<control-id>/       generated output (gitignored)
tests/                       stdlib unittest suite
ENGINE.md · VISION.md · PLAN.md · SECURITY.md · CONTRIBUTING.md
```

## What this is not

- **Not an ISMS yet.** Engine works; documents are drafts ([`PLAN.md`](PLAN.md)).
- **Not a compliance platform** — the trade, not a criticism: the evidence is
  independently checkable and lives in git, reviewed like code
  ([`VISION.md`](VISION.md)).
- **Not certification, and not auditor-reviewed.** A passing record is one
  declared check holding against one captured set of facts at one point in time.
- **Not authoritative mappings.** Framework references are illustrative
  placeholders; standards are cited by identifier only, no standard text.

## Limitations

Honest list in [`PLAN.md`](PLAN.md): synthetic data only; integrity, not
authenticity; a passing check is not a working control; empty-vs-absent
unresolved; attestations not signed.

## License

Apache-2.0 — [`LICENSE`](LICENSE). Third-party names and standards identifiers
are referenced for description only; no third-party standard text is included.

## Security

Do not put real evidence, credentials, or sensitive data in this repository —
see [`SECURITY.md`](SECURITY.md).
