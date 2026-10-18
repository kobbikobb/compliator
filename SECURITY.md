# Security Policy

## Do not put sensitive evidence in this repository

This project is an open prototype. **Everything in it is public.**

Do not commit:

- real audit evidence, screenshots, or exports from a real organization;
- raw provider payloads containing personal data, customer data, secrets,
  tokens, account identifiers, or internal hostnames;
- credentials, API keys, `.env` files, or private keys of any kind;
- anything under an NDA, or redistributed third-party standard text
  (ISO/IEC management-system or Annex A text is copyrighted and must not be
  copied here).

Evidence from real systems belongs in private storage outside this repo (local
gitignored paths first; a private object store later if justified). See
`.gitignore` for what is already excluded, and `README.md` for the trust model.

## Simulated data only

Fixtures, example companies, and manual evidence forms in this repository are
explicitly synthetic. If you add an example, label it as simulated and invent
identifiers. Use reserved domains such as `example.invalid` for fictional
people, hosts, and mailboxes.

## Reporting a vulnerability

Please report security problems privately rather than in a public issue:

1. Use GitHub's private vulnerability reporting on this repository
   (Security → Report a vulnerability), or
2. If that is unavailable, open a minimal public issue asking for a private
   contact channel, without disclosing details.

Include: what you found, how to reproduce it, the affected version/commit, and
the impact you believe it has. There is no bug bounty and no guaranteed
response time — this is maintained in spare time — but genuine reports are
appreciated and will be acknowledged.

## Scope and expectations

The threat model this project takes seriously is narrow: evidence integrity and
honest reporting. Concretely, defects worth reporting include a collection
failure that silently writes empty or misleading evidence, a manipulation of a
record that survives verification, or a fixture that leaks something it should
not. Note that hashing detects edits *relative to a trusted manifest*; it does
not authenticate the collector and does not prove completeness — see the
limitations section of `README.md` before treating a passing record as proof.
