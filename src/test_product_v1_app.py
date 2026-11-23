"""Interface-level tests for app/app.py using Streamlit's AppTest harness.

These drive the real application script in-process (no browser), so they
check form -> validation -> controller -> displayed result. They complement,
and do not replace, manual testing in a browser.

Run from the repository root:

    python -m unittest discover -s src -p "test_*.py" -v
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    import streamlit as st
    from streamlit.testing.v1 import AppTest
except ImportError:  # Streamlit is only needed for the interface tests.
    AppTest = None

import product_inference as pi  # noqa: E402
from fuzzy_controller import fuzzy_controller  # noqa: E402
from baseline_controller import baseline_controller  # noqa: E402

APP = str(ROOT / "app" / "app.py")
COMPARE = "Compare all three controllers"


@unittest.skipIf(AppTest is None, "streamlit is not installed")
class AppInterfaceTests(unittest.TestCase):

    def setUp(self):
        st.cache_resource.clear()
        self.at = AppTest.from_file(APP, default_timeout=60).run()
        self.assertEqual(len(self.at.exception), 0)

    def fill(self, **values):
        for key, value in values.items():
            if key in ("tariff_level", "controller_choice"):
                self.at.selectbox(key=key).set_value(value)
            else:
                self.at.text_input(key=key).set_value(value)
        return self

    @staticmethod
    def normal(**overrides):
        return {"temperature_c": "25", "humidity_pct": "55",
                "occupancy_count": "50", **overrides}

    def select(self, controller):
        """Changing the selector renames the button, so rerun before clicking."""
        self.at.selectbox(key="controller_choice").set_value(controller).run()

    def submit(self):
        self.at.button[0].click().run()
        return self.at

    def shown_results(self):
        values = [m.value for m in self.at.metric]
        return [values[i:i + 3] for i in range(0, len(values), 3)]

    def error_text(self):
        return " ".join(e.value for e in self.at.error) + " " + " ".join(
            m.value for m in self.at.markdown if m.value.startswith("- "))

    def test_page_loads_with_notice_form_and_sections(self):
        self.assertEqual(
            [t.label for t in self.at.tabs],
            ["Recommendation", "Evaluation results (synthetic)",
             "Campus energy benchmark", "About & limitations"],
        )
        self.assertEqual(len(self.at.warning), 1)
        self.assertIn("not HVAC commands", self.at.warning[0].value)
        self.assertEqual(self.at.button[0].label, "Generate Recommendation")
        self.assertEqual(
            [self.at.text_input(key=k).value for k in
             ("temperature_c", "humidity_pct", "occupancy_count")],
            ["25", "55", "50"],
        )

    def test_valid_submission_matches_direct_baseline_call(self):
        self.fill(temperature_c="36", humidity_pct="85", occupancy_count="45",
                  tariff_level="medium")
        self.submit()
        cooling, fan, action = baseline_controller(36, 85, 45, "medium")
        self.assertEqual(self.shown_results(), [
            [f"{cooling:.2f} %", fan.capitalize(), action.capitalize()]])
        self.assertEqual(len(self.at.error), 0)

    def test_fuzzy_and_ga_submission_match_direct_calls(self):
        row = pd.Series({"temperature_c": 35.2, "humidity_pct": 71.3,
                         "occupancy_count": 57, "tariff_level": "low"})
        ga = pi.load_ga_params()
        expected = {
            "Fuzzy": fuzzy_controller(row),
            "GA-optimised Fuzzy": fuzzy_controller(row, params=ga),
        }
        for label, out in expected.items():
            with self.subTest(controller=label):
                self.fill(temperature_c="35.2", humidity_pct="71.3",
                          occupancy_count="57", tariff_level="low")
                self.select(label)
                self.submit()
                self.assertEqual(self.shown_results(), [[
                    f"{out['cooling_pct']:.2f} %", out["fan_level"].capitalize(),
                    "Normal"]])

    def test_compare_mode_shows_all_three_for_identical_inputs(self):
        self.fill(temperature_c="35.2", humidity_pct="71.3",
                  occupancy_count="57", tariff_level="high")
        self.select(COMPARE)
        self.assertEqual(self.at.button[0].label, "Compare Controllers")
        self.submit()
        shown = self.shown_results()
        self.assertEqual(len(shown), 3)
        expected = pi.recommend_all({
            "temperature_c": "35.2", "humidity_pct": "71.3",
            "occupancy_count": "57", "tariff_level": "high"})
        for got, result in zip(shown, expected):
            self.assertEqual(got, [f"{result['cooling_pct']:.2f} %",
                                   result["fan_level"].capitalize(),
                                   "Avoid Peak"])
        self.assertEqual(len({row[0] for row in shown}), 3)

    def test_invalid_inputs_show_field_errors_and_no_recommendation(self):
        cases = [
            ("temperature_c", "46", "Temperature"),
            ("temperature_c", "17", "Temperature"),
            ("humidity_pct", "101", "Humidity"),
            ("humidity_pct", "19", "Humidity"),
            ("occupancy_count", "-1", "Occupancy"),
            ("occupancy_count", "101", "Occupancy"),
            ("occupancy_count", "20.5", "whole number"),
            ("temperature_c", "abc", "enter a number"),
            ("humidity_pct", "", "enter a value"),
            ("temperature_c", "nan", "finite"),
            ("occupancy_count", "inf", "finite"),
        ]
        for field, value, expected_text in cases:
            with self.subTest(field=field, value=value):
                self.fill(**self.normal(**{field: value}))
                self.submit()
                self.assertEqual(len(self.at.exception), 0)
                self.assertEqual(self.shown_results(), [])
                self.assertIn("invalid", self.at.error[0].value)
                self.assertIn(expected_text, self.error_text())

    def test_invalid_submission_replaces_an_earlier_result(self):
        self.submit()
        self.assertEqual(len(self.shown_results()), 1)
        self.fill(temperature_c="abc").submit()
        self.assertEqual(self.shown_results(), [])

    def test_app_recovers_after_correction(self):
        self.fill(humidity_pct="150").submit()
        self.assertEqual(self.shown_results(), [])
        self.fill(humidity_pct="55").submit()
        self.assertEqual(len(self.shown_results()), 1)
        self.assertEqual(len(self.at.error), 0)

    def test_boundary_inputs_return_results(self):
        for field, values in (("temperature_c", ("18", "45")),
                              ("humidity_pct", ("20", "100")),
                              ("occupancy_count", ("0", "100"))):
            for value in values:
                with self.subTest(field=field, value=value):
                    self.fill(**self.normal(**{field: value}))
                    self.submit()
                    self.assertEqual(len(self.at.error), 0)
                    self.assertEqual(len(self.shown_results()), 1)

    def test_empty_room_shows_off_fan(self):
        self.fill(occupancy_count="0").submit()
        self.assertEqual(self.shown_results(), [["0.00 %", "Off", "Normal"]])

    def test_missing_ga_file_shows_clear_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(pi, "GA_PARAMS_PATH", Path(tmp) / "gone.json"):
                self.select("GA-optimised Fuzzy")
                self.submit()
                self.assertEqual(len(self.at.exception), 0)
                self.assertEqual(self.shown_results(), [])
                self.assertIn("could not be loaded", self.at.error[0].value)
                self.assertIn("not found", self.at.error[0].value)
                # Baseline still works without the GA file.
                self.select("Baseline")
                self.submit()
                self.assertEqual(len(self.shown_results()), 1)

    def test_consistency_expander_reports_matches(self):
        self.select(COMPARE)
        self.submit()
        frames = [df.value for df in self.at.dataframe]
        check = next(f for f in frames if "Direct controller call" in f.columns)
        self.assertEqual(list(check["Match"]), ["✅ yes"] * 3)

    def test_csv_download_is_offered_after_a_result(self):
        self.assertEqual(len(self.at.get("download_button")), 0)
        self.submit()
        self.assertEqual(len(self.at.get("download_button")), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
