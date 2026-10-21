"""Framework requirement catalogs: identifiers and our own one-line summaries.

No standard text is stored (VISION.md, principle 9). ``complete: false`` marks a
catalog that lists only some of a framework's requirements, so nothing can claim
coverage of the whole framework from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .errors import ConfigError


@dataclass(frozen=True)
class Catalog:
    key: str
    title: str
    version: str
    complete: bool
    requirements: dict[str, str]


def load_catalogs(directory: Path) -> dict[str, Catalog]:
    if not directory.is_dir():
        return {}
    catalogs: dict[str, Catalog] = {}
    for path in sorted(directory.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConfigError(f"{path}: invalid YAML: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"{path}: top level must be a mapping")
        key = data.get("framework")
        requirements = data.get("requirements")
        if not key or not data.get("title") or not data.get("version"):
            raise ConfigError(f"{path}: needs 'framework', 'title' and 'version'")
        if not isinstance(requirements, dict) or not requirements:
            raise ConfigError(
                f"{path}: 'requirements' must be a non-empty mapping of id -> summary"
            )
        if key in catalogs:
            raise ConfigError(f"{path}: duplicate framework {key!r}")
        catalogs[str(key)] = Catalog(
            key=str(key),
            title=str(data["title"]),
            version=str(data["version"]),
            complete=data.get("complete") is True,
            requirements={str(k): str(v) for k, v in requirements.items()},
        )
    return catalogs
