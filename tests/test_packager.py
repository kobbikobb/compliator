import io
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from compliator.config import load_project
from compliator.engine import collect
from compliator.errors import VerificationError
from compliator.evaluate import evaluate_check
from compliator.verify import verify_record

ROOT = Path(__file__).resolve().parents[1]


class TestPackagerAndVerify(unittest.TestCase):
    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.project = load_project(ROOT / "config")

    def tearDown(self):
        self._tmp.cleanup()

    def _collect_one(self):
        code = collect(
            self.project, control_ids=["soc2-cc8.1"], as_of="2026-10-17",
            evidence_root=self.tmp, out=io.StringIO(), err=io.StringIO(),
        )
        self.assertEqual(code, 0)
        record = next((self.tmp / "soc2-cc8.1").glob("*/"))
        return record

    def test_record_contains_raw_copy_and_provenance(self):
        record = self._collect_one()
        import json

        evidence = json.loads((record / "evidence.json").read_text())
        self.assertEqual(evidence["schema"], "compliator/evidence-record/v1")
        self.assertEqual(evidence["result"], "pass")
        self.assertEqual(evidence["source"]["plugin"], "mock_github")
        self.assertIn("file_sha256", evidence["source"]["provenance"])
        self.assertTrue((record / evidence["source"]["raw_file"]).is_file())
        # observed values are recorded, not just the verdict
        for check in evidence["checks"]:
            self.assertIn("observed", check)

    def test_verify_passes_on_fresh_record(self):
        record = self._collect_one()
        report = verify_record(record)
        self.assertTrue(report["ok"])
        self.assertEqual(report["control_id"], "soc2-cc8.1")

    def test_verify_detects_raw_tampering(self):
        record = self._collect_one()
        raw = record / "raw" / "github_org.json"
        import json

        payload = json.loads(raw.read_text())
        payload["repos"][0]["branch_protection"]["main"]["required_pull_request_reviews"]["enabled"] = False
        raw.write_text(json.dumps(payload, indent=2) + "\n")
        with self.assertRaises(VerificationError):
            verify_record(record)

    def test_verify_detects_evidence_edit(self):
        record = self._collect_one()
        evidence_path = record / "evidence.json"
        text = evidence_path.read_text().replace('"result": "pass"', '"result": "pass" ')
        evidence_path.write_text(text)
        with self.assertRaises(VerificationError):
            verify_record(record)

    def test_packager_is_deterministic_apart_from_timestamp(self):
        """Same inputs + same collected_at => byte-identical evidence.json."""
        from compliator.packager import write_record
        from compliator.plugins import get_plugin

        control = self.project.control_by_id("soc2-cc8.1")
        plugin = get_plugin("mock_github")
        options = self.project.sources["github_org"].options
        raw, provenance = plugin.pull(options, self.project.root)
        results = [evaluate_check(raw, c, date(2026, 10, 17)) for c in control.checks]
        stamp = datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)

        dir_a = self.tmp / "a"
        dir_b = self.tmp / "b"
        rec_a, _ = write_record(dir_a, control, "github_org", "mock_github", provenance, raw, results, "2026-10-17", stamp)
        rec_b, _ = write_record(dir_b, control, "github_org", "mock_github", provenance, raw, results, "2026-10-17", stamp)
        self.assertEqual((rec_a / "evidence.json").read_bytes(), (rec_b / "evidence.json").read_bytes())
        self.assertEqual(rec_a.name, rec_b.name)

    def test_latest_pointer_updates_on_success_only(self):
        record = self._collect_one()
        latest = self.tmp / "soc2-cc8.1" / "LATEST.json"
        self.assertTrue(latest.is_file())
        before = latest.read_text()
        collect(
            self.project, control_ids=["soc2-cc8.1"], as_of="2026-10-17",
            simulate_failure="github_org", evidence_root=self.tmp,
            out=io.StringIO(), err=io.StringIO(),
        )
        self.assertEqual(latest.read_text(), before)


if __name__ == "__main__":
    unittest.main()
