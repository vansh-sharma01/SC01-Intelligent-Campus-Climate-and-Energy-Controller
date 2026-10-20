import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from validate_data import validate_data
from fuzzy_controller import fuzzy_controller
from baseline_controller import baseline_controller


class Step4RequirementsTests(unittest.TestCase):

    def validate_frame(self, frame):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.csv"
            frame.to_csv(path, index=False)
            with contextlib.redirect_stdout(io.StringIO()):
                return validate_data(path)

    def test_valid_boundary_inputs_are_accepted(self):
        rows = []
        for i, (temp, humidity, occupancy) in enumerate([
            (18, 0, 0),
            (45, 100, 100),
            (24, 50, 20),
        ]):
            rows.append({
                "scenario_id": f"BOUNDARY-{i}",
                "temperature_c": temp,
                "humidity_pct": humidity,
                "occupancy_count": occupancy,
                "tariff_level": "medium",
            })
        self.assertTrue(self.validate_frame(pd.DataFrame(rows)))

    def test_invalid_temperature_is_rejected(self):
        frame = pd.DataFrame([{
            "scenario_id": "BAD-TEMP",
            "temperature_c": 46,
            "humidity_pct": 50,
            "occupancy_count": 20,
            "tariff_level": "low",
        }])
        with self.assertRaises(ValueError):
            self.validate_frame(frame)

    def test_invalid_humidity_is_rejected(self):
        frame = pd.DataFrame([{
            "scenario_id": "BAD-HUMIDITY",
            "temperature_c": 25,
            "humidity_pct": 101,
            "occupancy_count": 20,
            "tariff_level": "low",
        }])
        with self.assertRaises(ValueError):
            self.validate_frame(frame)

    def test_negative_occupancy_is_rejected(self):
        frame = pd.DataFrame([{
            "scenario_id": "BAD-OCCUPANCY",
            "temperature_c": 25,
            "humidity_pct": 50,
            "occupancy_count": -1,
            "tariff_level": "low",
        }])
        with self.assertRaises(ValueError):
            self.validate_frame(frame)

    def test_invalid_tariff_is_rejected(self):
        frame = pd.DataFrame([{
            "scenario_id": "BAD-TARIFF",
            "temperature_c": 25,
            "humidity_pct": 50,
            "occupancy_count": 20,
            "tariff_level": "urgent",
        }])
        with self.assertRaises(ValueError):
            self.validate_frame(frame)

    def test_missing_input_is_rejected(self):
        frame = pd.DataFrame([{
            "scenario_id": "BAD-MISSING",
            "temperature_c": 25,
            "humidity_pct": None,
            "occupancy_count": 20,
            "tariff_level": "medium",
        }])
        with self.assertRaises(ValueError):
            self.validate_frame(frame)

    def test_non_numeric_temperature_is_rejected(self):
        frame = pd.DataFrame([{
            "scenario_id": "BAD-NUMBER",
            "temperature_c": "abc",
            "humidity_pct": 50,
            "occupancy_count": 20,
            "tariff_level": "low",
        }])
        with self.assertRaises(ValueError):
            self.validate_frame(frame)

    def test_duplicate_scenario_ids_are_rejected(self):
        row = {
            "scenario_id": "DUPLICATE",
            "temperature_c": 25,
            "humidity_pct": 50,
            "occupancy_count": 20,
            "tariff_level": "low",
        }
        with self.assertRaises(ValueError):
            self.validate_frame(pd.DataFrame([row, row]))

    def test_baseline_zero_occupancy_turns_cooling_and_fan_off(self):
        cooling, fan, action = baseline_controller(38, 60, 0, "high")
        self.assertEqual((cooling, fan, action), (0, "off", "avoid_peak"))

    def test_high_tariff_triggers_avoid_peak_for_both_controllers(self):
        _, _, baseline_action = baseline_controller(28, 50, 20, "high")

        row = pd.Series({
            "temperature_c": 28,
            "humidity_pct": 50,
            "occupancy_count": 20,
            "tariff_level": "high",
        })
        fuzzy_result = fuzzy_controller(row)

        self.assertEqual(baseline_action, "avoid_peak")
        self.assertEqual(fuzzy_result["energy_action"], "avoid_peak")

    def test_fuzzy_outputs_stay_within_defined_ranges(self):
        scenarios = [
            (18, 0, 0, "low"),
            (45, 100, 100, "high"),
            (24, 50, 20, "medium"),
            (36, 85, 45, "medium"),
        ]
        for temp, humidity, occupancy, tariff in scenarios:
            row = pd.Series({
                "temperature_c": temp,
                "humidity_pct": humidity,
                "occupancy_count": occupancy,
                "tariff_level": tariff,
            })
            result = fuzzy_controller(row)

            self.assertTrue(0 <= result["cooling_pct"] <= 100)
            self.assertIn(
                result["fan_level"], ["off", "low", "medium", "high"]
            )
            self.assertIn(
                result["energy_action"], ["normal", "avoid_peak"]
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
