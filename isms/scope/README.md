# Scope

One document: `scope.md`, from [`_template.md`](_template.md). Template only —
no scope has been written yet.

An ISMS scope answers: what does this system of management actually cover? Which
organisation, systems, data, and boundaries — and what is deliberately left out.
Everything else in `isms/` is written inside these boundaries, so this comes
first.

## Is scope a policy?

No, and the distinction is worth keeping:

| | Scope | Policy |
| --- | --- | --- |
| Says | *what is covered* | *what you must do* |
| Answers | "does this system apply here?" | "are we following the rule?" |
| Can be violated | no — it is a definition | yes — that is the point |

The standard treats scope as its own documented information (clause 4.3), not a
policy. Nothing stops you filing it next to the policies, and it is document
#0 in the reading order — but calling it `POL-000` would blur "we defined our
boundary" with "we committed to a rule", and those two get evidenced
differently.

## What belongs in it

- who the organisation is, briefly, in plain language
- the systems, services, and data the ISMS covers, by name
- data categories and how sensitive each is
- what is out of scope, and why
- who is accountable, including who approves policies and accepts risk
- which standards you are orienting to, and that you claim no certification
- assumptions you have not verified

## Rules

- Name real systems, not categories. "The production database" beats "data stores".
- Say what is excluded. An unwritten exclusion reads as a gap; a written one is
  a decision.
- Keep it to a page or two. It is a boundary, not a description of the business.
- Keep identifiers (`SCOPE-001`) and conventions from [`../README.md`](../README.md).
