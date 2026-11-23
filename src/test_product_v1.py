"""Automated tests for the SC01 Product V1 inference layer.

Run from the repository root:

    python -m unittest discover -s src -p "test_*.py" -v

These tests check input validation, controller selection, output schema and
agreement with the existing controllers. They do NOT show that the
controllers save energy or improve comfort, and they do not replace the
manual browser checks of the interface.
"""

import csv
import io
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import product_inference as pi  # noqa: E402
from baseline_controller import TEST_CASES, baseline_controller  # noqa: E402
from fuzzy_controller import fuzzy_controller  # noqa: E402


def normal_input():
    """A fresh valid input for every test (used only as a test case)."""
    return {
        "temperature_c": "25",
        "humidity_pct": "55",
        "occupancy_count": "50",
        "tariff_level": "medium",
    }


class NormalInputTests(unittest.TestCase):

    def test_normal_input_is_accepted_and_cleaned(self):
        clean = pi.validate_inputs(normal_input())
        self.assertEqual(clean, {
            "temperature_c": 25.0, "humidity_pct": 55.0,
            "occupancy_count": 50, "tariff_level": "medium",
        })
        self.assertIsInstance(clean["occupancy_count"], int)

    def test_numbers_and_numeric_strings_both_work(self):
        as_numbers = {"temperature_c": 25, "humidity_pct": 55.0,
                      "occupancy_count": 50.0, "tariff_level": "medium"}
        self.assertEqual(
            pi.validate_inputs(as_numbers), pi.validate_inputs(normal_input())
        )

    def test_whitespace_and_tariff_case_are_normalised_not_guessed(self):
        values = normal_input()
        values.update(temperature_c=" 25 ", tariff_level=" High ")
        clean = pi.validate_inputs(values)
        self.assertEqual(clean["temperature_c"], 25.0)
        self.assertEqual(clean["tariff_level"], "high")


class BoundaryTests(unittest.TestCase):
    """Each limit is tested on its own with the other fields normal."""

    def check_accepts(self, field, value):
        values = normal_input()
        values[field] = value
        self.assertEqual(
            pi.validate_inputs(values)[field],
            float(value) if field != "occupancy_count" else int(value),
        )

    def test_temperature_limits(self):
        for value in ("18", "45"):
            self.check_accepts("temperature_c", value)

    def test_humidity_limits(self):
        for value in ("20", "100"):
            self.check_accepts("humidity_pct", value)

    def test_occupancy_limits(self):
        for value in ("0", "100"):
            self.check_accepts("occupancy_count", value)

    def test_every_tariff_is_accepted(self):
        for tariff in pi.TARIFFS:
            values = normal_input()
            values["tariff_level"] = tariff
            self.assertEqual(pi.validate_inputs(values)["tariff_level"], tariff)

    def test_boundary_inputs_give_controller_output(self):
        for field, values in (
            ("temperature_c", ("18", "45")),
            ("humidity_pct", ("20", "100")),
            ("occupancy_count", ("0", "100")),
        ):
            for value in values:
                data = normal_input()
                data[field] = value
                for result in pi.recommend_all(data):
                    self.assertIn(result["fan_level"], pi.FAN_LEVELS)


