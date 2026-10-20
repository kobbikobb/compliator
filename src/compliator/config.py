"""Configuration loading and validation.

Two layers of config drive everything:

  config/sources.yaml      - named sources; each maps to exactly one plugin
                             whose only job is pulling raw facts.
  config/controls/*.yaml   - one file per control: metadata, source
                             reference, and declarative checks.

Adding a control must be config-only unless it needs a genuinely new data
source (then: one thin plugin + a sources.yaml entry, still no control
logic outside these YAML files).

Validation is strict and happens BEFORE any collection: unknown operators,
op/population mismatches, dangling source references and duplicate control
ids are all hard ConfigErrors - a typo in a control definition must never
degrade into silently-not-checked evidence.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError
from .requirements import Catalog, load_catalogs
from .evaluate import ALL_OPS, OPS_REQUIRING_VALUE, POPULATION_OPS, SCALAR_OPS, Must, Population

FREQUENCY_RE = re.compile(r"^(\d+)d$")
CONTROL_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9.]+)+$")


@dataclass
class SourceDef:
    name: str
    plugin: str
    description: str
    options: dict[str, Any]


@dataclass
class Check:
    description: str
    population: Population | None
    must: Must

    @classmethod
    def from_dict(cls, data: dict[str, Any], context: str) -> "Check":
        if not isinstance(data, dict):
            raise ConfigError(f"{context}: check must be a mapping")
        description = data.get("description")
        if not description or not isinstance(description, str):
            raise ConfigError(f"{context}: check missing 'description'")

        population = None
        if "population" in data:
            pop_raw = data["population"]
            if not isinstance(pop_raw, dict) or "path" not in pop_raw:
                raise ConfigError(f"{context}: 'population' needs a 'path'")
            where = pop_raw.get("where", {})
            if not isinstance(where, dict):
                raise ConfigError(f"{context}: 'population.where' must be a mapping")
            population = Population(path=str(pop_raw["path"]), where=where)

        must_raw = data.get("must")
        if not isinstance(must_raw, dict):
            raise ConfigError(f"{context}: check missing 'must'")
        path = must_raw.get("path")
        if not path or not isinstance(path, str):
            raise ConfigError(f"{context}: 'must.path' is required")
        op = must_raw.get("op")
        if op not in ALL_OPS:
            raise ConfigError(
                f"{context}: unknown op {op!r} (supported: {', '.join(sorted(ALL_OPS))})"
            )
        if "value" not in must_raw and op in OPS_REQUIRING_VALUE:
            raise ConfigError(f"{context}: op {op!r} requires 'value'")

        if population is not None:
            if op not in POPULATION_OPS:
                raise ConfigError(
                    f"{context}: op {op!r} cannot be combined with 'population' "
                    f"(population ops: {', '.join(sorted(POPULATION_OPS))})"
                )
        else:
            if op in POPULATION_OPS - SCALAR_OPS:
                raise ConfigError(
                    f"{context}: op {op!r} requires a 'population'"
                )

        must = Must(path=path, op=op, value=must_raw.get("value"))
        return cls(description=description, population=population, must=must)


@dataclass
class Control:
    id: str
    title: str
    statement: str
    owner: str
    frequency_days: int
    frameworks: dict[str, str]
    mappings: dict[str, tuple[str, ...]]
    source: str
    checks: list[Check]
    config_path: Path
    config_sha256: str


@dataclass
class Project:
    root: Path
    config_dir: Path
    sources: dict[str, SourceDef]
    controls: list[Control]
    catalogs: dict[str, Catalog]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigError(f"missing config file: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top level must be a mapping")
    return data


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_sources(config_dir: Path) -> dict[str, SourceDef]:
    path = config_dir / "sources.yaml"
    data = _load_yaml(path)
    raw_sources = data.get("sources")
    if not isinstance(raw_sources, dict) or not raw_sources:
        raise ConfigError(f"{path}: 'sources' must be a non-empty mapping")
    sources: dict[str, SourceDef] = {}
    for name, body in raw_sources.items():
        if not isinstance(body, dict):
            raise ConfigError(f"{path}: source '{name}' must be a mapping")
        plugin = body.get("plugin")
        if not plugin:
            raise ConfigError(f"{path}: source '{name}' missing 'plugin'")
        options = body.get("options", {})
        if not isinstance(options, dict):
            raise ConfigError(f"{path}: source '{name}' options must be a mapping")
        sources[name] = SourceDef(
            name=name,
            plugin=plugin,
            description=str(body.get("description", "")),
            options=options,
        )
    return sources


def _parse_mappings(
    raw: Any, catalogs: dict[str, Catalog], path: Path
) -> dict[str, tuple[str, ...]]:
    """``{framework: [requirement ids]}``, every id checked against its catalog."""
    if raw is None:
        return {}
    if not isinstance(raw, dict) or not raw:
        raise ConfigError(f"{path}: 'mappings' must be a non-empty mapping of framework -> [ids]")
    mappings: dict[str, tuple[str, ...]] = {}
    for key, ids in raw.items():
        key = str(key)
        if key not in catalogs:
            known = ", ".join(sorted(catalogs)) or "none - no frameworks/ catalog found"
            raise ConfigError(f"{path}: mappings: unknown framework {key!r} (known: {known})")
        if not isinstance(ids, list) or not ids:
            raise ConfigError(f"{path}: mappings.{key} must be a non-empty list of requirement ids")
        for rid in map(str, ids):
            if rid not in catalogs[key].requirements:
                raise ConfigError(f"{path}: mappings.{key}: {rid!r} is not in the {key} catalog")
        mappings[key] = tuple(str(rid) for rid in ids)
    return mappings


def load_controls(
    config_dir: Path, sources: dict[str, SourceDef], catalogs: dict[str, Catalog] | None = None
) -> list[Control]:
    catalogs = catalogs or {}
    controls_dir = config_dir / "controls"
    if not controls_dir.is_dir():
        raise ConfigError(f"missing controls directory: {controls_dir}")
    paths = sorted(controls_dir.glob("*.yaml"))
    if not paths:
        raise ConfigError(f"no control configs found in {controls_dir}")

    controls: list[Control] = []
    seen_ids: set[str] = set()
    for path in paths:
        data = _load_yaml(path)
        meta = data.get("control")
        if not isinstance(meta, dict):
            raise ConfigError(f"{path}: missing 'control' mapping")

        control_id = meta.get("id")
        if not control_id or not CONTROL_ID_RE.match(str(control_id)):
            raise ConfigError(
                f"{path}: control id {control_id!r} must be lowercase, hyphen-separated "
                f"(e.g. soc2-cc8.1)"
            )
        if control_id in seen_ids:
            raise ConfigError(f"{path}: duplicate control id '{control_id}'")
        seen_ids.add(control_id)

        frequency = str(meta.get("frequency", ""))
        freq_match = FREQUENCY_RE.match(frequency)
        if not freq_match:
            raise ConfigError(f"{path}: frequency must look like '1d', got {frequency!r}")

        mappings = _parse_mappings(meta.get("mappings"), catalogs, path)
        framework_raw = meta.get("frameworks", {})
        if mappings:
            framework_raw = {
                key: ", ".join(f"{rid} - {catalogs[key].requirements[rid]}" for rid in ids)
                for key, ids in mappings.items()
            }
        if not isinstance(framework_raw, dict) or not framework_raw:
            raise ConfigError(f"{path}: needs a non-empty 'mappings' (or legacy 'frameworks') mapping")

        source = data.get("source")
        if not source or source not in sources:
            raise ConfigError(
                f"{path}: source {source!r} not defined in sources.yaml "
                f"(known: {', '.join(sorted(sources))})"
            )

        checks_raw = data.get("checks")
        if not isinstance(checks_raw, list) or not checks_raw:
            raise ConfigError(f"{path}: 'checks' must be a non-empty list")
        checks = [
            Check.from_dict(entry, f"{path}: check #{i + 1}")
            for i, entry in enumerate(checks_raw)
        ]

        for required in ("title", "statement", "owner"):
            if not meta.get(required):
                raise ConfigError(f"{path}: control missing '{required}'")

        controls.append(
            Control(
                id=str(control_id),
                title=str(meta["title"]),
                statement=str(meta["statement"]).strip(),
                owner=str(meta["owner"]),
                frequency_days=int(freq_match.group(1)),
                frameworks={str(k): str(v) for k, v in framework_raw.items()},
                mappings=mappings,
                source=str(source),
                checks=checks,
                config_path=path,
                config_sha256=_sha256_file(path),
            )
        )
    return controls


def load_project(config_dir: str | Path = "config") -> Project:
    config_dir = Path(config_dir).resolve()
    if not config_dir.is_dir():
        raise ConfigError(f"config directory not found: {config_dir}")
    root = config_dir.parent
    sources = load_sources(config_dir)
    catalogs = load_catalogs(root / "frameworks")
    controls = load_controls(config_dir, sources, catalogs)
    return Project(root=root, config_dir=config_dir, sources=sources, controls=controls, catalogs=catalogs)
