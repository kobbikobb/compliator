#!/usr/bin/env python3
"""Fail when a tracked file's name or content contains banned vocabulary.

The list lives in scripts/slop-words.txt; this file and that list are exempt
from the content check (they contain the words as data). Matching rules:

- case-insensitive;
- a single word matches as a prefix, so ``canonical`` also catches
  ``canonicalisation``;
- a phrase (contains a space or hyphen) matches as a substring;
- file names are checked the same way against every path component.

Runs over ``git ls-files``, so untracked scratch files and gitignored
directories (evidence/) are invisible to it by construction. Binary and
undecodable files are skipped; only their names are checked.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORDLIST = pathlib.Path(__file__).resolve().parent / "slop-words.txt"
EXEMPT_CONTENT = {WORDLIST.resolve(), pathlib.Path(__file__).resolve()}


def load_entries() -> list[str]:
    entries = []
    for line in WORDLIST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.append(line.lower())
    if not entries:
        raise SystemExit(f"no entries in {WORDLIST}")
    return entries


def content_patterns(entries: list[str]) -> list[tuple[str, re.Pattern[str]]]:
    return [(entry, re.compile(r"\b" + re.escape(entry), re.IGNORECASE)) for entry in entries]


def tracked_files() -> list[pathlib.Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return [ROOT / name for name in out.stdout.split("\0") if name]


def scan_name(path: pathlib.Path, entries: list[str]) -> list[str]:
    haystack = str(path.relative_to(ROOT)).lower()
    return [entry for entry in entries if entry in haystack]


def scan_content(path: pathlib.Path, patterns: list[tuple[str, re.Pattern[str]]]) -> list[str]:
    if path.resolve() in EXEMPT_CONTENT:
        return []
    try:
        data = path.read_bytes()
    except OSError:
        return []
    if b"\0" in data:
        return []  # binary
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return []
    hits = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for entry, pattern in patterns:
            if pattern.search(line):
                hits.append(f"{path.relative_to(ROOT)}:{lineno}: {entry!r} — {line.strip()[:100]}")
    return hits


def main() -> int:
    entries = load_entries()
    patterns = content_patterns(entries)
    failures: list[str] = []
    for path in tracked_files():
        for entry in scan_name(path, entries):
            failures.append(f"{path.relative_to(ROOT)}: file name contains {entry!r}")
        failures.extend(scan_content(path, patterns))
    if failures:
        print(f"slop vocabulary in {len(failures)} place(s):", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print(
            f"\n{len(entries)} banned entries in scripts/slop-words.txt. "
            "Rewrite the text, or argue for a list change in the pull request.",
            file=sys.stderr,
        )
        return 1
    print(f"clean: no banned vocabulary in {len(entries)}-entry list")
    return 0


if __name__ == "__main__":
    sys.exit(main())
