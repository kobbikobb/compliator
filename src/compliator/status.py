"""Is the instance in the state it claims to be in?

``compliator init`` answers "are we set up?" by counting files. This answers the
harder question: is what exists still true? Three things, in order:

1. **Are the documents finished?** Unfilled ``TODO``s, missing owners, a status
   that outruns its evidence (``approved`` with no ``approved_by``), and reviews
   that are overdue against their own stated cadence.
2. **Do the links hold?** A policy that cites a control id no control defines is
   a broken trace, and the trace is the point.
3. **Is the evidence current and intact?** Per control: a record at all, its
   verdict, its age against the declared frequency, and a full re-verification of
   the latest record's hashes.

It is **read-only**: it writes nothing, fixes nothing, and takes no option that
could change an instance. Exit code 1 means findings, so it can gate CI — with
the caveat that a warning is a judgement call, and drafts are normal in a young
instance.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path
from typing import Any, TextIO

import yaml

from .config import load_project
from .errors import CompliatorError, ConfigError, VerificationError
from .frameworks import declared_frameworks
from .requirements import Catalog
from .verify import verify_record

# Statuses a document may carry, and the cadences front matter may declare.
DOCUMENT_STATUSES = ("draft", "approved", "retired")
RISK_STATUSES = ("open", "treated", "accepted", "closed")
CADENCE_DAYS = {"annual": 365, "semiannual": 182, "quarterly": 91}
REQUIRED_KEYS = ("id", "title", "owner", "status")

# Files under isms/ that are not controlled documents.
NOT_A_DOCUMENT = ("README.md",)

# `isms/frameworks.md` is a plain note - it records a choice, it is not a document
# anyone approves, and the repository's own copy has no front matter either.
NOT_A_DOCUMENT_PATHS = ("isms/frameworks.md",)

# A TODO or CONFIRM *marker*, not the word: the templates talk about their own TODO markers
# in prose, and counting those would report work that does not exist. Generated
# markers are either a line beginning with TODO, or the first cell of a table row.
TODO_MARKER = re.compile(r"^\s*(?:\|\s*)?(?:\d+\.\s*)?(?:TODO|CONFIRM)\b", re.MULTILINE)


@dataclass(frozen=True)
class Finding:
    """Something a reader should act on. ``level`` is error, warning or note."""

    level: str
    subject: str
    message: str
    kind: str = ""  # "unfinished", "ready" or "evidence"; empty for the rest
    count: int = 0  # for "unfinished": the TODOs left


@dataclass
class Document:
    path: str
    front: dict[str, Any]
    todos: int = 0
    broken: str | None = None


def _parse(path: Path) -> tuple[dict[str, Any] | None, str, str | None]:
    """(front matter, body, problem). A problem is why the front matter is unusable."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, text, "no front matter block"
    _, _, rest = text.partition("---\n")
    block, sep, body = rest.partition("---\n")
    if not sep:
        return None, text, "front matter block is not closed"
    try:
        front = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        return None, body, f"front matter is not valid YAML: {exc}"
    if not isinstance(front, dict):
        return None, body, "front matter is not a mapping"
    return front, body, None


def _count_todos(body: str) -> int:
    return len(TODO_MARKER.findall(body))


def _documents(instance: Path) -> list[Document]:
    isms = instance / "isms"
    if not isms.is_dir():
        return []
    documents: list[Document] = []
    for path in sorted(isms.rglob("*.md")):
        relative = str(path.relative_to(instance))
        if path.name in NOT_A_DOCUMENT or relative in NOT_A_DOCUMENT_PATHS:
            continue
        front, body, problem = _parse(path)
        documents.append(
            Document(
                path=relative,
                front=front or {},
                todos=_count_todos(body),
                broken=problem,
            )
        )
    return documents


def _cadence_days(front: dict[str, Any], subject: str) -> tuple[int | None, list[Finding]]:
    cadence = front.get("review_cadence")
    if cadence is None:
        return None, []
    if not isinstance(cadence, str) or cadence not in CADENCE_DAYS:
        known = ", ".join(sorted(CADENCE_DAYS))
        return None, [Finding("warning", subject, f"review_cadence {cadence!r} is not one of: {known}")]
    return CADENCE_DAYS[cadence], []


def _presence_findings(instance: Path) -> list[Finding]:
    """A document set can be complete file-by-file and still be missing its point."""
    findings: list[Finding] = []
    if not (instance / "isms" / "scope.md").is_file():
        findings.append(Finding("warning", "isms/scope.md", "no scope statement - nothing says what is covered"))
    if not list((instance / "isms" / "policies").glob("POL-*.md")):
        findings.append(Finding("warning", "isms/policies/", "no policies yet - templates only"))
    if not list((instance / "isms" / "risks").glob("RISK-*.md")):
        findings.append(
            Finding("warning", "isms/risks/", "no risks recorded - for a real organisation an empty register is the finding")
        )
    return findings


