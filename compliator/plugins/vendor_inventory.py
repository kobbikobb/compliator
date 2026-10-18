"""Vendor inventory plugin - reads fixtures/vendor_inventory.yaml.

Stands in for the company's maintained vendor/service inventory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import yaml

from ..errors import PluginError
from .base import FileFixtureMixin, SourcePlugin


class VendorInventoryPlugin(FileFixtureMixin, SourcePlugin):
    name = "vendor_inventory"
    description = "Vendor inventory with risk tiers (mock fixture)"
    required_keys: ClassVar[tuple[str, ...]] = ("vendors",)
    file_option: ClassVar[str] = "fixture"

    def fetch(self, options: dict[str, Any], project_root: Path) -> dict[str, Any]:
        path = self._fixture_path(options, project_root, self.name)
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise PluginError(f"source unreachable: cannot read {path}: {exc}") from exc
        if not isinstance(data, dict) or not isinstance(data.get("vendors"), list):
            raise PluginError(f"{path}: expected mapping with a 'vendors' list")
        if not data["vendors"]:
            raise PluginError(f"{path}: 'vendors' list is empty")
        return data

    def provenance(self, options: dict[str, Any], project_root: Path) -> dict[str, Any]:
        path = self._fixture_path(options, project_root, self.name)
        return self._file_provenance(path, project_root, self.name, kind="vendor_inventory")
