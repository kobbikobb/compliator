"""What should happen next?

``compliator status`` lists everything outstanding. This names the one thing to
do now, following the order an ISMS is built in: framework, scope, risks, the
statement of applicability, policies, finishing the documents, controls, evidence.

Read-only, and the exit code is always 0 - it is advice, not a gate. The
documents and evidence are judged by the same checks ``status`` uses, so the two
cannot disagree about what is wrong; this only picks the first thing and says
what to do about it.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, TextIO

from .catalog import POLICIES, RISK_PATH, SCOPE_PATH, SUGGESTED_START
from .config import load_project
from .errors import CompliatorError, ConfigError
from .onboarding import declared_frameworks
from .status import Finding, check_documents, check_evidence


@dataclass(frozen=True)
class Step:
    what: str
    why: str
    do: str


@dataclass
class _Instance:
    target: Path
    today: date
    controls: list[Any]
    config_error: str | None
    evidence_root: Path
    findings: list[Finding]


Check = Callable[[_Instance], Step | None]


def _framework(inst: _Instance) -> Step | None:
    if declared_frameworks(inst.target):
        return None
    return Step(
        "No framework declared.",
        "The framework decides which statement of applicability you write and which requirements you work toward.",
        "make framework   (or: make framework FRAMEWORK=iso_27001_2022|soc2|both)",
    )


def _scope(inst: _Instance) -> Step | None:
    if (inst.target / SCOPE_PATH).is_file():
        return None
    return Step("No scope statement.", "Nothing says what the ISMS covers, so nothing can be judged complete.", "make init")


def _risks(inst: _Instance) -> Step | None:
    if list((inst.target / "isms" / "risks").glob("RISK-*.md")):
        return None
    return Step(
        "No risks recorded.",
        "Risks decide which requirements apply and which policies you need.",
        "make init   (then describe what could go wrong)",
    )


def _soa(inst: _Instance) -> Step | None:
    for framework in declared_frameworks(inst.target):
        if framework.soa_path and not (inst.target / framework.soa_path).is_file():
            return Step(
                f"No statement of applicability for {framework.title}.",
                "It records which requirements apply, why, and what covers them - the first thing an auditor reads.",
                f"make framework FRAMEWORK={framework.key}",
            )
    return None


def _policies(inst: _Instance) -> Step | None:
    existing = {path.name.split("-", 2)[1] for path in (inst.target / "isms" / "policies").glob("POL-*.md")}
    by_number = {policy.number: policy for policy in POLICIES}
    wanted = [by_number[number] for number in SUGGESTED_START if f"{number:03d}" not in existing]
    if not wanted:
        return None
    if len(wanted) == len(SUGGESTED_START):
        what = "No policies yet."
    else:
        what = f"{len(wanted)} recommended policies not written: " + ", ".join(policy.id for policy in wanted[:4])
        what += " and more." if len(wanted) > 4 else "."
    return Step(what, "Policies are the rules the applicable requirements are met with.", "make init")


def _document_order(subject: str) -> tuple[int, str]:
    if subject == SCOPE_PATH:
        return (0, subject)
    if subject.startswith("isms/risks/"):
        return (1, subject)
    if subject.startswith("isms/soa."):
        return (2, subject)
    return (3, subject)


def _document_errors(inst: _Instance) -> Step | None:
    errors = [f for f in inst.findings if f.level == "error" and f.subject.startswith("isms/")]
    if not errors:
        return None
    first = min(errors, key=lambda f: _document_order(f.subject))
    return Step(f"{first.subject}: {first.message}.", "A document that claims more than it can back is worse than a missing one.", f"edit {first.subject}")


def _unfinished(inst: _Instance) -> Step | None:
    todo = [f for f in inst.findings if f.level == "warning" and f.message.startswith("unfinished:")]
    if not todo:
        return None
    first = min(todo, key=lambda f: _document_order(f.subject))
    more = f" ({len(todo) - 1} more documents also unfinished)" if len(todo) > 1 else ""
    return Step(
        f"{first.subject} has {first.message.removeprefix('unfinished: ')} left{more}.",
        "Each TODO is a question only your organisation can answer.",
        f"edit {first.subject}, then make next",
    )


def _controls(inst: _Instance) -> Step | None:
    if inst.controls:
        return None
    why = inst.config_error or "no controls defined"
    return Step(
        "No controls defined.",
        f"Controls make a policy statement checkable ({why}).",
        "add config/controls/*.yaml (see ENGINE.md), then make list",
    )


def _evidence(inst: _Instance) -> Step | None:
    control_ids = {control.id for control in inst.controls}
    evidence = [f for f in inst.findings if f.subject in control_ids]
    if not evidence:
        return None
    errors = [f for f in evidence if f.level == "error"]
    if errors:
        first = errors[0]
        return Step(f"{first.subject}: {first.message}.", "Failing or tampered evidence is a finding in its own right.", "make verify, then fix the cause and make collect")
    first = evidence[0]
    return Step(f"{first.subject}: {first.message}.", "Evidence has to be collected, and kept current.", "make collect")


def _remaining(inst: _Instance) -> Step | None:
    warnings = [f for f in inst.findings if f.level == "warning"]
    if not warnings:
        return None
    first = warnings[0]
    return Step(f"{first.subject}: {first.message}.", "Left alone, this becomes a gap.", "make status")


def _ready(inst: _Instance) -> Step | None:
    drafts = [f for f in inst.findings if f.level == "note"]
    if not drafts:
        return None
    first = drafts[0]
    return Step(f"{first.subject}: {first.message}.", "Only a named human approves a document.", f"review {first.subject}, then set status and approved_by")


CHECKS: tuple[Check, ...] = (
    _framework,
    _scope,
    _risks,
    _soa,
    _policies,
    _document_errors,
    _unfinished,
    _controls,
    _evidence,
    _remaining,
    _ready,
)


def _load(target: Path, config_dir: Path | None, evidence_dir: Path | None, today: date) -> _Instance:
    config_path = config_dir or target / "config"
    evidence_root = evidence_dir or target / "evidence"
    controls: list[Any] = []
    config_error = None
    try:
        controls = list(load_project(config_path).controls)
    except ConfigError as exc:
        config_error = str(exc)
    _, findings = check_documents(target, {control.id for control in controls}, today)
    findings = findings + check_evidence(evidence_root, controls, today)
    return _Instance(target, today, controls, config_error, evidence_root, findings)


def next_step(
    target: Path,
    *,
    config_dir: Path | None = None,
    evidence_dir: Path | None = None,
    today: date | None = None,
) -> Step | None:
    """The first unmet step, or ``None`` when nothing is outstanding."""
    instance = _load(target, config_dir, evidence_dir, today or date.today())
    for check in CHECKS:
        step = check(instance)
        if step is not None:
            return step
    return None


def run(
    target: Path,
    *,
    config_dir: Path | None = None,
    evidence_dir: Path | None = None,
    as_of: str | None = None,
    out: TextIO | None = None,
) -> int:
    out = out or sys.stdout
    target = Path(target)
    if not target.is_dir():
        raise CompliatorError(f"target is not a directory: {target}")
    try:
        today = date.fromisoformat(as_of) if as_of else date.today()
    except ValueError as exc:
        raise CompliatorError(f"--as-of is not a date (YYYY-MM-DD): {exc}") from exc

    step = next_step(target, config_dir=config_dir, evidence_dir=evidence_dir, today=today)
    if step is None:
        print("Nothing outstanding. Keep evidence current (`make collect`) and reviews on cadence.", file=out)
        return 0
    print(f"Next: {step.what}", file=out)
    print(f"  Why: {step.why}", file=out)
    print(f"  Do:  {step.do}", file=out)
    print(file=out)
    print("`make status` shows everything outstanding.", file=out)
    return 0