def check_documents(instance: Path, control_ids: set[str], today: date) -> tuple[list[Document], list[Finding]]:
    """Review every document under isms/ for finish, honesty and broken links."""
    findings: list[Finding] = _presence_findings(instance)
    documents = _documents(instance)

    for document in documents:
        subject = document.path
        if document.broken:
            findings.append(Finding("error", subject, document.broken))
            continue

        for key in REQUIRED_KEYS:
            if key not in document.front:
                findings.append(Finding("error", subject, f"front matter is missing `{key}`"))
        # Present but empty only: an absent `owner` is already reported by the
        # loop above, and one defect must produce exactly one finding.
        if "owner" in document.front and not document.front.get("owner"):
            findings.append(Finding("error", subject, "no owner - an unattributed document is not evidence"))
        title = document.front.get("title")
        if title is not None and not str(title).strip():
            findings.append(Finding("error", subject, "empty title"))

        status = document.front.get("status")
        is_risk = str(subject).startswith("isms/risks/")
        allowed = RISK_STATUSES if is_risk else DOCUMENT_STATUSES
        if status is not None and status not in allowed:
            findings.append(Finding("warning", subject, f"status {status!r} is not one of: {', '.join(allowed)}"))
        if status == "approved" and not document.front.get("approved_by"):
            findings.append(
                Finding("error", subject, "status is 'approved' with no `approved_by` - a claim with nobody behind it")
            )
        if status != "approved" and document.front.get("approved_by"):
            findings.append(Finding("warning", subject, "`approved_by` is set but the status is not 'approved'"))

        if document.todos:
            if status == "approved":
                findings.append(
                    Finding("error", subject, f"approved with {document.todos} TODO left - unfinished work presented as done")
                )
            else:
                findings.append(Finding("warning", subject, f"unfinished: {document.todos} to finish (TODO or CONFIRM)", "unfinished", document.todos))
        elif status == "draft":
            findings.append(Finding("note", subject, "draft, no TODOs left - ready for someone to approve", "ready"))

        days, cadence_findings = _cadence_days(document.front, subject)
        findings.extend(cadence_findings)
        reviewed = document.front.get("last_reviewed")
        if reviewed in (None, ""):
            if status == "approved":
                findings.append(Finding("warning", subject, "approved but no `last_reviewed` - nobody recorded a review"))
        elif days is not None:
            when: date | None = None
            if isinstance(reviewed, datetime):
                when = reviewed.date()
            elif isinstance(reviewed, date):
                when = reviewed
            else:
                try:
                    when = date.fromisoformat(str(reviewed))
                except ValueError:
                    # A date with a time is still a date. YAML only turns one into
                    # a datetime when it is unquoted, so this path catches the
                    # quoted spelling too, rather than erroring on a formatting
                    # difference the author cannot see.
                    try:
                        when = datetime.fromisoformat(str(reviewed)).date()
                    except ValueError:
                        findings.append(Finding("error", subject, f"`last_reviewed` is not a date: {reviewed!r}"))
            if when is not None:
                age = (today - when).days
                if age < 0:
                    findings.append(Finding("warning", subject, f"`last_reviewed` is in the future ({when.isoformat()})"))
                elif age > days:
                    findings.append(
                        Finding("warning", subject, f"review overdue: last reviewed {when.isoformat()}, cadence is {age - days}d past due")
                    )

        for reference in document.front.get("controls") or []:
            if str(reference) not in control_ids:
                findings.append(Finding("error", subject, f"cites control `{reference}`, which no control defines"))

    return documents, findings


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def check_evidence(
    evidence_root: Path,
    controls: list[Any],
    today: date,
) -> list[Finding]:
    """Per control: a record, its verdict, its age, and its hashes."""
    findings: list[Finding] = []
    for control in controls:
        subject = control.id
        control_dir = evidence_root / control.id
        latest_path = control_dir / "LATEST.json"
        if not latest_path.is_file():
            findings.append(Finding("warning", subject, "no evidence collected yet"))
            continue
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("error", subject, f"LATEST.json is unreadable: {exc}"))
            continue
        if not isinstance(latest, dict):
            findings.append(Finding("error", subject, "LATEST.json is not an object"))
            continue

        result = latest.get("result")
        if result != "pass":
            findings.append(Finding("error", subject, f"latest record result is {result!r}"))
        collection = latest.get("collection_id")
        record_dir = control_dir / str(collection)
        if collection and record_dir.is_dir():
            try:
                verified = verify_record(record_dir)
            except VerificationError as exc:
                findings.append(Finding("error", subject, f"latest record fails verification: {exc}"))
            else:
                # `result` above comes from LATEST.json, which is outside the
                # hashed record and can be rewritten by anyone with write access.
                # The record is the thing the hashes cover, so it gets the last
                # word: a pointer saying "pass" over a record saying otherwise is
                # exactly the edit this tool exists to catch.
                if verified.get("result") != result:
                    findings.append(
                        Finding("error", subject, f"LATEST.json says {result!r} but the record says {verified.get('result')!r}")
                    )
        else:
            findings.append(Finding("warning", subject, "LATEST.json points at a record that is not there"))

        collected = _parse_timestamp(latest.get("collected_at"))
        if collected is None:
            findings.append(Finding("warning", subject, "LATEST.json has no readable `collected_at`"))
            continue
        age = (today - collected.date()).days
        if age > control.frequency_days:
            findings.append(
                Finding("warning", subject, f"evidence is {age}d old, collected every {control.frequency_days}d")
            )
    return [replace(finding, kind="evidence") for finding in findings]


