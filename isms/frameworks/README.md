# Frameworks

How an external framework relates to your policies and controls. Short design
note — there is **no code for any of this yet**, and the control configs
currently carry framework references as free-text strings, which is exactly what
this note argues should change.

## The layers

```
Framework (ISO/IEC 27001:2022, SOC 2 TSC, ...)
   └── Requirement (catalog item: A.8.32, CC8.1)      external, fixed, referenced by id
          │
          │   SoA: applicable? why? implemented?      ← the decision
          ▼
       Our policy (POL-004)                            our rule, satisfies requirements
          │
          ▼
       Our control (soc2-cc8.1)                        our claim, treats risks, mapped outward
          │
          ▼
       Checks                                          deterministic assertions over facts
```

## Four rules

1. **Framework requirements and our controls are different things.** Requirements
   are external and fixed; controls are ours. Keep one control set and map it
   outward.
2. **The mapping is many-to-many.** One control can satisfy several requirements
   (`soc2-cc8.1` ≈ `A.8.32` ≈ a NIST 800-53 `CM` control), and one requirement can
   need several controls. Duplicating a control per framework is the standard
   tooling mistake — you end up evidencing the same thing three times, and the
   three copies drift.
3. **The SoA is the join.** Applicability plus justification plus status *is* the
   mapping from a framework requirement to our controls. It is not a separate
   artifact.
4. **Not every framework wants one.** ISO/IEC 27001 requires a statement of
   applicability; SOC 2 does not (you choose criteria and describe the system).
   Framework metadata has to carry that difference rather than assuming it.

## Why it is worth fixing rather than living with free text

Today a control says `soc2: "CC8.1 - Change management (illustrative mapping)"`.
That means:

- a typo (`A.8.3z`, `CC8.10`) is invisible — nothing validates the identifier;
- "which Annex A controls have no covering control?" cannot be answered, so
  coverage gaps are unknowable;
- policy-to-requirement traces are prose, not data, so nothing can check them.

## Direction (not built)

- `isms/frameworks/<framework-id>.yaml` — a catalog: identifier, our own
  one-line summary, whether it is a clause or a control, framework version.
  **Identifiers and our own summaries only.** No copyrighted standard text is
  stored or redistributed ([`../../VISION.md`](../../VISION.md), principle 9).
- Control configs keep the mapping, structured and validated:

  ```yaml
  mappings:
    iso_27001_2022: [A.8.32]
    soc2_tsc: [CC8.1]
  ```

  The loader fails loudly on an identifier that is not in the catalog — a small
  change to `compliator/config.py`, turning a comment into an assertion.
- The framework version is pinned in the catalog and, ideally, in the evidence
  record alongside `config_sha256`, so a framework revision cannot silently
  reinterpret old evidence.
- Later: a coverage report — reverse the mapping and list requirements with no
  covering control, plus the documentation-consistency checks described in
  [`../../PLAN.md`](../../PLAN.md).

## Open questions

- Conformance language. Saying "conforms to A.8.32" claims something about the
  whole organizational control, not the technical check that passed. What is the
  honest wording — "implemented", "covered", "partially evidenced"?
- One requirement, several controls, none of which alone demonstrates it. How is
  partial coverage recorded without implying the requirement is met?
- Who owns a catalog, and how does it get updated when a framework is revised?
  (Milestone 2 decides where this lives; it is reference data, not ISMS content.)
- Whether catalog files belong in the public repo at all, or should be fetched,
  given the copyright boundary.

## Status

Written up now so the shape is visible before code exists. Milestone 1 reviews
it alongside [`../../VISION.md`](../../VISION.md); the catalog and validation are
their own later change.
