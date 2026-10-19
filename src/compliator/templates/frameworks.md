# Frameworks

Which external framework(s) this instance orients to, and where the decisions
about them live. A framework is external and fixed; our controls are ours, and
the mapping between them is many-to-many.

## Declared

$framework_rows

TODO: add the reason for each choice (a customer requirement, a contract, a
decision to prepare for a future audit) — an unstated reason gets re-litigated.

## What this means for the documents

- **Requirements and our controls are different things.** Reference framework
  requirements by identifier with your own summary; never paste standard text.
- **One control set, mapped outward.** Do not duplicate a control per framework.
- **The statement of applicability is the join** where a framework requires one:
  applicability plus justification plus status *is* the mapping.
- **Not every framework wants one.** ISO/IEC 27001 requires a statement of
  applicability; SOC 2 does not — you choose Trust Services Criteria and describe
  the system instead.

The longer argument, including where the free-text framework references in
`config/controls/*.yaml` should go instead, is in the repository's
`isms/frameworks.md`.
