"""Mock GitHub plugin - reads fixtures/github_org.json.

Stands in for a real GitHub REST/GraphQL client. In a real deployment the
``fetch`` body becomes API calls (list repos -> get branch protection ->
list workflow runs) and nothing else in this file changes structurally.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, ClassVar

from ..errors import PluginError
from .base import FileFixtureMixin, SourcePlugin


class MockGitHubPlugin(FileFixtureMixin, SourcePlugin):
    name = "mock_github"
    description = "GitHub organization facts (mock fixture)"
    required_keys: ClassVar[tuple[str, ...]] = ("org", "repos", "workflow_runs")
    file_option: ClassVar[str] = "fixture"

    def fetch(self, options: dict[str, Any], project_root: Path) -> dict[str, Any]:
        path = self._fixture_path(options, project_root, self.name)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PluginError(f"source unreachable: cannot read {path}: {exc}") from exc
        if not isinstance(data.get("repos"), list) or not isinstance(
            data.get("workflow_runs"), list
        ):
            raise PluginError(
                f"{path}: 'repos' and 'workflow_runs' must be lists (unexpected shape)"
            )
        return dict(data)

    def provenance(self, options: dict[str, Any], project_root: Path) -> dict[str, Any]:
        path = self._fixture_path(options, project_root, self.name)
        prov = self._file_provenance(path, project_root, self.name, kind="mock_github_fixture")
        prov["base_url"] = "https://github.example.invalid"
        return prov