class InvalidInputTests(unittest.TestCase):

    def assert_field_error(self, field, value, controller="fuzzy"):
        values = normal_input()
        values[field] = value
        with self.assertRaises(pi.InputValidationError) as caught:
            pi.recommend(values, controller)
        self.assertIn(field, caught.exception.errors)
        self.assertEqual(
            list(caught.exception.errors), [field],
            "only the changed field should be reported",
        )
        self.assertIsInstance(caught.exception, ValueError)

    def test_temperature_out_of_range(self):
        for value in ("17.9", "-5", "45.1", "100"):
            self.assert_field_error("temperature_c", value)

    def test_humidity_out_of_range(self):
        for value in ("19.9", "0", "100.1", "150", "-1"):
            self.assert_field_error("humidity_pct", value)

    def test_occupancy_out_of_range(self):
        for value in ("-1", "101", "1000"):
            self.assert_field_error("occupancy_count", value)

    def test_occupancy_must_be_a_whole_number(self):
        for value in ("20.5", "0.1", 99.9):
            self.assert_field_error("occupancy_count", value)

    def test_unknown_tariff(self):
        for value in ("urgent", "peak", "very high", "1", 3, ["low"]):
            self.assert_field_error("tariff_level", value)

    def test_text_where_number_expected(self):
        for field in ("temperature_c", "humidity_pct", "occupancy_count"):
            for value in ("abc", "25 C", "1_0", "twenty", True):
                self.assert_field_error(field, value)

    def test_nan_and_infinity(self):
        for field in ("temperature_c", "humidity_pct", "occupancy_count"):
            for value in ("nan", "NaN", "inf", "-inf", "Infinity",
                          float("nan"), float("inf")):
                self.assert_field_error(field, value)

    def test_blank_and_none_values(self):
        for field in pi.INPUT_FIELDS:
            for value in ("", "   ", None):
                self.assert_field_error(field, value)

    def test_missing_keys(self):
        for field in pi.INPUT_FIELDS:
            values = normal_input()
            del values[field]
            with self.assertRaises(pi.InputValidationError) as caught:
                pi.recommend(values)
            self.assertIn(field, caught.exception.errors)

    def test_all_problems_reported_together(self):
        values = {"temperature_c": "abc", "humidity_pct": "101",
                  "occupancy_count": "", "tariff_level": "urgent"}
        with self.assertRaises(pi.InputValidationError) as caught:
            pi.validate_inputs(values)
        self.assertEqual(set(caught.exception.errors), set(pi.INPUT_FIELDS))

    def test_error_messages_name_the_field_and_valid_range(self):
        errors = {}
        for field, value in (("temperature_c", "46"), ("humidity_pct", "10"),
                             ("occupancy_count", "101")):
            values = normal_input()
            values[field] = value
            try:
                pi.validate_inputs(values)
            except pi.InputValidationError as error:
                errors[field] = error.errors[field]
        self.assertIn("18-45", errors["temperature_c"])
        self.assertIn("20-100", errors["humidity_pct"])
        self.assertIn("0-100", errors["occupancy_count"])

    def test_non_mapping_input_is_rejected(self):
        for bad in (None, "25", 25, [25, 55, 50, "low"]):
            with self.assertRaises(pi.InputValidationError):
                pi.validate_inputs(bad)

    def test_invalid_input_never_reaches_a_controller(self):
        values = normal_input()
        values["temperature_c"] = "nan"
        with mock.patch.object(pi, "_run_controller") as run:
            with self.assertRaises(pi.InputValidationError):
                pi.recommend(values, "baseline")
            with self.assertRaises(pi.InputValidationError):
                pi.recommend_all(values)
            run.assert_not_called()

    def test_invalid_values_are_not_replaced_by_defaults(self):
        values = normal_input()
        values["humidity_pct"] = "abc"
        with self.assertRaises(pi.InputValidationError):
            pi.recommend(values)


class OutputSchemaTests(unittest.TestCase):

    def test_result_schema_and_ranges(self):
        for controller in pi.CONTROLLERS:
            result = pi.recommend(normal_input(), controller)
            self.assertEqual(
                list(result), list(pi.OUTPUT_COLUMNS),
            )
            self.assertEqual(result["controller"], controller)
            self.assertIsInstance(result["cooling_pct"], float)
            self.assertTrue(0 <= result["cooling_pct"] <= 100)
            self.assertIn(result["fan_level"], pi.FAN_LEVELS)
            self.assertIn(result["energy_action"], pi.ENERGY_ACTIONS)
            self.assertIn("Not an HVAC command", result["notice"])

    def test_outputs_stay_valid_across_the_input_domain(self):
        for temp in (18, 24, 30, 36, 45):
            for humidity in (20, 60, 80, 100):
                for occupancy in (0, 1, 50, 100):
                    for tariff in pi.TARIFFS:
                        values = {"temperature_c": temp,
                                  "humidity_pct": humidity,
                                  "occupancy_count": occupancy,
                                  "tariff_level": tariff}
                        for result in pi.recommend_all(values):
                            self.assertTrue(
                                0 <= result["cooling_pct"] <= 100)
                            self.assertIn(result["fan_level"], pi.FAN_LEVELS)
                            self.assertIn(
                                result["energy_action"], pi.ENERGY_ACTIONS)

    def test_empty_room_gives_zero_cooling_and_fan_off(self):
        values = normal_input()
        values["occupancy_count"] = "0"
        for result in pi.recommend_all(values):
            self.assertEqual(result["cooling_pct"], 0.0)
            self.assertEqual(result["fan_level"], "off")

    def test_high_tariff_gives_avoid_peak_and_others_normal(self):
        for tariff, expected in (("low", "normal"), ("medium", "normal"),
                                 ("high", "avoid_peak")):
            values = normal_input()
            values["tariff_level"] = tariff
            for result in pi.recommend_all(values):
                self.assertEqual(result["energy_action"], expected)

    def test_csv_export_contains_inputs_controller_outputs_and_notice(self):
        results = pi.recommend_all(normal_input())
        rows = list(csv.DictReader(io.StringIO(pi.results_to_csv(results))))
        self.assertEqual(len(rows), 3)
        self.assertEqual(list(rows[0]), list(pi.OUTPUT_COLUMNS))
        self.assertEqual([r["controller"] for r in rows], list(pi.CONTROLLERS))
        self.assertEqual(float(rows[1]["cooling_pct"]), results[1]["cooling_pct"])
        self.assertEqual(rows[0]["temperature_c"], "25.0")
        self.assertIn("Not an HVAC command", rows[2]["notice"])


