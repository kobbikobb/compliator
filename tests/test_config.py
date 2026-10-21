import tempfile
import unittest
from pathlib import Path

from compliator.config import load_project
from compliator.errors import ConfigError

GOOD_SOURCE = """
sources:
  dummy:
    plugin: mock_github
    options:
      fixture: fixtures/github_org.json
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


CONTROL_TEMPLATE = """
control:
  id: test-control
  title: T
  statement: S
  owner: o@example.invalid
  frequency: 1d
  frameworks:
    soc2: "CC1"
source: dummy
checks:
  - description: d
    {body}
"""


class TestConfigValidation(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.config = self.root / "config"
        write(self.config / "sources.yaml", GOOD_SOURCE)

    def tearDown(self):
        self._tmp.cleanup()

    def load(self):
        return load_project(self.config)

    def test_valid_project_loads(self):
        write(
            self.config / "controls" / "c.yaml",
            CONTROL_TEMPLATE.format(body="must:\n      path: a\n      op: equals\n      value: 1"),
        )
        project = self.load()
        self.assertEqual(len(project.controls), 1)
        self.assertEqual(project.controls[0].frequency_days, 1)

    def test_unknown_op_rejected(self):
        write(
            self.config / "controls" / "c.yaml",
            CONTROL_TEMPLATE.format(
                body="must:\n      path: a\n      op: whatever\n      value: 1"
            ),
        )
        with self.assertRaises(ConfigError):
            self.load()

    def test_population_op_without_population_rejected(self):
        write(
            self.config / "controls" / "c.yaml",
            CONTROL_TEMPLATE.format(
                body="must:\n      path: a\n      op: all_equal\n      value: 1"
            ),
        )
        with self.assertRaises(ConfigError):
            self.load()

    def test_scalar_op_with_population_rejected(self):
        write(
            self.config / "controls" / "c.yaml",
            CONTROL_TEMPLATE.format(
                body="population:\n      path: items\n    must:\n      path: a\n      op: equals\n      value: 1"
            ),
        )
        with self.assertRaises(ConfigError):
            self.load()

    def test_op_requiring_value_rejected_without_value(self):
        write(
            self.config / "controls" / "c.yaml",
            CONTROL_TEMPLATE.format(body="must:\n      path: a\n      op: all_equal"),
        )
        with self.assertRaises(ConfigError):
            self.load()

    def test_dangling_source_rejected(self):
        write(
            self.config / "controls" / "c.yaml",
            CONTROL_TEMPLATE.format(
                body="must:\n      path: a\n      op: equals\n      value: 1"
            ).replace("source: dummy", "source: nope"),
        )
        with self.assertRaises(ConfigError):
            self.load()

    def test_duplicate_control_id_rejected(self):
        body = "must:\n      path: a\n      op: equals\n      value: 1"
        write(self.config / "controls" / "a.yaml", CONTROL_TEMPLATE.format(body=body))
        write(self.config / "controls" / "b.yaml", CONTROL_TEMPLATE.format(body=body))
        with self.assertRaises(ConfigError):
            self.load()

    def test_bad_frequency_rejected(self):
        write(
            self.config / "controls" / "c.yaml",
            CONTROL_TEMPLATE.format(
                body="must:\n      path: a\n      op: equals\n      value: 1"
            ).replace("frequency: 1d", "frequency: soon"),
        )
        with self.assertRaises(ConfigError):
            self.load()

    def test_missing_owner_rejected(self):
        write(
            self.config / "controls" / "c.yaml",
            CONTROL_TEMPLATE.format(
                body="must:\n      path: a\n      op: equals\n      value: 1"
            ).replace("owner: o@example.invalid\n", ""),
        )
        with self.assertRaises(ConfigError):
            self.load()


CATALOG = """
framework: fw
title: Framework
version: "1"
complete: {complete}
requirements:
  R1: first
  R2: second
"""

MAPPED_CONTROL = CONTROL_TEMPLATE.replace(
    'frameworks:\n    soc2: "CC1"', "mappings:\n    {mappings}"
)


class TestMappings(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        write(self.root / "config" / "sources.yaml", GOOD_SOURCE)
        write(self.root / "frameworks" / "fw.yaml", CATALOG.format(complete="true"))

    def tearDown(self):
        self._tmp.cleanup()

    def load(self, mappings):
        body = "must:\n      path: a\n      op: equals\n      value: 1"
        write(
            self.root / "config" / "controls" / "c.yaml",
            MAPPED_CONTROL.format(mappings=mappings, body=body),
        )
        return load_project(self.root / "config")

    def test_mapped_ids_are_checked_and_summarised(self):
        control = self.load("fw: [R1]").controls[0]

        self.assertEqual(control.mappings, {"fw": ("R1",)})
        self.assertEqual(control.frameworks, {"fw": "R1 - first"})

    def test_an_id_missing_from_the_catalog_is_refused(self):
        with self.assertRaisesRegex(ConfigError, "'R9' is not in the fw catalog"):
            self.load("fw: [R9]")

    def test_an_unknown_framework_is_refused(self):
        with self.assertRaisesRegex(ConfigError, "unknown framework 'other'"):
            self.load("other: [R1]")


if __name__ == "__main__":
    unittest.main()
