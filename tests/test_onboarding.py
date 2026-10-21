import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import yaml

from compliator.__main__ import main
from compliator.catalog import POLICIES, SUGGESTED_START
from compliator.errors import OnboardingError
from compliator.onboarding import Ask, run, run_new_risk

ROOT = Path(__file__).resolve().parents[1]


def read_document(path):
    """Split a generated document into (front_matter, body, whole text)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path} has no front matter")
    _, _, rest = text.partition("---\n")
    block, sep, body = rest.partition("---\n")
    if not sep:
        raise AssertionError(f"{path} has an unterminated front matter block")
    return yaml.safe_load(block), body, text


def write_answers(directory, **answers):
    path = Path(directory) / "answers.yaml"
    path.write_text(yaml.safe_dump(answers), encoding="utf-8")
    return path


class TestOnboarding(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.target = self.tmp / "instance"

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, **kwargs):
        out = io.StringIO()
        with redirect_stdout(out):
            code = run(self.target, **kwargs)
        return code, out.getvalue()

    # -- scanning, and the two ways a run does nothing ------------------------

    def test_dry_run_asks_nothing_and_writes_nothing(self):
        code, out = self._run(dry_run=True)

        self.assertEqual(code, 0)
        self.assertIn("would write isms/scope.md", out)
        self.assertFalse(self.target.exists(), "dry run must not create the target")

    def test_already_set_up_reports_and_stops(self):
        answers = write_answers(self.tmp, organization="Acme SaaS Co.", policies="all")
        self._run(answers_path=answers)

        code, out = self._run(answers_path=answers, dry_run=True)

        self.assertEqual(code, 0)
        self.assertIn("Already set up", out)
        self.assertNotIn("would write", out)

    def test_declining_everything_is_not_an_error(self):
        answers = write_answers(
            self.tmp,
            create={"scope": False, "frameworks": False, "soa": False, "policies": False},
        )

        code, out = self._run(answers_path=answers)

        self.assertEqual(code, 0)
        self.assertIn("Nothing selected", out)
        self.assertFalse((self.target / "isms").exists())

    # -- what a full run writes ----------------------------------------------

    def test_answers_file_creates_the_suggested_set(self):
        answers = write_answers(
            self.tmp,
            organization="Acme SaaS Co.",
            what_it_does="invoicing for small agencies",
            owner="founder@example.invalid",
            frameworks="iso_27001_2022",
        )

        code, _ = self._run(answers_path=answers)

        self.assertEqual(code, 0)
        scope = self.target / "isms/scope.md"
        self.assertTrue(scope.is_file())
        self.assertTrue((self.target / "isms/frameworks.md").is_file())
        self.assertTrue((self.target / "isms/soa.iso_27001_2022.md").is_file())
        self.assertFalse((self.target / "isms/risks").exists())
        for number in SUGGESTED_START:
            self.assertTrue((self.target / f"isms/policies/{self._policy_name(number)}").is_file())
        for number in (5, 9, 11, 12):
            self.assertFalse((self.target / f"isms/policies/{self._policy_name(number)}").exists())

    def _policy_name(self, number):
        return next(policy.filename for policy in POLICIES if policy.number == number)

    def test_every_generated_document_has_an_owner_and_is_a_draft(self):
        answers = write_answers(self.tmp, owner="founder@example.invalid", policies="all")
        self._run(answers_path=answers)

        documents = sorted((self.target / "isms").rglob("*.md"))
        self.assertEqual(len(documents), 12 + 3)  # 12 policies, scope, SoA, frameworks.md
        for document in documents:
            if document.name == "frameworks.md":
                continue  # a note, not a controlled document - it has no front matter
            front, body, text = read_document(document)
            self.assertEqual(front["owner"], "founder@example.invalid", document.name)
            self.assertIn(front["status"], ("draft", "open"), document.name)
            self.assertNotIn("approved_by", front, document.name)
            self.assertNotIn("last_reviewed", front, document.name)
            self.assertIn("TODO", body, f"{document.name} should be a skeleton")
            self.assertNotIn("$", text, f"{document.name} has an unfilled template placeholder")
            self.assertNotIn("POL-AREA-NNN", text, document.name)

    def test_scope_records_the_organisation_from_the_answers(self):
        answers = write_answers(
            self.tmp, organization="Acme SaaS Co.", what_it_does="invoicing for small agencies"
        )
        self._run(answers_path=answers)

        front, body, _ = read_document(self.target / "isms/scope.md")
        self.assertEqual(front["id"], "SCOPE-001")
        self.assertEqual(front["title"], "ISMS Scope Statement")
        self.assertIn("Acme SaaS Co.", body)
        self.assertIn("invoicing for small agencies", body)

    def test_default_statements_are_marked_for_confirmation_and_follow_the_profile(self):
        answers = write_answers(
            self.tmp, owner="ciso@example.invalid", policies=[1, 3], profile={"contractors": True, "idp": False}
        )
        self._run(answers_path=answers)

        _, body, _ = read_document(self.target / "isms/policies/POL-003-access-control.md")
        self.assertIn("CONFIRM: Multi-factor authentication is required", body)
        self.assertIn("CONFIRM: Contractors and third parties", body)
        self.assertNotIn("single sign-on", body)
        _, body, _ = read_document(self.target / "isms/policies/POL-001-information-security.md")
        self.assertIn("1. CONFIRM: ciso@example.invalid is responsible", body)

    def test_a_policy_without_defaults_keeps_its_todo(self):
        self._run(answers_path=write_answers(self.tmp, policies=[4]))

        _, body, _ = read_document(self.target / "isms/policies/POL-004-change-management.md")
        self.assertIn("TODO: the rules", body)
        self.assertNotIn("1. CONFIRM", body)

    def test_unknown_profile_question_is_refused(self):
        with self.assertRaises(OnboardingError):
            self._run(answers_path=write_answers(self.tmp, profile={"nope": True}))

    def test_new_risk_numbers_on_and_leaves_ratings_as_work_to_do(self):
        with redirect_stdout(io.StringIO()):
            run_new_risk(self.target, "Credential leak reaches production data", today="2026-01-01")
            run_new_risk(self.target, "Supplier outage", today="2026-01-01")

        first = self.target / "isms/risks/RISK-001-credential-leak-reaches-production-data.md"
        front, _, _ = read_document(first)
        self.assertEqual(front["title"], "Credential leak reaches production data")
        self.assertEqual(front["status"], "open")
        for field in ("likelihood", "impact", "inherent", "residual", "treatment"):
            self.assertEqual(front[field], "TODO", f"{field} must not be pre-rated")
        self.assertTrue((self.target / "isms/risks/RISK-002-supplier-outage.md").is_file())

    def test_new_risk_asks_for_the_scenario_and_refuses_an_empty_one(self):
        with redirect_stdout(io.StringIO()):
            run_new_risk(self.target, ask=Ask(["Laptop lost"]))
            with self.assertRaises(OnboardingError):
                run_new_risk(self.target, ask=Ask([""]))

        self.assertTrue((self.target / "isms/risks/RISK-001-laptop-lost.md").is_file())

    # -- framework selection drives the SoA ----------------------------------

    def test_soc2_needs_no_statement_of_applicability(self):
        answers = write_answers(self.tmp, frameworks="soc2")
        code, out = self._run(answers_path=answers)

        self.assertEqual(code, 0)
        self.assertFalse(list((self.target / "isms").glob("soa.*.md")))
        frameworks = (self.target / "isms/frameworks.md").read_text(encoding="utf-8")
        self.assertIn("SOC 2 Trust Services Criteria", frameworks)
        self.assertIn("not required", frameworks)
        # It is not a document waiting to be written, so it must not be reported
        # as one the user declined.
        self.assertIn("No statement of applicability", out)
        self.assertNotIn("soa.iso_27001_2022.md,", out)

    def test_both_frameworks_write_one_soa_and_record_both(self):
        answers = write_answers(self.tmp, frameworks="both")
        self._run(answers_path=answers)

        self.assertTrue((self.target / "isms/soa.iso_27001_2022.md").is_file())
        frameworks = (self.target / "isms/frameworks.md").read_text(encoding="utf-8")
        self.assertIn("ISO/IEC 27001:2022", frameworks)
        self.assertIn("SOC 2 Trust Services Criteria", frameworks)

    def test_no_framework_declared_still_writes_the_rest(self):
        answers = write_answers(self.tmp, frameworks="none")
        self._run(answers_path=answers)

        self.assertTrue((self.target / "isms/scope.md").is_file())
        self.assertFalse(list((self.target / "isms").glob("soa.*.md")))

    def test_policy_selection_accepts_all_none_and_numbers(self):
        for selection, expected in (("all", 12), ("none", 0), ([3, 5], 2)):
            with self.subTest(selection=selection):
                with tempfile.TemporaryDirectory() as fresh:
                    target = Path(fresh) / "instance"
                    answers = write_answers(fresh, policies=selection)
                    with redirect_stdout(io.StringIO()):
                        run(target, answers_path=answers)
                    written = list((target / "isms/policies").glob("POL-*.md"))
                    self.assertEqual(len(written), expected)

    # -- refusals ------------------------------------------------------------

    def test_existing_files_are_never_overwritten(self):
        answers = write_answers(self.tmp, policies="minimal", organization="Acme SaaS Co.")
        self._run(answers_path=answers)
        scope = self.target / "isms/scope.md"
        scope.write_text(scope.read_text(encoding="utf-8") + "\nEDITED BY A HUMAN\n", encoding="utf-8")

        code, out = self._run(answers_path=answers)

        self.assertEqual(code, 0)
        self.assertIn("never overwritten", out)
        self.assertIn("EDITED BY A HUMAN", scope.read_text(encoding="utf-8"))

    def test_unknown_framework_names_the_value(self):
        answers = write_answers(self.tmp, frameworks="iso_9999")

        with self.assertRaises(OnboardingError) as caught:
            self._run(answers_path=answers)

        self.assertIn("iso_9999", str(caught.exception))

    def test_unknown_answers_key_is_refused(self):
        answers = write_answers(self.tmp, framwork="iso")

        with self.assertRaises(OnboardingError) as caught:
            self._run(answers_path=answers)

        self.assertIn("framwork", str(caught.exception))

    def test_policy_number_out_of_range_is_refused(self):
        answers = write_answers(self.tmp, policies=[13])

        with self.assertRaises(OnboardingError):
            self._run(answers_path=answers)

    def test_missing_answers_file_is_refused(self):
        with self.assertRaises(OnboardingError):
            self._run(answers_path=self.tmp / "nope.yaml")

    def test_unrecognised_create_key_is_refused(self):
        answers = write_answers(self.tmp, create={"scopes": False})

        with self.assertRaises(OnboardingError):
            self._run(answers_path=answers)

    def test_cli_reports_failures_with_exit_code_2(self):
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = main(["init", "--target", str(self.target), "--answers", str(self.tmp / "missing.yaml")])

        self.assertEqual(code, 2)
        self.assertIn("answers file not found", err.getvalue())

    def test_interactive_run_derives_the_policies_from_a_few_facts(self):
        script = ["y", "Acme SaaS Co.", "invoicing", "founder@example.invalid", "soc2", "y"]
        script += ["y", "n", "y", "n", "n", "n"]  # idp, contractors, customer data, staff, suppliers, office
        script += [""]                            # accept the derived set

        code, out = self._run(ask=Ask(script))

        self.assertEqual(code, 0)
        self.assertIn("Create isms/scope.md", out)
        self.assertIn("Not needed for you: Acceptable Use, Supplier Management, HR Security, Physical Security", out)
        self.assertTrue((self.target / "isms/policies/POL-003-access-control.md").is_file())
        self.assertFalse((self.target / "isms/policies/POL-005-acceptable-use.md").exists())
        _, body, _ = read_document(self.target / "isms/scope.md")
        self.assertIn("Acme SaaS Co.", body)

    def test_the_answers_can_pull_in_more_policies_or_be_chosen_one_by_one(self):
        script = ["n", "soc2", "y"] + ["y"] * 3 + ["y", "y", "y"] + ["c"]
        script += ["n", "n", "y"] + ["n"] * 13

        self._run(ask=Ask(script))

        self.assertTrue((self.target / "isms/policies/POL-003-access-control.md").is_file())
        self.assertFalse((self.target / "isms/policies/POL-001-information-security.md").exists())

    def test_a_script_that_runs_out_is_reported(self):
        with self.assertRaises(OnboardingError) as caught:
            self._run(ask=Ask([]))

        self.assertIn("ran out", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
