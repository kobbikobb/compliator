import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from compliator.__main__ import main
from compliator.guidance import next_step
from compliator.onboarding import Ask, declared_frameworks, run, run_framework


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

        self.assertEqual([f.key for f in declared_frameworks(self.target)], ["iso_27001_2022", "soc2"])
        text = (self.target / "isms/frameworks.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("SOC 2 Trust Services Criteria |"), 1)
        self.assertIn("ISO/IEC 27001:2022 |", text)

    def test_declared_framework_is_not_asked_again_by_init(self):
        quietly(run_framework, self.target, "soc2")
        _, out = quietly(run, self.target, ask=Ask(["n"] * 20))  # decline every document

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
        self.assertIn("make framework", step.do)

    def test_follows_the_build_order(self):
        quietly(run_framework, self.target, "iso_27001_2022")
        self.assertIn("scope", next_step(self.target).what)

        (self.target / "isms/scope.md").write_text("---\nid: S\ntitle: t\nowner: o\nstatus: draft\n---\n", encoding="utf-8")
        self.assertIn("risks", next_step(self.target).what)

    def test_cli_exits_zero_with_findings(self):
        code, out = quietly(main, ["next", "--target", str(self.target)])

        self.assertEqual(code, 0)
        self.assertIn("Next:", out)

    def test_repository_gets_advice_not_a_crash(self):
        root = Path(__file__).resolve().parents[1]
        code, out = quietly(main, ["next", "--target", str(root)])

        self.assertEqual(code, 0)
        self.assertIn("Next:", out)


if __name__ == "__main__":
    unittest.main()
