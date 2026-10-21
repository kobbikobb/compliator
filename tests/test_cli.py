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


class TestCliErrors(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_missing_config_is_a_clean_error_not_a_traceback(self):
        code, _, err = cli("collect", "--config-dir", str(self.target / "nope"))

        self.assertEqual(code, 2)
        self.assertTrue(err.startswith("error:"))

    def test_undecodable_file_is_reported_with_its_path(self):
        isms = self.target / "isms"
        isms.mkdir()
        (isms / "frameworks.md").write_bytes(b"\xff\xfe\x00bad")

        code, _, err = cli("framework", "--target", str(self.target), "--set", "soc2")

        self.assertEqual(code, 2)
        self.assertTrue(err.startswith("error:"))
        self.assertNotIn("Traceback", err)
