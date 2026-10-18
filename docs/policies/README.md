# Policies

One Markdown file per policy, in this directory. Policies are the rules you
commit to; controls (`config/controls/*.yaml`) are the claims that implement
them, and evidence is the proof they hold.

## Status: template

`_template.md` is a template. No policies have been written. Use
`copy _template.md _template`-style duplication only for real policies, and
delete the prompts.

## Filename and id

`POL-<AREA>-<NNN>.md`, and the same id in the front matter. Examples:
`POL-ACCESS-001.md`, `POL-CHANGE-001.md`, `POL-VENDOR-001.md`.

Ids are permanent. The trace from a policy to the evidence that proves it goes
through the control id, so changing ids breaks history.

## Two kinds of policy statement, and they are not equal

- **Verifiable** — "every production change is merged through a reviewed pull
  request". This can have a control with checks that read facts from a system of
  record. Say which control implements it.
- **Judgemental** — "we consider security when selecting vendors". Real and
  necessary, but not machine-checkable. Say so honestly, and if it needs
  evidence, point at the human record (a vendor review form in `manual/`) rather
  than inventing a check that does not mean anything.

Do not dress the second kind up as the first. It is the fastest way to make a
whole evidence set worthless.

## Minimum bar for a policy worth keeping

1. **Actionable.** A reader can tell whether they are following it.
2. **Owned.** A named person or role, who exists.
3. **Reviewed on a stated cadence**, with `last_reviewed` filled in only when a
   review actually happened.
4. **Linked to controls** where a control exists, or an explicit note that it is
   reviewed by humans only.
5. **Short.** A page beats five. If it needs five, it is probably two policies.

## Front matter

```yaml
---
id: POL-ACCESS-001
title: Access Control Policy
owner: security@example.invalid
status: draft                 # draft | approved | retired
review_cadence: annual        # annual | semiannual | quarterly
last_reviewed: 2026-10-01     # omit until reviewed
approved_by:                  # omit until a human approves; agents cannot fill this
controls:
  - soc2-cc6.1
---
```

See [`_template.md`](_template.md) for the document body, and
[`../README.md`](../README.md) for the conventions shared by all ISMS documents.

## Approvals

Marking `status: approved` and filling `approved_by` is a human act. An agent may
*draft* a policy, propose an update, and flag that a review is due. It may not
approve one, and a change that flips `status` to `approved` without a named human
behind it should be rejected in review. See [`../../VISION.md`](../../VISION.md),
principle 5.
