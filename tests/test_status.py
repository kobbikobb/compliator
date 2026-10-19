import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from compliator.__main__ import main
from compliator.config import load_project
from compliator.engine import collect
from compliator.errors import CompliatorError
from compliator.onboarding import run as run_init
from compliator.status import run

ROOT = Path(__file__).resolve().parents[1]


class TestStatus(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.instance = self.tmp / "instance"

    def tearDown(self):
        self._tmp.cleanup()

    # -- helpers -------------------------------------------------------------

    def _scaffold(self, **answers):
        path = self.tmp / "answers.yaml"
        path.write_text(yaml.safe_dump(answers), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            run_init(self.instance, answers_path=path, today="2026-10-19")
        return self.instance

    def _status(self, as_of="2026-10-19", **kwargs):
        out = io.StringIO()
        code = run(self.instance, as_of=as_of, out=out, **kwargs)
        return code, out.getvalue()

    def _document(self, relative, front, body="\nNothing to finish here.\n"):
        path = self.instance / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        block = yaml.safe_dump(front, sort_keys=False)
        path.write_text(f"---\n{block}---\n{body}", encoding="utf-8")
        return path

    def _common_front(self, **overrides):
        front = {
            "owner": "founder@example.invalid",
            "status": "draft",
            "review_cadence": "annual",
            "last_reviewed": "2026-09-01",
        }
        front.update(overrides)
        return front

    def _clean_instance(self, policy_overrides=None, body="\nNothing to finish here.\n"):
        """A complete document set: scope, one policy, one risk - nothing unfinished."""
        self._document("isms/scope.md", {"id": "scope", "title": "Scope", **self._common_front()})
        self._document(
            "isms/risks/RISK-001-credential-leak.md",
            {"id": "RISK-001", "title": "A credential leaks", **self._common_front(status="open")},
        )
        front = {"id": "POL-001", "title": "Information Security Policy", **self._common_front()}
        front.update(policy_overrides or {})
        return self._document("isms/policies/POL-001-information-security.md", front, body=body)

    def _collect_into(self, evidence_root):
        with tempfile.TemporaryDirectory() as fixtures:
            code = collect(
                load_project(ROOT / "config"),
                as_of="2026-10-18",
                evidence_root=Path(fixtures) / "evidence",
                out=io.StringIO(),
                err=io.StringIO(),
            )
            self.assertEqual(code, 0)
            shutil.copytree(Path(fixtures) / "evidence", evidence_root)

    # -- a fresh scaffold ----------------------------------------------------

    def test_freshly_scaffolded_instance_reports_unfinished_work(self):
        self._scaffold(organization="Acme", frameworks="iso_27001_2022", policies="minimal")

        code, out = self._status()

        self.assertEqual(code, 1)
        self.assertIn("unfinished:", out)
        self.assertIn("0 error(s)", out)
        self.assertIn("No control configuration", out)  # documents-only instance

    def test_documents_only_instance_reports_the_empty_register(self):
        self._scaffold(organization="Acme", policies="none")

        code, out = self._status()

        self.assertEqual(code, 1)
        self.assertIn("no policies yet", out)
        self.assertIn("0 error(s)", out)

    def test_status_writes_nothing(self):
        self._scaffold(organization="Acme", policies="minimal")
        before = {str(path): path.stat().st_mtime_ns for path in self.instance.rglob("*")}

        self._status()

        after = {str(path): path.stat().st_mtime_ns for path in self.instance.rglob("*")}
        self.assertEqual(before, after)

    # -- document findings ---------------------------------------------------

    def test_approved_without_an_approver_is_an_error(self):
        self._clean_instance({"status": "approved"})

        code, out = self._status()

        self.assertEqual(code, 1)
        self.assertIn("no `approved_by`", out)

    def test_approved_with_todos_left_is_an_error(self):
        self._clean_instance(
            {"status": "approved", "approved_by": "founder@example.invalid"},
            body="\nTODO: write the actual policy here.\n",
        )

        code, out = self._status()

        self.assertEqual(code, 1)
        self.assertIn("unfinished work presented as done", out)

    def test_missing_owner_is_an_error(self):
        self._clean_instance({"owner": ""})

        code, out = self._status()

        self.assertEqual(code, 1)
        self.assertIn("no owner", out)

    def test_missing_front_matter_is_an_error(self):
        self._clean_instance()
        (self.instance / "isms/policies/POL-002-risk-management.md").write_text(
            "# A policy with no front matter\n", encoding="utf-8"
        )

        code, out = self._status()

        self.assertEqual(code, 1)
        self.assertIn("no front matter", out)

    def test_overdue_review_is_a_warning(self):
        self._clean_instance({"last_reviewed": "2024-01-01"})

        code, out = self._status(as_of="2026-10-19")

        self.assertEqual(code, 1)
        self.assertIn("review overdue", out)

    def test_review_inside_the_cadence_is_clean(self):
        self._clean_instance()

        code, out = self._status(as_of="2026-10-19")

        self.assertEqual(code, 0)
        self.assertIn("0 warning(s)", out)

    def test_citing_a_control_that_does_not_exist_is_an_error(self):
        self._clean_instance({"controls": ["soc2-cc9.9"]})

        code, out = self._status()

        self.assertEqual(code, 1)
        self.assertIn("soc2-cc9.9", out)

    def test_the_word_todo_in_prose_is_not_a_marker(self):
        body = "\n> Replace every `TODO` as you go. A policy that still says `TODO` is not evidence.\n"
        self._clean_instance(body=body)

        code, out = self._status()

        self.assertEqual(code, 0)
        self.assertIn("draft, no TODOs left", out)

    # -- evidence findings ---------------------------------------------------

    def test_stale_evidence_is_a_warning(self):
        self._clean_instance()
        evidence_root = self.instance / "evidence"
        self._collect_into(evidence_root)

        # `collected_at` is wall-clock, so staleness is measured from a date far
        # enough ahead that no cadence can cover it.
        code, out = self._status(as_of="2027-06-01", config_dir=ROOT / "config", evidence_dir=evidence_root)

        self.assertEqual(code, 1)
        self.assertIn("old, collected every", out)

    def test_fresh_evidence_passes_verification(self):
        self._clean_instance()
        evidence_root = self.instance / "evidence"
        self._collect_into(evidence_root)

        # No --as-of: aged against the same day the record was written.
        code, out = self._status(config_dir=ROOT / "config", evidence_dir=evidence_root)

        self.assertEqual(code, 0)
        self.assertNotIn("fails verification", out)

    def test_a_tampered_record_is_an_error(self):
        self._clean_instance()
        evidence_root = self.instance / "evidence"
        self._collect_into(evidence_root)
        raw = next(evidence_root.glob("*/[0-9]*/raw/*.json"))
        raw.write_text(json.dumps({"tampered": True}), encoding="utf-8")

        code, out = self._status(config_dir=ROOT / "config", evidence_dir=evidence_root)

        self.assertEqual(code, 1)
        self.assertIn("fails verification", out)

    def test_missing_evidence_is_a_warning(self):
        self._clean_instance()

        code, out = self._status(config_dir=ROOT / "config", evidence_dir=self.instance / "evidence")

        self.assertEqual(code, 1)
        self.assertIn("no evidence collected yet", out)

    # -- wiring --------------------------------------------------------------

    def test_a_target_that_is_not_there_is_refused(self):
        with self.assertRaises(CompliatorError):
            run(self.instance, out=io.StringIO())

    def test_an_unreadable_as_of_is_refused(self):
        self._clean_instance()

        with self.assertRaises(CompliatorError):
            run(self.instance, as_of="last tuesday", out=io.StringIO())

    def test_cli_runs_status_and_returns_its_exit_code(self):
        self._scaffold(organization="Acme", policies="none")
        out = io.StringIO()

        with contextlib.redirect_stdout(out):
            code = main(["status", "--target", str(self.instance), "--as-of", "2026-10-19"])

        self.assertEqual(code, 1)
        self.assertIn("Instance:", out.getvalue())


if __name__ == "__main__":
    unittest.main()
