"""Step 6 regression tests for missing / damaged resource messages.

Added after the Step 6 resource tests (plan rows R05, R07, R08) found that
  * a corrupt GA parameter file gave an error that did not say what to do, and
  * a missing Step 7 or benchmark CSV showed the raw exception, which contains
    the full local file path.

Run from the repository root:

    python -m unittest discover -s src -p "test_step6_resource_messages.py" -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    import streamlit as st
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None

import product_inference as pi  # noqa: E402

APP = str(ROOT / "app" / "app.py")
GOOD = json.loads((ROOT / "results" / "step6" / "ga_best_params.json")
                  .read_text())


class GaFileMessageTests(unittest.TestCase):
    def load_text(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ga_best_params.json"
            path.write_text(text)
            with self.assertRaises(pi.ControllerLoadError) as caught:
                pi.load_ga_params(path)
        return str(caught.exception)

    def assert_actionable(self, message):
        self.assertIn("ga_best_params.json", message)
        self.assertIn("Restore results/step6/ga_best_params.json", message)
        self.assertNotIn("Expecting property name", message)  # raw JSON text

    def test_invalid_json_says_what_to_do(self):
        message = self.load_text("{not json")
        self.assertIn("unreadable or incomplete", message)
        self.assert_actionable(message)

    def test_incomplete_parameters_say_what_to_do(self):
        data = dict(GOOD)
        data["parameters"] = {"t1": 24.0}
        self.assert_actionable(self.load_text(json.dumps(data)))

    def test_non_finite_parameter_says_what_to_do(self):
        data = dict(GOOD)
        data["parameters"] = dict(GOOD["parameters"], t1=float("nan"))
        self.assert_actionable(self.load_text(json.dumps(data)))

    def test_wrong_temperature_order_says_what_to_do(self):
        data = dict(GOOD)
        data["parameters"] = dict(GOOD["parameters"], t1=40.0)
        self.assert_actionable(self.load_text(json.dumps(data)))


@unittest.skipIf(AppTest is None, "streamlit is not installed")
class CsvTabMessageTests(unittest.TestCase):
    def test_missing_csv_errors_show_no_local_path_and_name_the_file(self):
        secret = "/very/secret/local/folder"
        error = FileNotFoundError(f"[Errno 2] No such file: '{secret}/x.csv'")
        st.cache_data.clear()
        st.cache_resource.clear()
        with mock.patch("pandas.read_csv", side_effect=error):
            at = AppTest.from_file(APP, default_timeout=60).run()
        st.cache_data.clear()
        self.assertEqual(len(at.exception), 0)
        messages = [e.value for e in at.error]
        self.assertEqual(len(messages), 2)
        self.assertTrue(all(secret not in m for m in messages))
        self.assertTrue(any("results/step7/" in m for m in messages))
        self.assertTrue(any("campus_energy_benchmark.csv" in m
                            for m in messages))
        # the Recommendation tab still works
        at.selectbox(key="controller_choice").set_value("Baseline").run()
        at.button[0].click().run()
        self.assertEqual(len(at.exception), 0)
        metrics = [m.value for m in at.metric]
        self.assertEqual(metrics, ["50.00 %", "Medium", "Normal"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
