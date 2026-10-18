import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fuzzy_controller import fuzzy_controller


def make_row(
    temperature_c=25,
    humidity_pct=50,
    occupancy_count=20,
    tariff_level="low",
):
    return pd.Series({
        "scenario_id": "TEST",
        "temperature_c": temperature_c,
        "humidity_pct": humidity_pct,
        "occupancy_count": occupancy_count,
        "tariff_level": tariff_level,
    })


class TestFuzzyControllerBoundaries(unittest.TestCase):

    def test_temperature_lower_boundary(self):
        result = fuzzy_controller(make_row(temperature_c=18))
        self.assertTrue(0 <= result["cooling_pct"] <= 100)

    def test_temperature_upper_boundary(self):
        result = fuzzy_controller(make_row(temperature_c=45))
        self.assertTrue(0 <= result["cooling_pct"] <= 100)

    def test_humidity_lower_boundary(self):
        result = fuzzy_controller(make_row(humidity_pct=20))
        self.assertTrue(0 <= result["cooling_pct"] <= 100)

    def test_humidity_upper_boundary(self):
        result = fuzzy_controller(make_row(humidity_pct=100))
        self.assertTrue(0 <= result["cooling_pct"] <= 100)

    def test_occupancy_lower_boundary(self):
        result = fuzzy_controller(make_row(occupancy_count=0))
        self.assertEqual(result["cooling_pct"], 0)
        self.assertEqual(result["fan_level"], "off")

    def test_occupancy_upper_boundary(self):
        result = fuzzy_controller(make_row(occupancy_count=100))
        self.assertTrue(0 <= result["cooling_pct"] <= 100)


class TestFuzzyControllerInvalidInputs(unittest.TestCase):

    def test_invalid_temperature_below_range(self):
        with self.assertRaises(ValueError):
            fuzzy_controller(make_row(temperature_c=17))

    def test_invalid_temperature_above_range(self):
        with self.assertRaises(ValueError):
            fuzzy_controller(make_row(temperature_c=46))

    def test_invalid_humidity_below_range(self):
        with self.assertRaises(ValueError):
            fuzzy_controller(make_row(humidity_pct=19))

    def test_invalid_humidity_above_range(self):
        with self.assertRaises(ValueError):
            fuzzy_controller(make_row(humidity_pct=101))

    def test_invalid_occupancy_below_range(self):
        with self.assertRaises(ValueError):
            fuzzy_controller(make_row(occupancy_count=-1))

    def test_invalid_occupancy_above_range(self):
        with self.assertRaises(ValueError):
            fuzzy_controller(make_row(occupancy_count=101))

    def test_invalid_tariff(self):
        with self.assertRaises(ValueError):
            fuzzy_controller(make_row(tariff_level="invalid"))

    def test_empty_tariff(self):
        with self.assertRaises(ValueError):
            fuzzy_controller(make_row(tariff_level=""))

    def test_uppercase_tariff(self):
        with self.assertRaises(ValueError):
            fuzzy_controller(make_row(tariff_level="HIGH"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