class ControllerSelectionTests(unittest.TestCase):

    def test_each_controller_is_selected_by_name(self):
        values = {"temperature_c": 35.2, "humidity_pct": 71.3,
                  "occupancy_count": 57, "tariff_level": "low"}
        results = {name: pi.recommend(values, name) for name in pi.CONTROLLERS}
        self.assertEqual({n: r["controller"] for n, r in results.items()},
                         {n: n for n in pi.CONTROLLERS})
        # The three methods genuinely differ for this input.
        cooling = {r["cooling_pct"] for r in results.values()}
        self.assertEqual(len(cooling), 3)

    def test_unknown_controller_is_rejected(self):
        for name in ("neural", "", None, "Fuzzy "):
            with self.assertRaises(ValueError):
                pi.recommend(normal_input(), name)

    def test_recommend_all_returns_all_three_in_order(self):
        results = pi.recommend_all(normal_input())
        self.assertEqual([r["controller"] for r in results],
                         list(pi.CONTROLLERS))
        self.assertEqual(
            {(r["temperature_c"], r["humidity_pct"], r["occupancy_count"],
              r["tariff_level"]) for r in results},
            {(25.0, 55.0, 50, "medium")},
        )


class ConsistencyWithExistingControllersTests(unittest.TestCase):
    """The layer must return exactly what the existing controllers return."""

    @classmethod
    def setUpClass(cls):
        cls.ga_params = json.loads(
            (ROOT / "results" / "step6" / "ga_best_params.json")
            .read_text(encoding="utf-8")
        )["parameters"]

    def direct(self, values):
        row = pd.Series(values)
        return {
            "baseline": tuple(baseline_controller(
                values["temperature_c"], values["humidity_pct"],
                values["occupancy_count"], values["tariff_level"])),
            "fuzzy": tuple(fuzzy_controller(row)[
                ["cooling_pct", "fan_level", "energy_action"]]),
            "ga_fuzzy": tuple(fuzzy_controller(row, params=self.ga_params)[
                ["cooling_pct", "fan_level", "energy_action"]]),
        }

    def test_layer_matches_direct_calls(self):
        cases = [normal_input()]
        cases += [{k: case[k] for k in pi.INPUT_FIELDS} for case in TEST_CASES]
        for extra in ({"temperature_c": 18, "humidity_pct": 20,
                       "occupancy_count": 0, "tariff_level": "low"},
                      {"temperature_c": 45, "humidity_pct": 100,
                       "occupancy_count": 100, "tariff_level": "high"}):
            cases.append(extra)
        for values in cases:
            clean = pi.validate_inputs(values)
            expected = self.direct(clean)
            for result in pi.recommend_all(values):
                got = (result["cooling_pct"], result["fan_level"],
                       result["energy_action"])
                self.assertEqual(got, expected[result["controller"]],
                                 msg=f"{result['controller']} {values}")

    def test_baseline_layer_reproduces_step1_expected_outputs(self):
        for case in TEST_CASES:
            values = {k: case[k] for k in pi.INPUT_FIELDS}
            result = pi.recommend(values, "baseline")
            self.assertEqual(
                (result["cooling_pct"], result["fan_level"],
                 result["energy_action"]),
                case["expected"], msg=case["scenario_id"],
            )

    def test_layer_matches_saved_step7_evaluation_sample(self):
        # Fan level and energy action exactly; cooling within 0.01 (a value on
        # a rounding boundary can differ by 0.01 between Python versions).
        saved = pd.read_csv(ROOT / "results/step7/three_controller_comparison.csv")
        scenarios = pd.read_csv(ROOT / "data/processed/cleaned_input.csv")
        sample = scenarios.sample(n=300, random_state=7).index
        for index in sample:
            scenario, row = scenarios.loc[index], saved.loc[index]
            self.assertEqual(scenario["scenario_id"], row["scenario_id"])
            values = {k: scenario[k] for k in pi.INPUT_FIELDS}
            for result in pi.recommend_all(values):
                name = result["controller"]
                self.assertEqual(result["fan_level"], row[f"{name}_fan_level"])
                self.assertEqual(result["energy_action"],
                                 row[f"{name}_energy_action"])
                self.assertAlmostEqual(
                    result["cooling_pct"], row[f"{name}_cooling_pct"],
                    delta=0.0100001,
                )


