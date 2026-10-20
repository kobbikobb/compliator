"""Reading and updating the framework declaration in ``isms/frameworks.md``."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from .catalog import FRAMEWORKS, FRAMEWORKS_PATH, Framework

TABLE_HEADER = "| Framework | Statement of applicability | Notes |"
NO_FRAMEWORK_ROW = "| — | — | none declared yet |"


def framework_row(framework: Framework) -> str:
    soa = framework.soa_path if framework.requires_soa else "not required"
    return f"| {framework.title} | {soa} | {framework.note} |"


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


def declare_in_notes(target: Path, frameworks: Sequence[Framework], dry_run: bool) -> bool:
    """Append rows for unrecorded frameworks; existing content is kept."""
    path = target / FRAMEWORKS_PATH
    recorded = {framework.key for framework in declared_frameworks(target)}
    new_rows = [framework_row(f) for f in frameworks if f.key not in recorded]
    if not new_rows:
        return False
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip() != NO_FRAMEWORK_ROW]
    header = next((i for i, line in enumerate(lines) if line.startswith("| Framework |")), None)
    if header is None:
        lines += ["", "## Declared", "", TABLE_HEADER, "| --- | --- | --- |", *new_rows]
    else:
        end = header + 1
        while end < len(lines) and lines[end].startswith("|"):
            end += 1
        lines[end:end] = new_rows
    if not dry_run:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  {'would update' if dry_run else 'updated'}    {FRAMEWORKS_PATH}  (+{len(new_rows)} framework row(s))")
    return True
