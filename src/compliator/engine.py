"""The runner: ONE engine, N control configs.

Flow per control:
    freshness check -> pull raw facts via plugin -> evaluate declarative
    checks -> package evidence record (trust boundary) -> record outcome

Fail-loud contract (the design requirement this POC exists to prove):

  * A source that cannot be reached, or returns an unexpected shape, is a
    collection ERROR - printed loudly, reflected in the exit code (2), and
    it writes NO evidence record. It never degrades into empty or stale
    evidence.
  * A control whose checks evaluate to non-passing is a legitimate FAIL -
    that is findings-grade evidence and it records as such (exit 1).
  * An empty population is an ERROR, not a pass (see evaluate.py).
  * Every outcome is annotated with the age of the last good evidence, so a
    stale record can never be mistaken for a fresh one.
"""

from __future__ import annotations

import json
import sys
import traceback
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import TextIO

from . import __version__
from .config import Control, Project
from .errors import CompliatorError, EmptyPopulationError, PluginError
from .evaluate import evaluate_check
from .packager import write_record
from .plugins import get_plugin

BANNER = "!" * 68


@dataclass
class ControlOutcome:
    control: Control
    status: str  # "pass" | "fail" | "error"
    checks_passed: int = 0
    checks_total: int = 0
    record_dir: Path | None = None
    error: str | None = None
    last_good: str | None = None
    last_good_age_days: int | None = None


def _read_latest(
    evidence_root: Path, control: Control
) -> tuple[datetime | None, str | None, str | None]:
    """Return (collected_at, iso_string, result) from LATEST.json, or (None, None, None)."""
    latest_path = evidence_root / control.id / "LATEST.json"
    if not latest_path.is_file():
        return None, None, None
    try:
        data = json.loads(latest_path.read_text(encoding="utf-8"))
        ts = datetime.fromisoformat(str(data["collected_at"]).replace("Z", "+00:00"))
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return None, None, None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts, str(data.get("collected_at")), str(data.get("result"))


def _stale_warning(out: TextIO, control: Control, age_days: int) -> None:
    print(
        f"STALE EVIDENCE: control {control.id} last passed/failed collection "
        f"{age_days}d ago (frequency {control.frequency_days}d). "
        f"Evidence is older than its declared collection cadence.",
        file=out,
    )


def _loud_failure(
    err: TextIO,
    control: Control,
    source_name: str,
    plugin_name: str,
    reason: str,
    last_good_iso: str | None,
    last_good_age_days: int | None,
) -> None:
    print(BANNER, file=err)
    print("!! COLLECTION FAILED", file=err)
    print(f"!! control : {control.id} ({control.title})", file=err)
    print(f"!! source  : {source_name} (plugin {plugin_name})", file=err)
    print(f"!! reason  : {reason}", file=err)
    if last_good_iso:
        stale_note = (
            f"  -> EXCEEDS frequency ({control.frequency_days}d): STALE"
            if last_good_age_days is not None and last_good_age_days > control.frequency_days
            else ""
        )
        print(
            f"!! last good evidence: {last_good_iso} ({last_good_age_days}d old){stale_note}",
            file=err,
        )
    else:
        print("!! last good evidence: NONE - this control has never collected", file=err)
    print("!! NO evidence record was written for this run.", file=err)
    print(BANNER, file=err)