def check_coverage(instance: Path, controls: list[Any], catalogs: dict[str, Catalog]) -> list[Finding]:
    """Requirements of a declared framework that no control maps to.

    Only a catalog marked complete can show a gap; a partial one cannot say
    what is missing from the framework.
    """
    covered = {(key, rid) for control in controls for key, ids in control.mappings.items() for rid in ids}
    findings = []
    for framework in declared_frameworks(instance):
        catalog = catalogs.get(framework.key)
        if catalog is None or not catalog.complete:
            continue
        for rid, summary in catalog.requirements.items():
            if (framework.key, rid) not in covered:
                findings.append(
                    Finding("warning", f"{framework.key}:{rid}", f"no control maps to this requirement ({summary})", "coverage")
                )
    return findings


LEVEL_ORDER = {"error": 0, "warning": 1, "note": 2}


def _print_report(
    instance: Path,
    documents: list[Document],
    findings: list[Finding],
    out: TextIO,
    note: str | None,
) -> None:
    print(f"Instance: {instance}", file=out)
    print(file=out)
    print(f"Documents ({len(documents)})", file=out)
    if not documents:
        print("  none under isms/ - run `compliator init`", file=out)
    for document in documents:
        status = document.front.get("status", "?" if document.broken else "-")
        todo = f"{document.todos} TODO" if document.todos else ""
        owner = document.front.get("owner", "")
        print(f"  {str(status):<9} {document.path:<46} {todo:<9} {owner}", file=out)
    if note:
        print(file=out)
        print(note, file=out)

    print(file=out)
    if findings:
        print("Findings", file=out)
        for finding in sorted(findings, key=lambda item: (LEVEL_ORDER.get(item.level, 9), item.subject)):
            print(f"  {finding.level:<8} {finding.subject:<46} {finding.message}", file=out)
    else:
        print("No findings.", file=out)

    counts = {level: sum(1 for finding in findings if finding.level == level) for level in LEVEL_ORDER}
    print(file=out)
    print(
        f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['note']} note(s)",
        file=out,
    )


def run(
    target: Path,
    *,
    config_dir: Path | None = None,
    evidence_dir: Path | None = None,
    as_of: str | None = None,
    out: TextIO | None = None,
) -> int:
    """Report on the documents and the evidence. Read-only. 0 clean, 1 findings, 2 refused."""
    out = out or sys.stdout
    target = Path(target)
    if not target.exists():
        raise CompliatorError(f"target does not exist: {target}")
    if not target.is_dir():
        raise CompliatorError(f"target is not a directory: {target}")

    try:
        today = date.fromisoformat(as_of) if as_of else date.today()
    except ValueError as exc:
        raise CompliatorError(f"--as-of is not a date (YYYY-MM-DD): {exc}") from exc
    config_path = Path(config_dir) if config_dir else target / "config"
    evidence_root = Path(evidence_dir) if evidence_dir else target / "evidence"

    controls: list[Any] = []
    catalogs: dict[str, Catalog] = {}
    note = None
    config_finding: Finding | None = None
    try:
        project = load_project(config_path)
    except ConfigError as exc:
        # A documents-only instance is legitimate - README says you only need one
        # half to start - so a *missing* config is a warning. A config that is
        # there and will not load is broken, and an explicitly requested one that
        # is not there is a typo. Neither may be quiet, because when this fails
        # the evidence half goes unexamined: a skipped half reported as "no
        # findings" would be the exact false assurance this tool exists to
        # prevent, so it is a finding at its own level, and never a header note.
        level = "error" if config_path.exists() or config_dir is not None else "warning"
        config_finding = Finding(
            level,
            "config",
            f"no control configuration at {config_path} ({exc}) - the evidence half was not checked",
        )
        note = f"No control configuration at {config_path} ({exc}). Only the documents were checked."
    else:
        controls = list(project.controls)
        catalogs = project.catalogs

    findings: list[Finding] = []
    documents, document_findings = check_documents(target, {control.id for control in controls}, today)
    findings.extend(document_findings)
    findings.extend(check_evidence(evidence_root, controls, today))
    findings.extend(check_coverage(target, controls, catalogs))
    if config_finding is not None:
        findings.append(config_finding)

    _print_report(target, documents, findings, out, note)
    return 1 if any(finding.level in ("error", "warning") for finding in findings) else 0
