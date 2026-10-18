"""CLI entry point: ``python -m compliator <command>``.

The package is imported from ``src/`` rather than installed, so from a checkout
run it as ``PYTHONPATH=src python3 -m compliator <command>``.

Commands:
    collect   run the collection engine over configured controls
    verify    re-verify hashes of an evidence record (or a whole evidence root)
    list      list configured controls and their checks
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import load_project
from .engine import collect
from .errors import CompliatorError
from .verify import verify_all, verify_record


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="compliator", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_collect = sub.add_parser("collect", help="run evidence collection")
    p_collect.add_argument("--config-dir", default="config", help="config directory (default: config)")
    p_collect.add_argument("--evidence-dir", default=None, help="evidence output root (default: <project>/evidence)")
    p_collect.add_argument(
        "--control", action="append", default=None, metavar="ID",
        help="collect only this control id (repeatable)",
    )
    p_collect.add_argument("--as-of", default=None, metavar="YYYY-MM-DD", help="date to evaluate age-based checks against")
    p_collect.add_argument(
        "--simulate-failure", default=None, metavar="SOURCE_OR_PLUGIN",
        help="force a collector failure for a source (demo of the fail-loud path)",
    )

    p_verify = sub.add_parser("verify", help="verify evidence record hashes")
    p_verify.add_argument("path", nargs="?", default="evidence", help="record dir or evidence root (default: evidence)")

    p_list = sub.add_parser("list", help="list configured controls")
    p_list.add_argument("--config-dir", default="config")

    return parser


def _cmd_collect(args: argparse.Namespace) -> int:
    project = load_project(args.config_dir)
    evidence_root = Path(args.evidence_dir).resolve() if args.evidence_dir else None
    return collect(
        project,
        control_ids=args.control,
        as_of=args.as_of,
        simulate_failure=args.simulate_failure,
        evidence_root=evidence_root,
    )


def _print_warnings(report: dict[str, object]) -> None:
    for warning in report.get("warnings", []):  # type: ignore[union-attr]
        print(f"    warning: {warning}")


def _cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if (path / "MANIFEST.json").is_file():
        report = verify_record(path)
        print(f"OK  {report['control_id']}  result={report['result']}  {report['record']}")
        print(f"    verified files: {', '.join(report['files_verified'])}")  # type: ignore[arg-type]
        _print_warnings(report)
        return 0
    reports = verify_all(path)
    for report in reports:
        print(f"OK  {report['control_id']}  result={report['result']}  {report['record']}")
        _print_warnings(report)
    print(f"{len(reports)} record(s) verified.")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    project = load_project(args.config_dir)
    for control in project.controls:
        frameworks = ", ".join(f"{k}:{v}" for k, v in control.frameworks.items())
        print(f"{control.id}  source={control.source}  frequency={control.frequency_days}d")
        print(f"  {control.title}")
        print(f"  frameworks: {frameworks}")
        for check in control.checks:
            pop = f" over {check.population.path}" if check.population else ""
            print(f"    - [{check.must.op}]{pop} {check.description}")
        print()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "collect":
            return _cmd_collect(args)
        if args.command == "verify":
            return _cmd_verify(args)
        if args.command == "list":
            return _cmd_list(args)
    except CompliatorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
