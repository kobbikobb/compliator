"""Get a new instance from nothing to a first draft.

``compliator init`` does two things in one pass:

1. **Scan.** It looks for the documents an ISMS needs and reports which are
   missing. That report is also the answer to "are we set up yet?".
2. **Ask, once per document.** For each missing item it asks a single question
   and, if the answer is yes, writes a skeleton.

What it writes is a *skeleton*: the right location, correct front matter, the
headings a policy needs, and a ``TODO`` wherever a fact about the organisation
belongs. It never invents policy content, never overwrites a file that already
exists, and never fills ``approved_by`` or sets ``status: approved`` - a named
human approves (VISION.md, principle 5).

Interactive by default, entirely non-interactive with ``--answers FILE``, and
``--dry-run`` plans without prompting or writing.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path
from string import Template
from typing import Any, Sequence

import yaml

from .catalog import (
    ALIASES,
    FRAMEWORKS_PATH,
    FRAMEWORKS,
    POLICIES,
    RISK_PATH,
    SCOPE_PATH,
    SUGGESTED_START,
    Framework,
    Policy,
)
from .errors import OnboardingError

TEMPLATE_DIR = Path(__file__).parent / "templates"

DEFAULT_OWNER = "security@example.invalid"
DEFAULT_ORGANIZATION = "TODO"
TODO = "TODO"

ANSWERS_KEYS = frozenset(
    {"organization", "what_it_does", "owner", "frameworks", "policies", "risk_title", "create"}
)

# Items the scan knows about, as "labels" so the answers file can veto one.
CREATE_SCOPE = "scope"
CREATE_FRAMEWORKS = "frameworks"
CREATE_RISK = "risk"
CREATE_SOA = "soa"
CREATE_POLICIES = "policies"


@dataclass
class Result:
    created: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


class Ask:
    """Reads answers from the terminal, or from a script (tests, demos)."""

    def __init__(self, script: Sequence[str] | None = None) -> None:
        self._script = None if script is None else list(script)

    def _read(self, prompt: str) -> str:
        if self._script is not None:
            if not self._script:
                raise OnboardingError("scripted answers ran out")
            answer = self._script.pop(0)
            print(f"{prompt} {answer}".rstrip())
            return answer
        try:
            return input(f"{prompt} ")
        except EOFError as exc:  # pragma: no cover - depends on a real terminal
            raise OnboardingError("standard input ended; nothing further was written") from exc

    def yes(self, question: str, default: bool) -> bool:
        suffix = "[Y/n]" if default else "[y/N]"
        while True:
            raw = self._read(f"{question} {suffix}").strip().lower()
            if not raw:
                return default
            if raw in ("y", "yes"):
                return True
            if raw in ("n", "no"):
                return False
            print("  please answer y or n")

    def text(self, question: str, default: str) -> str:
        raw = self._read(f"{question} [{default}]").strip()
        return raw or default


def _load_answers(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise OnboardingError(f"answers file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise OnboardingError(f"{path}: not valid YAML: {exc}") from exc
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise OnboardingError(f"{path}: expected a mapping at the top level")
    unknown = sorted(set(data) - ANSWERS_KEYS)
    if unknown:
        known = ", ".join(sorted(ANSWERS_KEYS))
        raise OnboardingError(f"{path}: unknown key(s): {', '.join(unknown)} (known: {known})")
    return data


def _resolve_frameworks(value: Any) -> tuple[Framework, ...]:
    """Turn "iso, soc2" / ["soc2"] / "none" into registry entries, loudly."""
    if value is None:
        return (FRAMEWORKS[0],)
    raw: list[str] = []
    if isinstance(value, str):
        raw = [part for part in value.replace("+", ",").split(",") if part.strip()]
    elif isinstance(value, (list, tuple)):
        raw = [str(part) for part in value]
    else:
        raise OnboardingError(f"frameworks: expected a string or a list, got {type(value).__name__}")

    keys: list[str] = []
    for part in raw:
        needle = part.strip().lower().replace("-", "_").replace(" ", "_")
        for chunk in needle.split("_and_"):
            if not chunk:
                continue
            if chunk not in ALIASES:
                known = sorted({key for key in ALIASES if key not in ("all", "both")})
                raise OnboardingError(f"unknown framework: {part.strip()!r} (known: {', '.join(known)}, both, none)")
            for key in ALIASES[chunk]:
                if key not in keys:
                    keys.append(key)
    return tuple(next(framework for framework in FRAMEWORKS if framework.key == key) for key in keys)


FRAMEWORK_MENU = (
    ("1", "iso", "ISO/IEC 27001:2022 - requires a statement of applicability"),
    ("2", "soc2", "SOC 2 Trust Services Criteria - you choose criteria, no statement of applicability"),
    ("3", "both", "Both"),
    ("4", "none", "Decide later"),
)


def declared_frameworks(target: Path) -> tuple[Framework, ...]:
    """Frameworks with a row in frameworks.md or an SoA file."""
    notes = target / FRAMEWORKS_PATH
    text = notes.read_text(encoding="utf-8") if notes.is_file() else ""
    found = []
    for framework in FRAMEWORKS:
        in_table = re.search(rf"^\|\s*{re.escape(framework.title)}\s*\|", text, re.MULTILINE)
        has_soa = framework.soa_path is not None and (target / framework.soa_path).is_file()
        if in_table or has_soa:
            found.append(framework)
    return tuple(found)


def _ask_framework(ask: "Ask") -> tuple[Framework, ...]:
    print("Which framework are you orienting to? It decides which statement of")
    print("applicability you write; you can add another later with `make framework`.")
    for number, _, label in FRAMEWORK_MENU:
        print(f"  {number}) {label}")
    answer = ask.text("Choose 1-4", "1").strip()
    by_number = {number: alias for number, alias, _ in FRAMEWORK_MENU}
    return _resolve_frameworks(by_number.get(answer, answer))


def _resolve_policies(value: Any) -> tuple[Policy, ...]:
    """``minimal`` | ``all`` | ``none`` | ``[1, 3, 5]`` -> policies, in order."""
    by_number = {policy.number: policy for policy in POLICIES}
    if value is None:
        return tuple(by_number[number] for number in SUGGESTED_START)
    if isinstance(value, str):
        token = value.strip().lower()
        if token in ("minimal", "suggested", "start", ""):
            return tuple(by_number[number] for number in SUGGESTED_START)
        if token in ("all", "everything"):
            return POLICIES
        if token in ("none", "no"):
            return ()
        numbers = [part for part in token.replace(",", " ").split() if part]
    elif isinstance(value, (list, tuple)):
        numbers = list(value)
    else:
        raise OnboardingError(f"policies: expected a string or a list, got {type(value).__name__}")

    selected: list[Policy] = []
    for number in numbers:
        try:
            index = int(number)
        except (TypeError, ValueError) as exc:
            raise OnboardingError(f"policies: {number!r} is not a policy number") from exc
        if index not in by_number:
            valid = f"{POLICIES[0].number}-{POLICIES[-1].number}"
            raise OnboardingError(f"policies: no policy {index} (valid: {valid}, or a name)")
        selected.append(by_number[index])
    return tuple(sorted(selected, key=lambda policy: policy.number))


def _front_matter(fields: dict[str, Any]) -> str:
    """Deterministic YAML front matter. Omitted keys stay omitted - on purpose."""
    body = yaml.safe_dump(fields, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return f"---\n{body}---\n"


def _render(template_name: str, **values: Any) -> str:
    template = Template((TEMPLATE_DIR / template_name).read_text(encoding="utf-8"))
    return template.substitute(**values)


def _document(front_matter: dict[str, Any], body: str) -> str:
    text = _front_matter(front_matter) + "\n" + body
    return text if text.endswith("\n") else text + "\n"


def _scan(target: Path, frameworks: Sequence[Framework]) -> list[tuple[str, str]]:
    """(path, state) for everything an instance could hold.

    Scanning for every framework's SoA file, not just the selected ones, is
    deliberate: the report answers "what could this instance hold", so it should
    not change shape based on an answer not given yet.
    """
    paths = [SCOPE_PATH, FRAMEWORKS_PATH, RISK_PATH]
    paths += [policy.path for policy in POLICIES]
    paths += [framework.soa_path for framework in frameworks if framework.soa_path]

    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        rows.append((path, "present" if (target / path).is_file() else "missing"))
    return rows


@dataclass
class _Plan:
    organization: str
    what_it_does: str
    owner: str
    frameworks: tuple[Framework, ...]
    policies: tuple[Policy, ...]
    risk_title: str
    create: dict[str, bool]


def _plan_from_answers(answers: dict[str, Any], create_all: bool) -> _Plan:
    created = answers.get("create", {})
    if created and not isinstance(created, dict):
        raise OnboardingError("create: expected a mapping of item -> boolean")
    vetoed = {key for key, value in created.items() if value is False}
    unknown = sorted(set(created) - {CREATE_SCOPE, CREATE_FRAMEWORKS, CREATE_RISK, CREATE_SOA, CREATE_POLICIES})
    if unknown:
        known = ", ".join([CREATE_SCOPE, CREATE_FRAMEWORKS, CREATE_RISK, CREATE_SOA, CREATE_POLICIES])
        raise OnboardingError(f"create: unknown item(s): {', '.join(unknown)} (known: {known})")
    return _Plan(
        organization=str(answers.get("organization") or DEFAULT_ORGANIZATION),
        what_it_does=str(answers.get("what_it_does") or TODO),
        owner=str(answers.get("owner") or DEFAULT_OWNER),
        frameworks=_resolve_frameworks(answers.get("frameworks")),
        policies=_resolve_policies(answers.get("policies")),
        risk_title=str(answers.get("risk_title") or TODO),
        create={key: (create_all and key not in vetoed) for key in
                (CREATE_SCOPE, CREATE_FRAMEWORKS, CREATE_RISK, CREATE_SOA, CREATE_POLICIES)},
    )


def _plan_interactively(ask: Ask, pending: set[str], known: tuple[Framework, ...] | None) -> _Plan:
    """One question at a time, in the order the documents depend on each other."""
    print()
    create: dict[str, bool] = {}
    organization = DEFAULT_ORGANIZATION
    what_it_does = TODO
    owner = DEFAULT_OWNER

    create[CREATE_SCOPE] = SCOPE_PATH in pending and ask.yes(
        f"Create {SCOPE_PATH} (the scope statement)?", default=True
    )
    if create[CREATE_SCOPE]:
        organization = ask.text("  Organisation name", DEFAULT_ORGANIZATION)
        what_it_does = ask.text("  What the business does, in one line", TODO)
        owner = ask.text("  Owner (a role or an address)", DEFAULT_OWNER)

    frameworks = known if known is not None else _ask_framework(ask)
    framework_paths = {framework.soa_path for framework in frameworks if framework.soa_path}

    create[CREATE_FRAMEWORKS] = FRAMEWORKS_PATH in pending and ask.yes(
        f"Create {FRAMEWORKS_PATH} (records the choice)?", default=True
    )

    # Policies 1-2 come before the risks, which come before the SoA, which comes
    # before the rest of the policies - the dependency order README.md describes.
    policies: list[Policy] = []
    for policy in POLICIES:
        if policy.path not in pending:
            continue
        default = policy.number in SUGGESTED_START
        mark = "suggested" if default else "only if it applies to you"
        if ask.yes(f"Create {policy.path} ({mark})?", default=default):
            policies.append(policy)

    create[CREATE_RISK] = RISK_PATH in pending and ask.yes(f"Create {RISK_PATH} (the first risk)?", default=True)
    risk_title = TODO
    if create[CREATE_RISK]:
        risk_title = ask.text("  What could go wrong, in one line", TODO)

    soa_pending = bool(framework_paths & pending)
    create[CREATE_SOA] = soa_pending and ask.yes(
        f"Create the statement of applicability ({', '.join(sorted(p for p in framework_paths if p))})?", default=True
    )
    create[CREATE_POLICIES] = bool(policies)

    return _Plan(
        organization=organization,
        what_it_does=what_it_does,
        owner=owner,
        frameworks=frameworks,
        policies=tuple(policies),
        risk_title=risk_title,
        create=create,
    )


def _frameworks_line(frameworks: Sequence[Framework]) -> str:
    if not frameworks:
        return "No framework declared yet. TODO: decide which one you are orienting to (`isms/frameworks.md`)."
    names = ", ".join(framework.title for framework in frameworks)
    return f"Orienting to: {names}. Applicability decisions are in the statement of applicability."


def _framework_rows(frameworks: Sequence[Framework]) -> str:
    if not frameworks:
        return "| — | — | none declared yet |"
    rows = ["| Framework | Statement of applicability | Notes |", "| --- | --- | --- |"]
    for framework in frameworks:
        soa = framework.soa_path if framework.requires_soa else "not required"
        rows.append(f"| {framework.title} | {soa} | {framework.note} |")
    return "\n".join(rows)


def _contents(plan: _Plan, today: str) -> dict[str, str]:
    """path -> file contents, for every item this plan would write."""
    files: dict[str, str] = {}
    common = {
        "organization": plan.organization,
        "what_it_does": plan.what_it_does,
        "owner": plan.owner,
        "date": today,
    }

    if plan.create[CREATE_SCOPE]:
        files[SCOPE_PATH] = _document(
            {
                "id": "SCOPE-001",
                "title": "ISMS Scope Statement",
                "owner": plan.owner,
                "status": "draft",
                "review_cadence": "annual",
            },
            _render("scope.md", frameworks_line=_frameworks_line(plan.frameworks), **common),
        )

    if plan.create[CREATE_FRAMEWORKS]:
        files[FRAMEWORKS_PATH] = _render("frameworks.md", framework_rows=_framework_rows(plan.frameworks))

    for policy in plan.policies:
        if not plan.create[CREATE_POLICIES]:
            break
        files[policy.path] = _document(
            {
                "id": policy.id,
                "title": policy.title,
                "owner": plan.owner,
                "status": "draft",
                "review_cadence": "annual",
            },
            _render(
                "policy.md",
                id=policy.id,
                title=policy.title,
                summary=policy.summary,
                checkable=policy.checkable,
                review_cadence="annual",
                **common,
            ),
        )

    if plan.create[CREATE_RISK]:
        files[RISK_PATH] = _document(
            {
                "id": "RISK-001",
                "title": plan.risk_title,
                "owner": plan.owner,
                "status": "open",
                # Ratings and treatment are TODO: they are an assessment and a
                # decision, and a default here would read as one.
                "likelihood": TODO,
                "impact": TODO,
                "inherent": TODO,
                "residual": TODO,
                "treatment": TODO,
            },
            _render("risk.md", title=plan.risk_title, owner=plan.owner, date=today),
        )

    if plan.create[CREATE_SOA]:
        for framework in plan.frameworks:
            if not framework.soa_path:
                continue
            files[framework.soa_path] = _document(
                {
                    "id": "SOA-001",
                    "framework": framework.key,
                    "title": "Statement of Applicability",
                    "owner": plan.owner,
                    "status": "draft",
                    "review_cadence": "annual",
                },
                _render("soa.md", framework_title=framework.title, date=today),
            )
    return files


def _emit(target: Path, path: str, contents: str, dry_run: bool, result: Result) -> None:
    destination = target / path
    if destination.exists():
        print(f"  unchanged  {path}  (already exists - never overwritten)")
        result.skipped.append(path)
        return
    if dry_run:
        print(f"  would write {path}  ({len(contents.splitlines())} lines)")
        result.created.append(path)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(contents, encoding="utf-8")
    print(f"  created    {path}")
    result.created.append(path)


def _print_next_steps(result: Result, remaining: Sequence[str], required_soa: set[str]) -> None:
    print()
    if result.created:
        print(f"{len(result.created)} document(s) written as drafts.")
    if result.skipped:
        print(f"{len(result.skipped)} left alone because they already exist.")

    # A statement of applicability no declared framework asks for is not a
    # document waiting to be written - saying "not selected" about it reads as if
    # a TODO were outstanding.
    inapplicable = [path for path in remaining if path.startswith("isms/soa.") and path not in required_soa]
    left_out = [path for path in remaining if path not in inapplicable]
    if left_out:
        shown = ", ".join(left_out[:3])
        more = f" and {len(left_out) - 3} more" if len(left_out) > 3 else ""
        print(f"{len(left_out)} not created (not selected): {shown}{more}")
        print("  They are still offered next time - nothing was written for them.")
    if inapplicable:
        print("No statement of applicability: the declared framework(s) do not require one.")

    print()
    print("Next: run `make next` - it names the one thing to do now.")


def run(
    target: Path,
    *,
    answers_path: Path | None = None,
    dry_run: bool = False,
    ask: Ask | None = None,
    today: str | None = None,
    framework: str | None = None,
) -> int:
    """Scan, ask, write. Returns a process exit code (0 ok, 2 refused)."""
    if target.exists() and not target.is_dir():
        raise OnboardingError(f"target is not a directory: {target}")
    if not target.exists() and not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    # The scan is the "are we set up yet?" answer, and it is printed before any
    # question is asked - including in the case where no question is needed.
    rows = _scan(target, FRAMEWORKS)
    missing = [path for path, state in rows if state == "missing"]

    print(f"Scanning {target if str(target) else '.'}")
    for path, state in rows:
        print(f"  {state:<8} {path}")
    print()
    if not missing:
        print("Already set up: every document this scan knows about is present.")
        print("Nothing was written. `compliator verify evidence` checks the other half.")
        return 0
    print(f"{len(missing)} of {len(rows)} document(s) missing. Existing files are never overwritten.")

    answers = _load_answers(answers_path) if answers_path else None
    if framework is not None:
        known: tuple[Framework, ...] | None = _resolve_frameworks(framework)
    else:
        known = declared_frameworks(target) or None
    if answers is not None:
        if known is not None and "frameworks" not in answers:
            answers["frameworks"] = [item.key for item in known]
        plan = _plan_from_answers(answers, create_all=True)
    elif dry_run:
        plan = _plan_from_answers(
            {"frameworks": [item.key for item in known]} if known is not None else {}, create_all=True
        )
    else:
        if ask is None and not sys.stdin.isatty():
            raise OnboardingError(
                "standard input is not a terminal; pass --answers FILE for a non-interactive run, or --dry-run"
            )
        plan = _plan_interactively(ask or Ask(), set(missing), known)

    stamp = today or _date.today().isoformat()

    required_soa = {framework.soa_path for framework in plan.frameworks if framework.soa_path}
    files = _contents(plan, stamp)
    result = Result()
    wanted = set(files)
    pending = [path for path in missing if path in wanted]
    remaining = [path for path in missing if path not in wanted]

    if not pending:
        print()
        if wanted:
            print("Nothing to write: everything selected is already present.")
        else:
            print("Nothing selected, so nothing was written.")
        _print_next_steps(result, remaining, required_soa)
        return 0

    print()
    print("Writing:" if not dry_run else "Plan:")
    for path in sorted(files, key=lambda item: _order(item)):
        if path in pending:
            _emit(target, path, files[path], dry_run, result)

    _print_next_steps(result, remaining, required_soa)
    return 0


def _order(path: str) -> tuple[int, str]:
    """Creation order: scope, frameworks, policies in sequence, risk, SoA last."""
    if path == SCOPE_PATH:
        return (0, path)
    if path == FRAMEWORKS_PATH:
        return (1, path)
    for policy in POLICIES:
        if path == policy.path:
            return (10 + policy.number, path)
    if path == RISK_PATH:
        return (30, path)
    return (40, path)


NO_FRAMEWORK_ROW = "| — | — | none declared yet |"


def _declare_in_notes(target: Path, frameworks: Sequence[Framework], dry_run: bool) -> bool:
    """Append rows for unrecorded frameworks; existing content is kept."""
    path = target / FRAMEWORKS_PATH
    text = path.read_text(encoding="utf-8")
    recorded = {framework.key for framework in declared_frameworks(target)}
    new_rows = [
        f"| {f.title} | {f.soa_path if f.requires_soa else 'not required'} | {f.note} |"
        for f in frameworks
        if f.key not in recorded
    ]
    if not new_rows:
        return False
    lines = [line for line in text.splitlines() if line.strip() != NO_FRAMEWORK_ROW]
    header = next((i for i, line in enumerate(lines) if line.startswith("| Framework |")), None)
    if header is None:
        lines += ["", "## Declared", "", "| Framework | Statement of applicability | Notes |", "| --- | --- | --- |", *new_rows]
    else:
        end = header + 1
        while end < len(lines) and lines[end].startswith("|"):
            end += 1
        lines[end:end] = new_rows
    if not dry_run:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  {'would update' if dry_run else 'updated'}    {FRAMEWORKS_PATH}  (+{len(new_rows)} framework row(s))")
    return True


def run_framework(
    target: Path,
    choice: str | None = None,
    *,
    dry_run: bool = False,
    ask: Ask | None = None,
    today: str | None = None,
) -> int:
    """Declare framework(s) and write their SoA. Never overwrites."""
    if target.exists() and not target.is_dir():
        raise OnboardingError(f"target is not a directory: {target}")
    declared = declared_frameworks(target)

    if choice is None:
        if declared:
            print("Declared: " + ", ".join(item.title for item in declared))
            print("To add or change, pass FRAMEWORK=iso_27001_2022, soc2 or both.")
            return 0
        if ask is None and not sys.stdin.isatty():
            raise OnboardingError("standard input is not a terminal; pass --set iso_27001_2022|soc2|both|none")
        frameworks = _ask_framework(ask or Ask())
    else:
        frameworks = _resolve_frameworks(choice)

    plan = _Plan(
        organization=DEFAULT_ORGANIZATION,
        what_it_does=TODO,
        owner=DEFAULT_OWNER,
        frameworks=frameworks,
        policies=(),
        risk_title=TODO,
        create={
            CREATE_SCOPE: False,
            CREATE_FRAMEWORKS: True,
            CREATE_RISK: False,
            CREATE_SOA: True,
            CREATE_POLICIES: False,
        },
    )
    if not frameworks:
        print("No framework declared, so nothing was written. Run `make framework` when you have decided.")
        return 0

    files = _contents(plan, today or _date.today().isoformat())
    result = Result()
    print("Plan:" if dry_run else "Writing:")
    updated = False
    for path in sorted(files, key=_order):
        if path == FRAMEWORKS_PATH and (target / path).is_file():
            updated = _declare_in_notes(target, frameworks, dry_run)
            continue
        _emit(target, path, files[path], dry_run, result)
    if not (result.created or updated):
        print("Already declared; nothing to write.")
    print()
    print("Next: run `make next`.")
    return 0