def collect(
    project: Project,
    control_ids: list[str] | None = None,
    as_of: str | None = None,
    simulate_failure: str | None = None,
    evidence_root: Path | None = None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    """Run collection. Returns process exit code: 0 ok, 1 failures, 2 errors."""
    as_of_str = as_of or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    as_of_date = date.fromisoformat(as_of_str)
    evidence_root = evidence_root or (project.root / "evidence")

    controls = project.controls
    if control_ids:
        wanted = set(control_ids)
        controls = [c for c in controls if c.id in wanted]
        missing = wanted - {c.id for c in controls}
        if missing:
            print(f"error: unknown control(s): {', '.join(sorted(missing))}", file=err)
            return 2

    print(
        f"compliator {__version__} - collecting {len(controls)} control(s), as_of {as_of_str}",
        file=out,
    )
    print(file=out)

    stale_at_start: list[tuple[Control, int]] = []
    for control in controls:
        ts, _iso, _ = _read_latest(evidence_root, control)
        if ts is not None:
            age = (datetime.now(timezone.utc) - ts).days
            if age > control.frequency_days:
                stale_at_start.append((control, age))
    for control, age in stale_at_start:
        _stale_warning(err, control, age)
    if stale_at_start:
        print(file=err)

    outcomes: list[ControlOutcome] = []
    for control in controls:
        outcome = ControlOutcome(control=control, status="error")
        source_def = project.sources[control.source]
        last_ts, last_iso, _ = _read_latest(evidence_root, control)
        if last_ts is not None:
            outcome.last_good = last_iso
            outcome.last_good_age_days = (datetime.now(timezone.utc) - last_ts).days

        try:
            plugin = get_plugin(source_def.plugin)
            if simulate_failure and (
                simulate_failure in ("all", control.source, source_def.plugin)
            ):
                raise PluginError(
                    f"simulated failure for source '{control.source}' "
                    f"(requested via --simulate-failure)"
                )
            raw, provenance = plugin.pull(source_def.options, project.root)
            check_results = [evaluate_check(raw, check, as_of_date) for check in control.checks]
        except (PluginError, EmptyPopulationError) as exc:
            outcome.error = str(exc)
            _loud_failure(
                err,
                control,
                control.source,
                source_def.plugin,
                str(exc),
                outcome.last_good,
                outcome.last_good_age_days,
            )
            outcomes.append(outcome)
            continue
        except CompliatorError as exc:
            outcome.error = f"evaluation error: {exc}"
            _loud_failure(
                err,
                control,
                control.source,
                source_def.plugin,
                str(exc),
                outcome.last_good,
                outcome.last_good_age_days,
            )
            outcomes.append(outcome)
            continue
        except Exception as exc:  # unexpected - still loud, still no empty evidence
            outcome.error = f"unexpected error: {exc}"
            print(BANNER, file=err)
            print(f"!! COLLECTION FAILED (unexpected): {control.id}: {exc}", file=err)
            print(BANNER, file=err)
            traceback.print_exc(file=err)
            outcomes.append(outcome)
            continue

        record_dir, result = write_record(
            evidence_root=evidence_root,
            control=control,
            source_name=control.source,
            plugin_name=source_def.plugin,
            provenance=provenance,
            raw=raw,
            check_results=check_results,
            as_of=as_of_str,
        )
        outcome.status = result
        outcome.checks_total = len(check_results)
        outcome.checks_passed = sum(1 for r in check_results if r.passed)
        outcome.record_dir = record_dir
        outcomes.append(outcome)

        for result_ in check_results:
            mark = "PASS" if result_.passed else "FAIL"
            print(f"  [{mark}] {control.id}: {result_.description}", file=out)
            if not result_.passed:
                print(f"         observed: {result_.observed!r}", file=out)
                if result_.detail:
                    print(f"         detail  : {result_.detail}", file=out)
        if not all(r.passed for r in check_results):
            print(
                f"  -> control {control.id} FAILED: "
                f"{outcome.checks_passed}/{outcome.checks_total} checks passed",
                file=out,
            )
        print(file=out)

    print("=" * 68, file=out)
    print(f"{'control':<18}{'result':<8}{'checks':<10}evidence", file=out)
    print("-" * 68, file=out)
    for outcome in outcomes:
        checks = f"{outcome.checks_passed}/{outcome.checks_total}" if outcome.checks_total else "-"
        if outcome.record_dir is None:
            evidence = "(none written)"
        else:
            try:
                evidence = str(outcome.record_dir.relative_to(project.root))
            except ValueError:
                evidence = str(outcome.record_dir)
        print(
            f"{outcome.control.id:<18}{outcome.status.upper():<8}{checks:<10}{evidence}", file=out
        )
    print("=" * 68, file=out)

    errors = sum(1 for o in outcomes if o.status == "error")
    failures = sum(1 for o in outcomes if o.status == "fail")
    if errors:
        print(
            f"{errors} collection error(s) - NO evidence recorded for those controls. "
            f"Last-good ages are shown above; treat as stale until fixed.",
            file=err,
        )
    if failures:
        print(f"{failures} control(s) failed their checks - review evidence records.", file=err)

    if errors:
        return 2
    if failures:
        return 1
    print("All controls collected and passing.", file=out)
    return 0
