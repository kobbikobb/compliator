# ISMS documents

The human-readable part of the ISMS: what is in scope, which policies apply,
which risks are managed, and which framework controls are applicable. The
machine-checkable part lives in `config/` and `evidence/`.

Nothing in here requires the software. These are Markdown files in git,
reviewed like code. You can keep them with or without the engine.

## Status: templates

Every folder holds a `_template.md` and no real content. The reference
organisation is fictional, and the templates say so. Nothing here is a working
security programme, and none of it is reviewed by an auditor.

## Order to populate

Do these in order — each one gives the next something to reference.

| # | Folder | Document | Why here |
| --- | --- | --- | --- |
| 0 | [`scope/`](scope/) | ISMS scope | Nothing else can be written until you know what is in scope |
| 1 | [`policies/`](policies/) | Information Security Policy (`POL-001`) | The one policy the standard requires; states the commitment |
| 2 | [`policies/`](policies/) | Risk Management Policy (`POL-002`) | Says how you identify, assess, and treat risk |
| 3 | [`risks/`](risks/) | Risk register (`RISK-001`…) | The actual risks, assessed and treated |
| 4 | [`soa/`](soa/) | Statement of Applicability | Which framework controls apply to you, and why — a decision made *from* the risks |
| 5 | [`policies/`](policies/) | The rest of the policies (`POL-003`…) | Only the ones the SoA says you need |
| 6 | `config/controls/` | Controls with checks | The machine-checkable claims |

The order matters at steps 3–5. Assessing risks first tells you which controls
apply, so the SoA decides how many topic policies you actually need. Writing 40
policies and then discovering that 12 of them were never applicable is the
standard way this goes wrong.

## Shared conventions

Kept in one place so each folder's README can stay about its own subject.

- **Markdown, with narrow front matter.** A few keys that something actually
  reads. Structured metadata only where a machine needs it.
- **One file per policy, one per risk.** Reviews then show up as a readable diff
  against a single document.
- **Stable ids.** `SCOPE-001`, `POL-001`, `RISK-001`, `SOA-001`; controls use
  their own scheme (`soc2-cc8.1`). An id is permanent: the trace from a policy
  to the evidence that proves it runs through ids, so renaming one breaks
  history. Numbering is described per folder — it encodes sequence, not
  importance.
- **Every document has a named owner and a review date.** An unattributed
  document is not evidence of anything.
- **`status:` is honest.** `draft` means nobody has approved it. Agents draft and
  propose; a named human approves (see [`../VISION.md`](../VISION.md) principle 5).
- **No copyrighted standard text.** Reference requirements by identifier
  (`A.8.32`, `CC8.1`) with your own one-line summary. Do not paste Annex A or TSC
  text into this repository.
- **Simulated data only.** The repository is public:
  [`../SECURITY.md`](../SECURITY.md).

## Frameworks

How framework requirements connect to your policies and controls — and where
they do not — is described in [`frameworks/`](frameworks/). Short version: the
framework is external and fixed, your controls are yours, the mapping is
many-to-many, and the SoA is where applicability gets decided.

## Related

- Manual evidence (filled-in acknowledgment and review forms) lives in
  `manual/`, not here. A policy is the rule; a signed form is evidence the rule
  was followed.
- [`../PLAN.md`](../PLAN.md) — which milestone builds what.
- [`../SECURITY.md`](../SECURITY.md) — what must never be committed.
