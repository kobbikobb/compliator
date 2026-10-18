"""HR roster plugin - reads fixtures/hr_roster.csv.

Stands in for an HR system export (CSV). Parsing notes:
  * empty cells become None (an empty CSV cell means "not recorded", and
    evidence must distinguish that from a real value),
  * the raw facts include row_count so population completeness can be
    cross-checked against the source file.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, ClassVar

from ..errors import PluginError
from .base import FileFixtureMixin, SourcePlugin

REQUIRED_COLUMNS = ("name", "status", "start_date")


class HRRosterPlugin(FileFixtureMixin, SourcePlugin):
    name = "hr_roster"
    description = "HR roster CSV export (mock fixture)"
    required_keys: ClassVar[tuple[str, ...]] = ("employees", "row_count")
    file_option: ClassVar[str] = "fixture"

    def fetch(self, options: dict[str, Any], project_root: Path) -> dict[str, Any]:
        path = self._fixture_path(options, project_root, self.name)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise PluginError(f"source unreachable: cannot read {path}: {exc}") from exc
        reader = csv.DictReader(text.splitlines(), restkey="__extra_columns__")
        if reader.fieldnames is None:
            raise PluginError(f"{path}: empty CSV (unexpected shape)")
        missing = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
        if missing:
            raise PluginError(
                f"{path}: CSV missing required column(s): {', '.join(missing)}"
            )
        employees = []
        for row_num, row in enumerate(reader, start=2):
            extra = row.pop("__extra_columns__", None)
            if extra:
                raise PluginError(
                    f"{path}: row {row_num} has more fields than the header "
                    f"(unexpected shape - refusing to guess; check for stray commas)"
                )
            employees.append(
                {key: (value if value not in ("", None) else None) for key, value in row.items()}
            )
        if not employees:
            raise PluginError(f"{path}: CSV contains no data rows")
        return {"employees": employees, "row_count": len(employees), "columns": list(reader.fieldnames)}

    def provenance(self, options: dict[str, Any], project_root: Path) -> dict[str, Any]:
        path = self._fixture_path(options, project_root, self.name)
        return self._file_provenance(path, project_root, self.name, kind="hr_csv_export")
