import io
import unittest
from pathlib import Path

from compliator.config import load_project
from compliator.engine import collect

ROOT = Path(__file__).resolve().parents[1]


class TestEngineEndToEnd(unittest.TestCase):
    def setUp(self):
        self.project = load_project(ROOT / "config")
        self.evidence = Path(self.tmpdir())

    def tmpdir(self):
        import tempfile

        if not hasattr(self, "_tmp"):
            self._tmp = tempfile.TemporaryDirectory()
        return self._tmp.name

    def tearDown(self):
        if hasattr(self, "_tmp"):
            self._tmp.cleanup()

    def test_collect_all_green(self):
        out, err = io.StringIO(), io.StringIO()
        code = collect(
            self.project, as_of="2026-10-17", evidence_root=self.evidence, out=out, err=err
        )
        self.assertEqual(code, 0, msg=err.getvalue())
        self.assertIn("All controls collected and passing.", out.getvalue())

        for control in self.project.controls:
            latest = self.evidence / control.id / "LATEST.json"
            self.assertTrue(latest.is_file(), f"missing LATEST for {control.id}")
            self.assertIn('"result": "pass"', latest.read_text())

    def test_collect_single_control(self):
        out, err = io.StringIO(), io.StringIO()
        code = collect(
            self.project,
            control_ids=["soc2-cc8.1"],
            as_of="2026-10-17",
            evidence_root=self.evidence,
            out=out,
            err=err,
        )
        self.assertEqual(code, 0)
        self.assertTrue((self.evidence / "soc2-cc8.1" / "LATEST.json").is_file())
        self.assertFalse((self.evidence / "soc2-cc7.2").exists())

    def test_unknown_control_is_config_error(self):
        code = collect(
            self.project,
            control_ids=["nope"],
            evidence_root=self.evidence,
            out=io.StringIO(),
            err=io.StringIO(),
        )
        self.assertEqual(code, 2)

    def test_simulated_failure_is_loud_and_writes_no_record(self):
        out, err = io.StringIO(), io.StringIO()
        code = collect(
            self.project,
            control_ids=["soc2-cc8.1"],
            as_of="2026-10-17",
            simulate_failure="github_org",
            evidence_root=self.evidence,
            out=out,
            err=err,
        )
        self.assertEqual(code, 2)
        self.assertIn("COLLECTION FAILED", err.getvalue())
        self.assertIn("NO evidence record was written", err.getvalue())
        self.assertFalse((self.evidence / "soc2-cc8.1" / "LATEST.json").exists())

    def test_failure_reports_last_good_age(self):
        collect(
            self.project,
            control_ids=["soc2-cc8.1"],
            as_of="2026-10-17",
            evidence_root=self.evidence,
            out=io.StringIO(),
            err=io.StringIO(),
        )
        err = io.StringIO()
        collect(
            self.project,
            control_ids=["soc2-cc8.1"],
            as_of="2026-10-17",
            simulate_failure="github_org",
            evidence_root=self.evidence,
            out=io.StringIO(),
            err=err,
        )
        self.assertIn("last good evidence:", err.getvalue())

    def test_no_last_good_is_reported_as_none(self):
        err = io.StringIO()
        collect(
            self.project,
            control_ids=["soc2-cc8.1"],
            as_of="2026-10-17",
            simulate_failure="github_org",
            evidence_root=self.evidence,
            out=io.StringIO(),
            err=err,
        )
        self.assertIn("last good evidence: NONE", err.getvalue())


if __name__ == "__main__":
    unittest.main()
