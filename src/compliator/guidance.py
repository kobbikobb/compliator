"""The first unmet step in the order an ISMS is built; read-only, exit 0.

Findings come from the same checks `status` uses.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Optional, TextIO

from .catalog import POLICIES, RISK_PATH, SCOPE_PATH, SUGGESTED_START
from .config import load_project
from .errors import CompliatorError, ConfigError
from .frameworks import declared_frameworks
from .status import Finding, check_coverage, check_documents, check_evidence


@dataclass(frozen=True)
class Step:
    what: str
    why: str
    action: str


@dataclass
class _Snapshot:
    target: Path
    controls: list[Any]
    config_error: str | None
    findings: list[Finding]


Check = Callable[[_Snapshot], Optional[Step]]


def _framework(inst: _Snapshot) -> Step | None:
    if declared_frameworks(inst.target):
        return None
    return Step(
        "No framework declared.",
        "It decides whether you write a statement of applicability. You can change it later.",
        "make framework   (or: make framework FRAMEWORK=iso_27001_2022|soc2|both)",
    )


def _scope(inst: _Snapshot) -> Step | None:
    if (inst.target / SCOPE_PATH).is_file():
        return None
    return Step("No scope statement.", "Nothing says what the ISMS covers, so nothing can be judged complete.", "make init")


def _risks(inst: _Snapshot) -> Step | None:
    if list((inst.target / "isms" / "risks").glob("RISK-*.md")):
        return None
    return Step(
        "No risks recorded.",
        "Risks decide which requirements apply and which policies you need.",
        "make init   (then describe what could go wrong)",
    )


def _soa(inst: _Snapshot) -> Step | None:
    for framework in declared_frameworks(inst.target):
        if framework.soa_path and not (inst.target / framework.soa_path).is_file():
            return Step(
                f"No statement of applicability for {framework.title}.",
                "It records which requirements apply, why, and what covers them.",
                f"make framework FRAMEWORK={framework.key}",
            )
    return None


def _foundation_policies(inst: _Snapshot) -> Step | None:
    existing = {path.name.split("-", 2)[1] for path in (inst.target / "isms" / "policies").glob("POL-*.md")}
    missing = [number for number in (1, 2) if f"{number:03d}" not in existing]
    if not missing:
        return None
    return Step(
        "Information security and risk management policies not written: "
        + ", ".join(f"POL-{number:03d}" for number in missing) + ".",
        "They set the commitment and the method the risk assessment follows.",
        "make init",
    )


def _policies(inst: _Snapshot) -> Step | None:
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


def _document_errors(inst: _Snapshot) -> Step | None:
    errors = [f for f in inst.findings if f.level == "error" and f.kind != "evidence"]
    if not errors:
        return None
    first = min(errors, key=lambda f: _document_order(f.subject))
    return Step(f"{first.subject}: {first.message}.", "A document that claims more than it can back is not evidence.", f"edit {first.subject}")


def _unfinished(inst: _Snapshot) -> Step | None:
    todo = [f for f in inst.findings if f.kind == "unfinished"]
    if not todo:
        return None
    first = min(todo, key=lambda f: _document_order(f.subject))
    more = f" ({len(todo) - 1} more documents also unfinished)" if len(todo) > 1 else ""
    return Step(
        f"{first.subject} has {first.count} TODO left{more}.",
        "Each TODO is a question only your organisation can answer.",
        f"edit {first.subject}, then make next",
    )


def _controls(inst: _Snapshot) -> Step | None:
    if inst.controls:
        return None
    why = inst.config_error or "no controls defined"
    return Step(
        "No controls defined.",
        f"Controls make a policy statement checkable ({why}).",
        "add config/controls/*.yaml (see ENGINE.md), then make list",
    )


def _coverage(inst: _Snapshot) -> Step | None:
    gaps = [f for f in inst.findings if f.kind == "coverage"]
    if not gaps:
        return None
    more = f" ({len(gaps) - 1} more uncovered)" if len(gaps) > 1 else ""
    return Step(
        f"{gaps[0].subject}: {gaps[0].message}{more}.",
        "A requirement marked applicable needs a control, or a documented reason it has none.",
        "add the id to `mappings` in a control under config/controls/, or write the control",
    )


def _evidence(inst: _Snapshot) -> Step | None:
    evidence = [f for f in inst.findings if f.kind == "evidence"]
    if not evidence:
        return None
    errors = [f for f in evidence if f.level == "error"]
    if errors:
        first = errors[0]
        return Step(f"{first.subject}: {first.message}.", "Failing or tampered evidence is a finding in its own right.", "make verify, then fix the cause and make collect")
    first = evidence[0]
    return Step(f"{first.subject}: {first.message}.", "Evidence has to be collected, and kept current.", "make collect")


def _remaining(inst: _Snapshot) -> Step | None:
    warnings = [f for f in inst.findings if f.level == "warning"]
    if not warnings:
        return None
    first = warnings[0]
    return Step(f"{first.subject}: {first.message}.", "Unresolved, this stays a finding in `make status`.", "make status")


def _awaiting_approval(inst: _Snapshot) -> Step | None:
    drafts = [f for f in inst.findings if f.kind == "ready"]
    if not drafts:
        return None
    first = drafts[0]
    return Step(f"{first.subject}: {first.message}.", "Only a named human approves a document.", f"review {first.subject}, then set status and approved_by")


CHECKS: tuple[Check, ...] = (
    _framework,
    _scope,
    _foundation_policies,
    _risks,
    _soa,
    _policies,
    _document_errors,
    _unfinished,
    _controls,
    _coverage,
    _evidence,
    _remaining,
    _awaiting_approval,
)


def _load(target: Path, config_dir: Path | None, evidence_dir: Path | None, today: date) -> _Snapshot:
    config_path = config_dir or target / "config"
    evidence_root = evidence_dir or target / "evidence"
    controls: list[Any] = []
    catalogs = {}
    config_error = None
    try:
        project = load_project(config_path)
        controls, catalogs = list(project.controls), project.catalogs
    except ConfigError as exc:
        config_error = str(exc)
    _, findings = check_documents(target, {control.id for control in controls}, today)
    findings = findings + check_evidence(evidence_root, controls, today) + check_coverage(target, controls, catalogs)
    return _Snapshot(target, controls, config_error, findings)


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
        print("No findings. That is not conformance: approvals, internal audit and management review are still yours to do.", file=out)
        return 0
    print(f"Next: {step.what}", file=out)
    print(f"  Why: {step.why}", file=out)
    print(f"  Do:  {step.action}", file=out)
    print(file=out)
    print("`make status` shows everything outstanding.", file=out)
    return 0
