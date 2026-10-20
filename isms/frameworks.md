# Frameworks

How an external framework relates to your policies and controls. Short design
note; what is built is listed under "Built" below.

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

## Built

- `frameworks/<framework-id>.yaml`: requirement ids and our own summaries, with a
  version and a `complete` flag. No standard text.
- Controls carry `mappings: {framework: [ids]}`; the loader fails on an unknown
  framework or id.
- `status` and `next` report requirements of a declared framework that no control
  maps to, for catalogs marked `complete: true`.

## Not built

- Complete catalogs. The two shipped are partial, so no coverage gap can show.
- The framework version pinned in the evidence record next to `config_sha256`.
- Policy-to-requirement traces as data.

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
