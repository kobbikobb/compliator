"""Assertion evaluation: declarative checks over raw facts.

This is where control logic lives - NOT in plugins. Plugins pull raw facts;
this module applies the check declared in each control's YAML config and
records what it observed alongside pass/fail, so an auditor reading the
evidence record can see the values that were tested, not just a verdict.

Supported operators (v1):

  population ops (check has a ``population``; ``must.path`` resolved per item):
    all_equal          every resolved value == value
    exists             every resolved value is present (not null)
    date_within_days   every resolved date is 0..value days before ``as_of``
    min_gte            minimum of resolved numeric values >= value
    count_gte          size of the population >= value

  scalar ops (check has no population; ``must.path`` resolved from root):
    equals             value at path == value
    gte                numeric value at path >= value
    exists             value at path is present (not null)
    count_gte          length of list at path >= value
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from .errors import CompliatorError, ConfigError, EmptyPopulationError

POPULATION_OPS = frozenset(
    {"all_equal", "exists", "date_within_days", "min_gte", "count_gte"}
)
SCALAR_OPS = frozenset({"equals", "gte", "exists", "count_gte"})
ALL_OPS = POPULATION_OPS | SCALAR_OPS
OPS_REQUIRING_VALUE = ALL_OPS - {"exists"}


def resolve_path(obj: Any, dotted: str) -> Any:
    """Resolve a dotted path of mapping keys. Returns None if absent.

    Deliberately no wildcards or list traversal: populations address lists
    explicitly, items are mappings, and paths only walk mappings. Anything
    fancier belongs in v2 alongside tests - silent partial resolution is how
    evidence ends up claiming things nobody checked.
    """
    cur = obj
    for key in dotted.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _parse_date(raw: Any, context: str) -> date | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str):
        try:
            return date.fromisoformat(raw)
        except ValueError as exc:
            raise CompliatorError(f"{context}: value {raw!r} is not YYYY-MM-DD") from exc
    raise CompliatorError(f"{context}: cannot read {raw!r} as a date")


@dataclass
class Population:
    path: str
    where: dict[str, Any] = field(default_factory=dict)


@dataclass
class Must:
    path: str
    op: str
    value: Any = None


@dataclass
class CheckResult:
    description: str
    population: Population | None
    must: Must
    population_size: int | None
    observed: Any
    passed: bool
    detail: str

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "description": self.description,
            "check": {
                "path": self.must.path,
                "op": self.must.op,
                "expected": self.must.value,
            },
            "population": None,
            "population_size": self.population_size,
            "observed": self.observed,
            "passed": self.passed,
        }
        if self.population is not None:
            out["population"] = {
                "path": self.population.path,
                "where": self.population.where,
            }
        if self.detail:
            out["detail"] = self.detail
        return out


def _resolve_population(raw: dict[str, Any], population: Population, desc: str) -> list[dict[str, Any]]:
    node = resolve_path(raw, population.path)
    if not isinstance(node, list):
        raise CompliatorError(
            f"check '{desc}': population path '{population.path}' is not a list "
            f"(got {type(node).__name__})"
        )
    items = [item for item in node if isinstance(item, dict)]
    if len(items) != len(node):
        raise CompliatorError(
            f"check '{desc}': population '{population.path}' contains non-mapping items"
        )
    for key, expected in population.where.items():
        items = [item for item in items if item.get(key) == expected]
    if not items:
        where_txt = f" where {population.where}" if population.where else ""
        raise EmptyPopulationError(
            f"check '{desc}': population '{population.path}'{where_txt} resolved to 0 items. "
            f"Refusing to pass on an empty population (completeness cannot be "
            f"evidenced, and a vacuous pass would be misleading)."
        )
    return items


def _eval_population_op(
    values: list[Any], must: Must, as_of: date, desc: str
) -> tuple[bool, Any, str]:
    op = must.op
    if op == "all_equal":
        observed = values
        bad = [v for v in values if v != must.value]
        return (not bad, observed, "" if not bad else f"{len(bad)} of {len(values)} items != {must.value!r}")
    if op == "exists":
        observed = values
        missing = [i for i, v in enumerate(values) if v is None or v == ""]
        return (
            not missing,
            observed,
            "" if not missing else f"missing/null at item index {missing}",
        )
    if op == "date_within_days":
        observed = values
        bad: list[str] = []
        for i, v in enumerate(values):
            try:
                parsed = _parse_date(v, f"check '{desc}' item {i}")
            except CompliatorError as exc:
                return False, observed, str(exc)
            if parsed is None:
                bad.append(f"item {i}: null date")
                continue
            delta = (as_of - parsed).days
            if delta < 0:
                bad.append(f"item {i}: {parsed.isoformat()} is in the future")
            elif delta > must.value:
                bad.append(f"item {i}: {parsed.isoformat()} is {delta}d old (max {must.value})")
        return (not bad, observed, "" if not bad else "; ".join(bad))
    if op == "min_gte":
        observed = values
        if any(v is None for v in values):
            return False, observed, "null values present; minimum cannot be established"
        try:
            lo = min(values)
        except TypeError:
            return False, observed, f"non-numeric values in {values!r}"
        return (lo >= must.value, observed, f"min={lo!r}")
    if op == "count_gte":
        return (len(values) >= must.value, len(values), f"count={len(values)}")
    raise ConfigError(f"unknown operator: {op}")  # pragma: no cover - validated at load


def _eval_scalar_op(
    raw: dict[str, Any], must: Must, desc: str
) -> tuple[bool, Any, str]:
    op = must.op
    resolved = resolve_path(raw, must.path)
    if op == "equals":
        return (resolved == must.value, resolved, "")
    if op == "gte":
        if resolved is None:
            return False, resolved, f"path '{must.path}' is null"
        try:
            return (resolved >= must.value, resolved, "")
        except TypeError:
            return False, resolved, f"{resolved!r} is not comparable to {must.value!r}"
    if op == "exists":
        return (resolved is not None and resolved != "", resolved, "")
    if op == "count_gte":
        if not isinstance(resolved, list):
            return False, resolved, f"path '{must.path}' is not a list"
        return (len(resolved) >= must.value, len(resolved), f"count={len(resolved)}")
    raise ConfigError(f"unknown operator: {op}")  # pragma: no cover - validated at load


def evaluate_check(raw: dict[str, Any], check: Any, as_of: date) -> CheckResult:
    """Apply one configured check to raw facts; never raises on verdict.

    Raises only for structural problems (bad population path, empty
    population, unreadable dates) - those are collection errors, not control
    failures, and the runner surfaces them loudly as such.
    """
    population = check.population
    if population is not None:
        items = _resolve_population(raw, population, check.description)
        if check.must.op == "count_gte":
            count = len(items)
            passed = count >= check.must.value
            return CheckResult(
                check.description,
                population,
                check.must,
                count,
                count,
                passed,
                f"count={count}, required>={check.must.value}",
            )
        values = [resolve_path(item, check.must.path) for item in items]
        passed, observed, detail = _eval_population_op(
            values, check.must, as_of, check.description
        )
        return CheckResult(
            check.description, population, check.must, len(items), observed, passed, detail
        )
    passed, observed, detail = _eval_scalar_op(raw, check.must, check.description)
    return CheckResult(check.description, None, check.must, None, observed, passed, detail)
