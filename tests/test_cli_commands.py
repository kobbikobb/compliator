import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from compliator.__main__ import main


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TestCliCommands(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.evidence = Path(self._tmp.name) / "evidence"
        self.config = str(Path(__file__).resolve().parents[1] / "config")

    def tearDown(self):
        self._tmp.cleanup()

    def test_list_names_every_control(self):
        code, out, _ = cli("list", "--config-dir", self.config)

        self.assertEqual(code, 0)
        self.assertIn("soc2-cc6.1", out)

    def test_collect_then_verify_round_trips(self):
        cli("collect", "--config-dir", self.config, "--evidence-dir", str(self.evidence))

        code, out, _ = cli("verify", str(self.evidence))
        self.assertEqual(code, 0)
        self.assertIn("record(s) verified", out)

        record = next(self.evidence.glob("*/*/MANIFEST.json")).parent
        code, out, _ = cli("verify", str(record))
        self.assertEqual(code, 0)
        self.assertIn("verified files", out)

    def test_bad_as_of_date_is_a_clean_error(self):
        code, _, err = cli("next", "--target", str(self.evidence.parent), "--as-of", "soon")

        self.assertEqual(code, 2)
        self.assertIn("YYYY-MM-DD", err)

    def test_non_directory_target_is_a_clean_error(self):
        code, _, err = cli("next", "--target", str(self.evidence.parent / "missing"))

        self.assertEqual(code, 2)
        self.assertIn("not a directory", err)
