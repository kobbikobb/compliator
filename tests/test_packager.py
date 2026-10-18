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


    def test_manifest_carries_schema_and_no_command_string(self):
        """The manifest pins a format; it stores no checkout-specific command."""
        import json

        record = self._collect_one()
        manifest = json.loads((record / "MANIFEST.json").read_text())
        self.assertEqual(manifest["schema"], "compliator/evidence-manifest/v1")
        self.assertNotIn("verify_with", manifest)
        for rel, digest in manifest["files"].items():
            self.assertTrue((record / rel).is_file())
            self.assertEqual(len(digest), 64)

    def test_verify_passes_without_warnings_on_current_record(self):
        from compliator import __version__

        record = self._collect_one()
        report = verify_record(record)
        self.assertTrue(report["ok"])
        self.assertEqual(report["engine_version"], __version__)
        self.assertEqual(report["warnings"], [])

    def _write_synthetic_record(self, *, evidence_schema, manifest_schema, engine_version="0.0.1-ancient"):
        """A hand-built record with valid hashes, so schema pins are tested alone."""
        from compliator.packager import canonical_json, sha256_file

        record = self.tmp / "synthetic" / "c1"
        (record / "raw").mkdir(parents=True)
        raw_path = record / "raw" / "source.json"
        raw_path.write_text(canonical_json({"resources": []}), encoding="utf-8")
        evidence = {
            "schema": evidence_schema,
            "control": {"id": "synthetic-1"},
            "collection": {"id": "c1", "engine_version": engine_version},
            "source": {"raw_file": "raw/source.json", "raw_sha256": sha256_file(raw_path)},
            "result": "pass",
        }
        evidence_path = record / "evidence.json"
        evidence_path.write_text(canonical_json(evidence), encoding="utf-8")
        manifest = {
            "collection_id": "c1",
            "control_id": "synthetic-1",
            "files": {
                "evidence.json": sha256_file(evidence_path),
                "raw/source.json": sha256_file(raw_path),
            },
        }
        if manifest_schema is not None:
            manifest["schema"] = manifest_schema
        (record / "MANIFEST.json").write_text(canonical_json(manifest), encoding="utf-8")
        return record

    def test_verify_rejects_unknown_evidence_schema(self):
        record = self._write_synthetic_record(
            evidence_schema="compliator/evidence-record/v9",
            manifest_schema="compliator/evidence-manifest/v1",
        )
        with self.assertRaises(VerificationError) as ctx:
            verify_record(record)
        self.assertIn("schema", str(ctx.exception))

    def test_verify_rejects_unknown_manifest_schema(self):
        record = self._write_synthetic_record(
            evidence_schema="compliator/evidence-record/v1",
            manifest_schema="compliator/evidence-manifest/v9",
        )
        with self.assertRaises(VerificationError) as ctx:
            verify_record(record)
        self.assertIn("schema", str(ctx.exception))

    def test_verify_rejects_manifest_without_schema(self):
        record = self._write_synthetic_record(
            evidence_schema="compliator/evidence-record/v1",
            manifest_schema=None,
        )
        with self.assertRaises(VerificationError) as ctx:
            verify_record(record)
        self.assertIn("no schema", str(ctx.exception))

    def test_verify_reports_engine_version_skew_without_failing(self):
        record = self._write_synthetic_record(
            evidence_schema="compliator/evidence-record/v1",
            manifest_schema="compliator/evidence-manifest/v1",
            engine_version="0.0.1-ancient",
        )
        report = verify_record(record)
        self.assertTrue(report["ok"])
        self.assertEqual(report["engine_version"], "0.0.1-ancient")
        self.assertTrue(any("0.0.1-ancient" in w for w in report["warnings"]))


if __name__ == "__main__":
    unittest.main()