class SavedGaParametersTests(unittest.TestCase):

    def test_loaded_params_equal_the_saved_file(self):
        saved = json.loads((ROOT / "results/step6/ga_best_params.json")
                           .read_text(encoding="utf-8"))["parameters"]
        self.assertEqual(pi.load_ga_params(), {k: float(saved[k]) for k in saved})

    def test_ga_controller_uses_saved_params_not_plain_fuzzy(self):
        values = normal_input()
        fuzzy = pi.recommend(values, "fuzzy")
        ga = pi.recommend(values, "ga_fuzzy")
        self.assertNotEqual(fuzzy["cooling_pct"], ga["cooling_pct"])
        expected = fuzzy_controller(
            pd.Series(pi.validate_inputs(values)), params=pi.load_ga_params()
        )["cooling_pct"]
        self.assertEqual(ga["cooling_pct"], expected)

    def test_missing_params_file_raises_and_does_not_fall_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "absent.json"
            with mock.patch.object(pi, "GA_PARAMS_PATH", missing):
                with self.assertRaises(pi.ControllerLoadError) as caught:
                    pi.recommend(normal_input(), "ga_fuzzy")
                self.assertIn("not found", str(caught.exception))
                with self.assertRaises(pi.ControllerLoadError):
                    pi.recommend_all(normal_input())
                # The other controllers are unaffected by the missing file.
                self.assertEqual(
                    pi.recommend(normal_input(), "baseline")["controller"],
                    "baseline",
                )

    def write_params(self, tmp, content):
        path = Path(tmp) / "params.json"
        path.write_text(content, encoding="utf-8")
        return path

    def test_corrupt_incomplete_or_invalid_params_file_raises(self):
        good = json.loads((ROOT / "results/step6/ga_best_params.json")
                          .read_text(encoding="utf-8"))
        incomplete = {"parameters": {"t1": 27.0}}
        disordered = json.loads(json.dumps(good))
        disordered["parameters"]["t1"] = 40.0
        non_numeric = json.loads(json.dumps(good))
        non_numeric["parameters"]["t2"] = "warm"
        for content in ("not json{", "{}", json.dumps(incomplete),
                        json.dumps(disordered), json.dumps(non_numeric)):
            with tempfile.TemporaryDirectory() as tmp:
                path = self.write_params(tmp, content)
                with self.assertRaises(pi.ControllerLoadError):
                    pi.load_ga_params(path)

    def test_inference_does_not_import_or_run_the_ga_optimiser(self):
        pi.recommend_all(normal_input())
        self.assertNotIn("ga_tune_fuzzy", sys.modules)


class ControllerImportFailureTests(unittest.TestCase):

    def test_import_failure_becomes_a_clear_controller_load_error(self):
        with mock.patch.object(
            pi, "_load_controller_functions",
            side_effect=pi.ControllerLoadError("could not be imported"),
        ):
            with self.assertRaises(pi.ControllerLoadError):
                pi.recommend(normal_input(), "baseline")


if __name__ == "__main__":
    unittest.main(verbosity=2)
