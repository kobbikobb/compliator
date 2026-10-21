"""Mock cloud plugin - reads fixtures/cloud_config.json.

Stands in for cloud provider APIs (AWS CloudTrail DescribeTrails /
GetUser etc.). Raw facts only: logging config and IAM user attributes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, ClassVar

from ..errors import PluginError
from .base import FileFixtureMixin, SourcePlugin


class MockCloudPlugin(FileFixtureMixin, SourcePlugin):
    name = "mock_cloud"
    description = "Cloud account facts (mock fixture)"
    required_keys: ClassVar[tuple[str, ...]] = ("account_id", "logging", "iam_users")
    file_option: ClassVar[str] = "fixture"

    def fetch(self, options: dict[str, Any], project_root: Path) -> dict[str, Any]:
        path = self._fixture_path(options, project_root, self.name)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PluginError(f"source unreachable: cannot read {path}: {exc}") from exc
        if not isinstance(data.get("iam_users"), list):
            raise PluginError(f"{path}: 'iam_users' must be a list (unexpected shape)")
        if not isinstance(data.get("logging"), dict):
            raise PluginError(f"{path}: 'logging' must be a mapping (unexpected shape)")
        return dict(data)

    def provenance(self, options: dict[str, Any], project_root: Path) -> dict[str, Any]:
        path = self._fixture_path(options, project_root, self.name)
        prov = self._file_provenance(path, project_root, self.name, kind="mock_cloud_fixture")
        prov["account_id"] = "0000-1111-2222"
        return prov
