import unittest
from datetime import date

from compliator.config import Check
from compliator.errors import CompliatorError, EmptyPopulationError
from compliator.evaluate import Must, Population, evaluate_check, resolve_path


def check(op, path, value=None, population=None):
    pop = (
        Population(path=population["path"], where=population.get("where", {}))
        if population
        else None
    )
    return Check(description=f"test {op}", population=pop, must=Must(path=path, op=op, value=value))


AS_OF = date(2026, 10, 17)


class TestResolvePath(unittest.TestCase):
    def test_nested(self):
        self.assertEqual(resolve_path({"a": {"b": {"c": 1}}}, "a.b.c"), 1)

    def test_missing_returns_none(self):
        self.assertIsNone(resolve_path({"a": {}}, "a.b.c"))
        self.assertIsNone(resolve_path({}, "a"))

    def test_non_mapping_stops(self):
        self.assertIsNone(resolve_path({"a": [1, 2]}, "a.b"))


class TestPopulationOps(unittest.TestCase):
    def test_all_equal_pass_and_fail(self):
        raw = {"items": [{"v": 1}, {"v": 1}]}
        result = evaluate_check(raw, check("all_equal", "v", 1, {"path": "items"}), AS_OF)
        self.assertTrue(result.passed)
        self.assertEqual(result.observed, [1, 1])

        raw = {"items": [{"v": 1}, {"v": 2}]}
        result = evaluate_check(raw, check("all_equal", "v", 1, {"path": "items"}), AS_OF)
        self.assertFalse(result.passed)
        self.assertIn("1 of 2", result.detail)

    def test_exists_rejects_nulls(self):
        raw = {"items": [{"v": "x"}, {"v": None}, {"v": ""}]}
        result = evaluate_check(raw, check("exists", "v", population={"path": "items"}), AS_OF)
        self.assertFalse(result.passed)
        self.assertIn("missing", result.detail)

    def test_exists_all_present(self):
        raw = {"items": [{"v": "x"}, {"v": "y"}]}
        self.assertTrue(evaluate_check(raw, check("exists", "v", population={"path": "items"}), AS_OF).passed)

    def test_date_within_days(self):
        raw = {"items": [{"d": "2026-10-01"}, {"d": "2026-01-01"}]}
        self.assertTrue(evaluate_check(raw, check("date_within_days", "d", 365, {"path": "items"}), AS_OF).passed)
        result = evaluate_check(raw, check("date_within_days", "d", 30, {"path": "items"}), AS_OF)
        self.assertFalse(result.passed)

    def test_date_null_fails(self):
        raw = {"items": [{"d": "2026-10-01"}, {"d": None}]}
        result = evaluate_check(raw, check("date_within_days", "d", 365, {"path": "items"}), AS_OF)
        self.assertFalse(result.passed)
        self.assertIn("null date", result.detail)

    def test_date_future_fails(self):
        raw = {"items": [{"d": "2027-01-01"}]}
        result = evaluate_check(raw, check("date_within_days", "d", 365, {"path": "items"}), AS_OF)
        self.assertFalse(result.passed)
        self.assertIn("future", result.detail)

    def test_min_gte(self):
        raw = {"items": [{"n": 2}, {"n": 1}]}
        self.assertTrue(evaluate_check(raw, check("min_gte", "n", 1, {"path": "items"}), AS_OF).passed)
        result = evaluate_check(raw, check("min_gte", "n", 2, {"path": "items"}), AS_OF)
        self.assertFalse(result.passed)

    def test_min_gte_null_fails(self):
        raw = {"items": [{"n": 2}, {"n": None}]}
        result = evaluate_check(raw, check("min_gte", "n", 1, {"path": "items"}), AS_OF)
        self.assertFalse(result.passed)
        self.assertIn("null", result.detail)

    def test_population_count_gte(self):
        raw = {"items": [{"v": 1}, {"v": 2}]}
        self.assertTrue(evaluate_check(raw, check("count_gte", "v", 2, {"path": "items"}), AS_OF).passed)
        self.assertFalse(evaluate_check(raw, check("count_gte", "v", 3, {"path": "items"}), AS_OF).passed)

    def test_where_filter(self):
        raw = {"items": [{"env": "prod", "v": True}, {"env": "dev", "v": False}]}
        cfg = check("all_equal", "v", True, {"path": "items", "where": {"env": "prod"}})
        self.assertTrue(evaluate_check(raw, cfg, AS_OF).passed)
        self.assertEqual(evaluate_check(raw, cfg, AS_OF).population_size, 1)

    def test_empty_population_is_error_not_pass(self):
        raw = {"items": [{"env": "dev"}]}
        cfg = check("all_equal", "v", True, {"path": "items", "where": {"env": "prod"}})
        with self.assertRaises(EmptyPopulationError):
            evaluate_check(raw, cfg, AS_OF)

    def test_missing_population_path_is_error(self):
        raw = {"other": []}
        with self.assertRaises(CompliatorError):
            evaluate_check(raw, check("all_equal", "v", 1, {"path": "items"}), AS_OF)

    def test_non_list_population_is_error(self):
        raw = {"items": {"not": "a list"}}
        with self.assertRaises(CompliatorError):
            evaluate_check(raw, check("all_equal", "v", 1, {"path": "items"}), AS_OF)


class TestScalarOps(unittest.TestCase):
    def test_equals(self):
        raw = {"cfg": {"enabled": True}}
        self.assertTrue(evaluate_check(raw, check("equals", "cfg.enabled", True), AS_OF).passed)
        self.assertFalse(evaluate_check(raw, check("equals", "cfg.enabled", False), AS_OF).passed)

    def test_gte(self):
        raw = {"cfg": {"retention": 400}}
        self.assertTrue(evaluate_check(raw, check("gte", "cfg.retention", 365), AS_OF).passed)
        self.assertFalse(evaluate_check(raw, check("gte", "cfg.retention", 401), AS_OF).passed)

    def test_gte_on_null_fails(self):
        raw = {"cfg": {}}
        result = evaluate_check(raw, check("gte", "cfg.retention", 365), AS_OF)
        self.assertFalse(result.passed)

    def test_count_gte_scalar(self):
        raw = {"users": [1, 2, 3]}
        self.assertTrue(evaluate_check(raw, check("count_gte", "users", 3), AS_OF).passed)
        self.assertFalse(evaluate_check(raw, check("count_gte", "users", 4), AS_OF).passed)


if __name__ == "__main__":
    unittest.main()
