"""CLI entry point: ``python -m compliator <command>``.

The package is imported from ``src/`` rather than installed, so from a checkout
run it as ``PYTHONPATH=src python3 -m compliator <command>``.

Commands:
    collect   run the collection engine over configured controls
    verify    re-verify hashes of an evidence record (or a whole evidence root)
    list      list configured controls and their checks
    init      scaffold an instance's ISMS documents, one item at a time
    status    report whether the documents and the evidence are still true
    framework declare framework(s)
    new-risk  add the next risk skeleton
    next      name the next step
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import load_project
from .engine import collect
from .errors import CompliatorError
from .guidance import run as run_next
from .onboarding import run as run_init
from .onboarding import run_framework, run_new_risk
from .status import run as run_status
from .verify import verify_all, verify_record


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="compliator", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_collect = sub.add_parser("collect", help="run evidence collection")
    p_collect.add_argument(
        "--config-dir", default="config", help="config directory (default: config)"
    )
    p_collect.add_argument(
        "--evidence-dir", default=None, help="evidence output root (default: <project>/evidence)"
    )
    p_collect.add_argument(
        "--control",
        action="append",
        default=None,
        metavar="ID",
        help="collect only this control id (repeatable)",
    )
    p_collect.add_argument(
        "--as-of",
        default=None,
        metavar="YYYY-MM-DD",
        help="date to evaluate age-based checks against",
    )
    p_collect.add_argument(
        "--simulate-failure",
        default=None,
        metavar="SOURCE_OR_PLUGIN",
        help="force a collector failure for a source (demo of the fail-loud path)",
    )

    p_verify = sub.add_parser("verify", help="verify evidence record hashes")
    p_verify.add_argument(
        "path",
        nargs="?",
        default="evidence",
        help="record dir or evidence root (default: evidence)",
    )

    p_list = sub.add_parser("list", help="list configured controls")
    p_list.add_argument("--config-dir", default="config")

    p_init = sub.add_parser("init", help="scaffold the ISMS documents for an instance")
    p_init.add_argument(
        "--target", default=".", help="instance root to scan and write into (default: .)"
    )
    p_init.add_argument(
        "--answers",
        default=None,
        metavar="FILE",
        help="YAML file answering every question; runs entirely non-interactively",
    )
    p_init.add_argument(
        "--dry-run",
        action="store_true",
        help="print what would be written, ask nothing, write nothing",
    )

    p_init.add_argument(
        "--framework",
        default=None,
        metavar="NAME",
        help="iso_27001_2022, soc2, both or none; skips the framework question",
    )

    p_framework = sub.add_parser("framework", help="declare framework(s)")
    p_framework.add_argument("--target", default=".", help="instance root (default: .)")
    p_framework.add_argument(
        "--set",
        dest="choice",
        default=None,
        metavar="NAME",
        help="iso_27001_2022, soc2, both or none",
    )
    p_framework.add_argument(
        "--dry-run", action="store_true", help="print what would be written, write nothing"
    )

    p_risk = sub.add_parser("new-risk", help="add the next risk skeleton (RISK-NNN)")
    p_risk.add_argument("--target", default=".", help="instance root (default: .)")
    p_risk.add_argument(
        "--title", default=None, help="the scenario in one line; asked for if omitted"
    )
    p_risk.add_argument("--owner", default=None, help="a role or an address")
    p_risk.add_argument(
        "--dry-run", action="store_true", help="print what would be written, write nothing"
    )

    p_next = sub.add_parser("next", help="name the next step")
    p_next.add_argument("--target", default=".", help="instance root to inspect (default: .)")
    p_next.add_argument("--config-dir", default=None)
    p_next.add_argument("--evidence-dir", default=None)
    p_next.add_argument("--as-of", default=None, metavar="YYYY-MM-DD")

    p_status = sub.add_parser("status", help="report on the documents and the evidence (read-only)")
    p_status.add_argument("--target", default=".", help="instance root to inspect (default: .)")
    p_status.add_argument(
        "--config-dir", default=None, help="control config directory (default: <target>/config)"
    )
    p_status.add_argument(
        "--evidence-dir", default=None, help="evidence root (default: <target>/evidence)"
    )
    p_status.add_argument(
        "--as-of",
        default=None,
        metavar="YYYY-MM-DD",
        help="date to age reviews and evidence against",
    )

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
    warnings = report.get("warnings", [])
    for warning in warnings if isinstance(warnings, list) else []:
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
        if control.mappings:
            frameworks = "; ".join(f"{k}: {', '.join(ids)}" for k, ids in control.mappings.items())
        else:
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
        if args.command == "init":
            return run_init(
                Path(args.target),
                answers_path=Path(args.answers) if args.answers else None,
                dry_run=args.dry_run,
                framework=args.framework,
            )
        if args.command == "framework":
            return run_framework(Path(args.target), args.choice, dry_run=args.dry_run)
        if args.command == "new-risk":
            owner = {"owner": args.owner} if args.owner else {}
            return run_new_risk(Path(args.target), args.title, dry_run=args.dry_run, **owner)
        if args.command == "next":
            return run_next(
                Path(args.target),
                config_dir=Path(args.config_dir) if args.config_dir else None,
                evidence_dir=Path(args.evidence_dir) if args.evidence_dir else None,
                as_of=args.as_of,
            )
        if args.command == "status":
            return run_status(
                Path(args.target),
                config_dir=Path(args.config_dir) if args.config_dir else None,
                evidence_dir=Path(args.evidence_dir) if args.evidence_dir else None,
                as_of=args.as_of,
            )
    except CompliatorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        where = f"{exc.filename}: " if exc.filename else ""
        print(f"error: {where}{exc.strerror or exc}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as exc:
        print(f"error: file is not valid UTF-8 ({exc.reason})", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
