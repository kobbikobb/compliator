import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from compliator.__main__ import main
from compliator.config import load_project
from compliator.frameworks import declared_frameworks
from compliator.guidance import (
    _awaiting_approval,
    _controls,
    _coverage,
    _document_errors,
    _evidence,
    _foundation_policies,
    _policies,
    _remaining,
    _risks,
    _Snapshot,
    _soa,
    _unfinished,
    next_step,
)
from compliator.onboarding import Ask, run, run_framework
from compliator.status import Finding, check_coverage


def quietly(function, *args, **kwargs):
    out = io.StringIO()
    with redirect_stdout(out):
        result = function(*args, **kwargs)
    return result, out.getvalue()


class TestFramework(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_menu_number_declares_the_framework_and_writes_its_soa(self):
        quietly(run_framework, self.target, ask=Ask(["1"]))

        self.assertEqual([f.key for f in declared_frameworks(self.target)], ["iso_27001_2022"])
        self.assertTrue((self.target / "isms/soa.iso_27001_2022.md").is_file())

    def test_soc2_is_declared_without_a_soa(self):
        quietly(run_framework, self.target, "soc2")

        self.assertEqual([f.key for f in declared_frameworks(self.target)], ["soc2"])
        self.assertEqual(list((self.target / "isms").glob("soa.*")), [])

    def test_deciding_later_writes_nothing_so_a_later_choice_works(self):
        quietly(run_framework, self.target, "none")
        self.assertFalse((self.target / "isms/frameworks.md").exists())

        quietly(run_framework, self.target, "soc2")
        self.assertEqual([f.key for f in declared_frameworks(self.target)], ["soc2"])

    def test_adding_a_second_framework_records_it_and_keeps_the_first(self):
        quietly(run_framework, self.target, "soc2")
        quietly(run_framework, self.target, "both")

        self.assertEqual(
            [f.key for f in declared_frameworks(self.target)], ["iso_27001_2022", "soc2"]
        )
        text = (self.target / "isms/frameworks.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("SOC 2 Trust Services Criteria |"), 1)
        self.assertIn("ISO/IEC 27001:2022 |", text)

    def test_wizard_offers_to_add_when_one_is_declared_and_keeps_by_default(self):
        quietly(run_framework, self.target, "soc2")

        quietly(run_framework, self.target, ask=Ask([""]))
        self.assertEqual([f.key for f in declared_frameworks(self.target)], ["soc2"])

        quietly(run_framework, self.target, ask=Ask(["1"]))
        self.assertEqual(
            [f.key for f in declared_frameworks(self.target)], ["iso_27001_2022", "soc2"]
        )

    def test_rerunning_the_same_choice_changes_nothing(self):
        quietly(run_framework, self.target, "both")
        before = (self.target / "isms/frameworks.md").read_text(encoding="utf-8")
        _, out = quietly(run_framework, self.target, "both")

        self.assertEqual((self.target / "isms/frameworks.md").read_text(encoding="utf-8"), before)
        self.assertIn("Already declared", out)

    def test_a_note_without_a_table_gets_one_and_keeps_its_text(self):
        notes = self.target / "isms/frameworks.md"
        notes.parent.mkdir(parents=True)
        notes.write_text("# Frameworks\n\nMy own notes.", encoding="utf-8")
        quietly(run_framework, self.target, "soc2")

        text = notes.read_text(encoding="utf-8")
        self.assertIn("My own notes.", text)
        self.assertEqual([f.key for f in declared_frameworks(self.target)], ["soc2"])

    def test_declared_framework_is_not_asked_again_by_init(self):
        quietly(run_framework, self.target, "soc2")
        _, out = quietly(
            run, self.target, ask=Ask(["n"] * 10 + [""] + ["n"] * 20)
        )  # no risks, no documents

        self.assertNotIn("Which framework", out)

    def test_init_framework_flag_skips_the_question(self):
        _, out = quietly(run, self.target, framework="soc2", dry_run=True)

        self.assertNotIn("Which framework", out)
        self.assertNotIn("soa.iso_27001_2022", out.split("Plan:")[-1])


class TestNext(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_empty_instance_starts_with_the_framework(self):
        step = next_step(self.target)

        self.assertIn("framework", step.what)
        self.assertIn("make framework", step.action)

    def test_follows_the_build_order(self):
        quietly(run_framework, self.target, "iso_27001_2022")
        self.assertIn("scope", next_step(self.target).what)

        isms = self.target / "isms"
        (isms / "scope.md").write_text(
            "---\nid: S\ntitle: t\nowner: o\nstatus: draft\n---\n", encoding="utf-8"
        )
        self.assertIn("risks", next_step(self.target).what)

        (isms / "risks").mkdir()
        (isms / "risks" / "RISK-001-a.md").write_text("---\nid: R\n---\n", encoding="utf-8")
        self.assertIn("POL-001", next_step(self.target).what)

    def test_unfinished_step_quotes_the_first_open_line(self):
        from compliator.guidance import _Snapshot, _unfinished
        from compliator.status import Finding

        findings = [
            Finding("warning", "isms/scope.md", "x", "unfinished", 2, "TODO: what the ISMS covers")
        ]
        step = _unfinished(_Snapshot(self.target, [], None, findings))

        self.assertIn("TODO: what the ISMS covers", step.what)
        self.assertNotIn("more documents", step.what)

    def test_cli_exits_zero_with_findings(self):
        code, out = quietly(main, ["next", "--target", str(self.target)])

        self.assertEqual(code, 0)
        self.assertIn("Next:", out)

    def test_repository_gets_advice_not_a_crash(self):
        root = Path(__file__).resolve().parents[1]
        code, out = quietly(main, ["next", "--target", str(root)])

        self.assertEqual(code, 0)
        self.assertIn("Next:", out)


class TestChecks(unittest.TestCase):
    """Each check fires on its own finding and stays quiet otherwise."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _step(self, check, findings=(), controls=(), config_error=None):
        return check(_Snapshot(self.target, list(controls), config_error, list(findings)))

    def test_findings_based_checks_are_silent_without_findings(self):
        for check in (
            _document_errors,
            _unfinished,
            _coverage,
            _evidence,
            _remaining,
            _awaiting_approval,
        ):
            self.assertIsNone(self._step(check), check.__name__)

    def test_document_errors_name_the_scope_before_other_documents(self):
        findings = [
            Finding("error", "isms/policies/POL-001-a.md", "bad"),
            Finding("error", "isms/scope.md", "worse"),
        ]

        step = self._step(_document_errors, findings)

        self.assertIn("isms/scope.md", step.what)
        self.assertEqual(step.action, "edit isms/scope.md")

    def test_evidence_errors_point_to_verify_and_stale_evidence_to_collect(self):
        stale = Finding("warning", "c1", "stale", "evidence")
        failing = Finding("error", "c2", "tampered", "evidence")

        self.assertIn("make verify", self._step(_evidence, [stale, failing]).action)
        self.assertEqual(self._step(_evidence, [stale]).action, "make collect")

    def test_no_controls_quotes_the_config_error(self):
        step = self._step(_controls, config_error="missing config file: x")

        self.assertIn("missing config file: x", step.why)
        self.assertIsNone(self._step(_controls, controls=[object()]))

    def test_coverage_counts_the_other_gaps(self):
        gaps = [Finding("warning", "soc2:R1", "uncovered", "coverage")] * 3

        self.assertIn("2 more uncovered", self._step(_coverage, gaps).what)

    def test_remaining_warnings_and_drafts_awaiting_approval(self):
        self.assertIn("make status", self._step(_remaining, [Finding("warning", "x", "m")]).action)
        ready = Finding("note", "isms/scope.md", "ready to approve", "ready")
        self.assertIn("approved_by", self._step(_awaiting_approval, [ready]).action)

    def test_partly_written_policies_are_counted(self):
        policies = self.target / "isms" / "policies"
        policies.mkdir(parents=True)
        (policies / "POL-001-a.md").write_text("x", encoding="utf-8")
        (policies / "POL-002-b.md").write_text("x", encoding="utf-8")

        step = self._step(_policies)

        self.assertIn("recommended policies not written", step.what)
        self.assertIsNone(self._step(_foundation_policies))

    def test_no_policies_says_so(self):
        self.assertEqual(self._step(_policies).what, "No policies yet.")

    def test_soa_missing_for_a_declared_framework(self):
        quietly(run_framework, self.target, "soc2")
        quietly(run_framework, self.target, "iso_27001_2022")
        (self.target / "isms/soa.iso_27001_2022.md").unlink()

        self.assertIn("statement of applicability", self._step(_soa).what)

    def test_risks_step_clears_once_a_risk_exists(self):
        self.assertIn("make new-risk", self._step(_risks).action)
        (self.target / "isms/risks").mkdir(parents=True)
        (self.target / "isms/risks/RISK-001-x.md").write_text("x", encoding="utf-8")

        self.assertIsNone(self._step(_risks))


class TestCoverage(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name)
        (self.target / "config/controls").mkdir(parents=True)
        (self.target / "frameworks").mkdir()
        (self.target / "config/sources.yaml").write_text(
            "sources:\n  s:\n    plugin: mock_github\n    options: {fixture: f.json}\n",
            encoding="utf-8",
        )
        (self.target / "config/controls/c.yaml").write_text(
            "control:\n  id: test-c\n  title: T\n  statement: S\n  owner: o\n  frequency: 1d\n"
            "  mappings:\n    soc2: [R1]\nsource: s\nchecks:\n  - description: d\n    must: {path: a, op: equals, value: 1}\n",
            encoding="utf-8",
        )
        quietly(run_framework, self.target, "soc2")

    def tearDown(self):
        self._tmp.cleanup()

    def _catalog(self, complete):
        (self.target / "frameworks/soc2.yaml").write_text(
            f"framework: soc2\ntitle: SOC 2\nversion: '1'\ncomplete: {complete}\nrequirements:\n  R1: one\n  R2: two\n",
            encoding="utf-8",
        )
        project = load_project(self.target / "config")
        return check_coverage(self.target, project.controls, project.catalogs)

    def test_a_complete_catalog_reports_the_uncovered_requirement(self):
        findings = self._catalog("true")

        self.assertEqual([f.subject for f in findings], ["soc2:R2"])

    def test_a_partial_catalog_reports_nothing(self):
        self.assertEqual(self._catalog("false"), [])


if __name__ == "__main__":
    unittest.main()
