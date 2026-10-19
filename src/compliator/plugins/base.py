"""Thin data-source plugins.

Contract (the whole point of the layering):

  * A plugin pulls RAW FACTS from one source and returns them as a mapping.
  * A plugin validates only SHAPE (top-level keys present, payload is a
    mapping) - never content, never pass/fail, never anything control-shaped.
  * A plugin reports PROVENANCE: where the facts came from and the SHA-256 of
    the underlying bytes, so the packager can bind evidence to its source.

Any control decision made inside a plugin would be unreviewable logic
hiding from the evidence record - so there is none.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path
from typing import Any, ClassVar

from ..errors import PluginError


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_safe(obj: Any, path: str = "$") -> Any:
    """Normalise raw facts to JSON-native values, or refuse loudly.

    Raw facts must be exactly representable in the evidence file. YAML dates
    become ISO strings (lossless for our purposes); anything else that cannot
    survive a JSON round trip (sets, bytes, arbitrary objects) or a non-string
    mapping key is a PluginError - never a silent str() coercion.
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if not isinstance(key, str):
                raise PluginError(
                    f"source facts at {path}: non-string mapping key {key!r} "
                    f"cannot be represented in evidence"
                )
            out[key] = json_safe(value, f"{path}.{key}")
        return out
    if isinstance(obj, (list, tuple)):
        return [json_safe(item, f"{path}[{i}]") for i, item in enumerate(obj)]
    raise PluginError(
        f"source facts at {path}: value of type {type(obj).__name__} cannot be "
        f"represented in evidence"
    )


class SourcePlugin(ABC):
    """Base class for all source plugins."""

    name: ClassVar[str]
    required_keys: ClassVar[tuple[str, ...]] = ()
    description: ClassVar[str] = ""

    def pull(self, options: dict[str, Any], project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
        """Return (raw_facts, provenance) or raise PluginError."""
        raw = self.fetch(options, project_root)
        if not isinstance(raw, dict):
            raise PluginError(
                f"source plugin '{self.name}' returned {type(raw).__name__}, expected mapping"
            )
        raw = json_safe(raw)
        missing = [key for key in self.required_keys if key not in raw]
        if missing:
            raise PluginError(
                f"source plugin '{self.name}': payload missing required top-level "
                f"key(s): {', '.join(missing)} (unexpected shape - refusing to collect)"
            )
        provenance = self.provenance(options, project_root)
        provenance.setdefault("plugin", self.name)
        return raw, provenance

    @abstractmethod
    def fetch(self, options: dict[str, Any], project_root: Path) -> dict[str, Any]:
        """Pull raw facts. Raise PluginError for any access/shape problem."""

    @abstractmethod
    def provenance(self, options: dict[str, Any], project_root: Path) -> dict[str, Any]:
        """Return provenance metadata (must include source file sha256)."""


def _resolve_option_path(options: dict[str, Any], key: str, plugin: str) -> Path:
    rel = options.get(key)
    if not rel or not isinstance(rel, str):
        raise PluginError(f"plugin '{plugin}': options.{key} (string path) is required")
    return Path(rel)


class FileFixtureMixin:
    """Shared helpers for plugins backed by a local file (all POC sources)."""

    file_option: ClassVar[str] = "fixture"

    def _fixture_path(self, options: dict[str, Any], project_root: Path, plugin: str) -> Path:
        path = _resolve_option_path(options, self.file_option, plugin)
        if not path.is_absolute():
            path = project_root / path
        if not path.is_file():
            raise PluginError(
                f"source unreachable: {path} does not exist "
                f"(plugin '{plugin}' cannot collect - NOT emitting empty evidence)"
            )
        return path

    def _file_provenance(self, path: Path, project_root: Path, plugin: str, kind: str) -> dict[str, Any]:
        try:
            rel = str(path.relative_to(project_root))
        except ValueError:
            rel = str(path)
        return {
            "kind": kind,
            "file": rel,
            "file_sha256": sha256_file(path),
        }
