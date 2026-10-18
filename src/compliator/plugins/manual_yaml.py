"""Manual input plugin - reads a human-maintained YAML file (manual/*.yaml).

This is the deliberate 20%: evidence that no system can produce because a
person attests to it (policy acknowledgments, vendor review sign-off).
The form is still collected through the same pipeline - raw copy + hash +
provenance - so manual evidence gets identical treatment to exports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import yaml

from ..errors import PluginError
from .base import FileFixtureMixin, SourcePlugin


class ManualYamlPlugin(FileFixtureMixin, SourcePlugin):
    name = "manual_yaml"
    description = "Human-maintained YAML attestation form (manual input)"
    required_keys: ClassVar[tuple[str, ...]] = ()
    file_option: ClassVar[str] = "path"

    def fetch(self, options: dict[str, Any], project_root: Path) -> dict[str, Any]:
        path = self._fixture_path(options, project_root, self.name)
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise PluginError(f"source unreachable: cannot read {path}: {exc}") from exc
        if not isinstance(data, dict) or not data:
            raise PluginError(f"{path}: expected a non-empty mapping")
        return data

    def provenance(self, options: dict[str, Any], project_root: Path) -> dict[str, Any]:
        path = self._fixture_path(options, project_root, self.name)
        prov = self._file_provenance(path, project_root, self.name, kind="manual_input")
        prov["maintained_by"] = options.get("maintained_by", "human (see form header)")
        return prov
