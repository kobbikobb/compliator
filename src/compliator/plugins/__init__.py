"""Plugin registry.

Adding a new source type: create one thin module (subclass SourcePlugin),
register it here, add an entry to config/sources.yaml. No control logic.
"""

from __future__ import annotations

from ..errors import ConfigError
from .base import SourcePlugin
from .hr_roster import HRRosterPlugin
from .manual_yaml import ManualYamlPlugin
from .mock_cloud import MockCloudPlugin
from .mock_github import MockGitHubPlugin

_REGISTRY: dict[str, type[SourcePlugin]] = {
    plugin.name: plugin
    for plugin in (
        MockGitHubPlugin,
        MockCloudPlugin,
        HRRosterPlugin,
        ManualYamlPlugin,
    )
}


def available_plugins() -> list[str]:
    return sorted(_REGISTRY)


def get_plugin(name: str) -> SourcePlugin:
    try:
        return _REGISTRY[name]()
    except KeyError as exc:
        raise ConfigError(
            f"unknown plugin '{name}' (available: {', '.join(available_plugins())})"
        ) from exc
