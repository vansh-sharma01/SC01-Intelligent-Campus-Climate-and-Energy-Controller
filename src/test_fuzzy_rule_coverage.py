"""Step 6 - fuzzy controller rule coverage and limit tests.

Run from the repository root:

    python -m unittest discover -s src -p "test_fuzzy_rule_coverage.py" -v

The fuzzy controller (src/fuzzy_controller.py) is NOT modified. Its 11
zero-order Sugeno rules live in a local list inside fuzzy_cooling(), so these
tests read that list from the real function while it runs, using Python's
profiling hook, and look at each rule's firing strength. Rules are numbered
R01-R11 in the order they appear in the controller:

  R01 temp low  & occ low        R07 temp high & occ low
  R02 temp low  & occ medium     R08 temp high & occ medium
  R03 temp low  & occ high       R09 temp high & occ high
  R04 temp med  & occ low        R10 temp med  & humidity high
  R05 temp med  & occ medium     R11 temp low  & humidity high & occ high
  R06 temp med  & occ high

Compatible with Python 3.9 and later.
"""

import json
import sys
import unittest
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))

import fuzzy_controller as fc  # noqa: E402

GA_PARAMS = json.loads(
    (ROOT / "results" / "step6" / "ga_best_params.json").read_text()
)["parameters"]
DEFAULT_PARAMS = dict(fc.DEFAULT_PARAMS)
SCENARIOS_FILE = ROOT / "data" / "processed" / "cleaned_input.csv"
RULE_COUNT = 11
RULE_NAMES = [
    "R01 temp low & occ low", "R02 temp low & occ medium",
    "R03 temp low & occ high", "R04 temp medium & occ low",
    "R05 temp medium & occ medium", "R06 temp medium & occ high",
    "R07 temp high & occ low", "R08 temp high & occ medium",
    "R09 temp high & occ high", "R10 temp medium & humidity high",
    "R11 temp low & humidity high & occ high",
]


def collect_strengths(points, params=None):
    """Call the real fuzzy_cooling() for each (temperature, humidity,
    occupancy) point and return the list of 11 rule strengths for each call.
    The controller code is untouched; the rule list is read when the function
    returns."""
    captured = []

    def profiler(frame, event, arg):
        if event == "return" and frame.f_code is fc.fuzzy_cooling.__code__:
            rules = frame.f_locals.get("rules")
            if rules is not None:
                captured.append([float(weight) for weight, _ in rules])

    previous = sys.getprofile()
    sys.setprofile(profiler)
    try:
        for temperature, humidity, occupancy in points:
            fc.fuzzy_cooling(temperature, humidity, occupancy, params)
    finally:
        sys.setprofile(previous)
    if len(captured) != len(points):
        raise AssertionError(
            f"read rule strengths for {len(captured)} of {len(points)} calls")
    return captured


def strengths_at(temperature, humidity, occupancy, params=None):
    return collect_strengths([(temperature, humidity, occupancy)], params)[0]


def valid_grid(params):
    """A grid over the whole valid input range, including the exact
    temperature breakpoints of the given parameters."""
    temps = [18 + 0.5 * i for i in range(55)]
    temps += [params["t1"], params["t2"], params["t3"]]
    humidities = [20, 30, 40, 50, 60, 65, 70, 80, 90, 100]
    occupancies = [1, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 85, 90, 100]
    return [(t, h, o) for t in temps for h in humidities for o in occupancies]


class RuleWitnessTests(unittest.TestCase):
    """One hand-calculated witness input per rule (default parameters
    t1/t2/t3 = 24/30/36): the rule must fire with the expected strength."""

    def check(self, rule_number, temperature, humidity, occupancy, expected):
        strengths = strengths_at(temperature, humidity, occupancy)
        self.assertEqual(len(strengths), RULE_COUNT)
        self.assertAlmostEqual(
            strengths[rule_number - 1], expected, places=9,
            msg=f"{RULE_NAMES[rule_number - 1]} at "
                f"{temperature}/{humidity}/{occupancy}")
        self.assertGreater(strengths[rule_number - 1], 0)
        cooling = fc.fuzzy_cooling(temperature, humidity, occupancy)
        self.assertTrue(0 <= cooling <= 100)

    def test_F01_rule_R01_temp_low_and_occupancy_low(self):
        self.check(1, 21, 50, 5, 0.5)

    def test_F02_rule_R02_temp_low_and_occupancy_medium(self):
        self.check(2, 21, 50, 30, 0.5)

    def test_F03_rule_R03_temp_low_and_occupancy_high(self):
        self.check(3, 21, 50, 80, 0.5)

    def test_F04_rule_R04_temp_medium_and_occupancy_low(self):
        self.check(4, 27, 50, 5, 0.5)

    def test_F05_rule_R05_temp_medium_and_occupancy_medium(self):
        self.check(5, 27, 50, 50, 0.5)

    def test_F06_rule_R06_temp_medium_and_occupancy_high(self):
        self.check(6, 27, 50, 100, 0.5)

    def test_F07_rule_R07_temp_high_and_occupancy_low(self):
        self.check(7, 33, 50, 5, 0.5)

    def test_F08_rule_R08_temp_high_and_occupancy_medium(self):
        self.check(8, 33, 50, 50, 0.5)

    def test_F09_rule_R09_temp_high_and_occupancy_high(self):
        self.check(9, 40, 50, 100, 1.0)

    def test_F10_rule_R10_temp_medium_and_humidity_high(self):
        self.check(10, 30, 82.5, 5, 0.5)

    def test_F11_rule_R11_temp_low_humidity_high_occupancy_high(self):
        self.check(11, 21, 100, 100, 0.5)


class NoDeadRuleTests(unittest.TestCase):
    def assert_all_rules_fire(self, points, params, label):
        strengths = collect_strengths(points, params)
        counts = [sum(1 for s in row if s > 0) for row in zip(*strengths)]
        print(f"\n[{label}] {len(points)} inputs evaluated; "
              "times each rule fired (strength > 0):")
        for name, count in zip(RULE_NAMES, counts):
            print(f"    {name:42s} {count:>6}")
        dead = [RULE_NAMES[i] for i, c in enumerate(counts) if c == 0]
        self.assertEqual(dead, [], f"rules that never fire: {dead}")

    def test_F12_no_dead_rule_in_the_10000_synthetic_scenarios(self):
        frame = pd.read_csv(SCENARIOS_FILE)
        frame = frame[frame["occupancy_count"] != 0]  # empty rooms skip fuzzy
        points = list(zip(frame["temperature_c"].astype(float),
                          frame["humidity_pct"].astype(float),
                          frame["occupancy_count"].astype(float)))
        self.assertGreater(len(points), 9000)
        self.assert_all_rules_fire(points, None, "10,000 scenarios, default")

    def test_F13_no_dead_rule_with_saved_ga_parameters(self):
        self.assert_all_rules_fire(valid_grid(GA_PARAMS), GA_PARAMS,
                                   "valid-range grid, saved GA parameters")

    def test_F13b_no_dead_rule_with_default_parameters_on_the_grid(self):
        self.assert_all_rules_fire(valid_grid(DEFAULT_PARAMS), None,
                                   "valid-range grid, default parameters")


class ZeroStrengthFallbackTests(unittest.TestCase):
    """fuzzy_cooling() falls back to 'cool_low if temperature < t2 else
    cool_high' when the total firing strength is zero."""

    def test_F14_fallback_at_temperature_equal_to_t1_default(self):
        strengths = strengths_at(24.0, 50, 50)
        self.assertEqual(sum(strengths), 0.0)
        self.assertEqual(fc.fuzzy_cooling(24.0, 50, 50), 15.0)
        out = fc.fuzzy_controller(pd.Series({
            "temperature_c": 24.0, "humidity_pct": 50,
            "occupancy_count": 50, "tariff_level": "low"}))
        self.assertEqual(out["cooling_pct"], 15.0)
        self.assertEqual(out["fan_level"], "low")

    def test_F14_fallback_at_temperature_equal_to_t1_ga(self):
        t1 = GA_PARAMS["t1"]
        strengths = strengths_at(t1, 50, 50, GA_PARAMS)
        self.assertEqual(sum(strengths), 0.0)
        self.assertAlmostEqual(fc.fuzzy_cooling(t1, 50, 50, GA_PARAMS),
                               GA_PARAMS["cool_low"], places=9)
        out = fc.fuzzy_controller(pd.Series({
            "temperature_c": t1, "humidity_pct": 50,
            "occupancy_count": 50, "tariff_level": "low"}), params=GA_PARAMS)
        self.assertEqual(out["cooling_pct"], round(GA_PARAMS["cool_low"], 2))
        self.assertEqual(out["fan_level"], "low")

    def test_F14_just_either_side_of_t1_is_not_a_fallback(self):
        for delta in (-0.01, 0.01):
            self.assertGreater(sum(strengths_at(24.0 + delta, 50, 50)), 0)

    def test_F15_zero_strength_only_at_t1_and_high_branch_unreachable(self):
        for label, params in (("default", DEFAULT_PARAMS), ("GA", GA_PARAMS)):
            points = valid_grid(params)
            strengths = collect_strengths(points, params)
            zero_points = [p for p, row in zip(points, strengths)
                           if sum(row) == 0]
            self.assertTrue(zero_points, f"{label}: expected the t1 case")
            for temperature, _, _ in zero_points:
                self.assertEqual(temperature, params["t1"])
                # the branch taken is 'low' because t1 < t2
                self.assertLess(temperature, params["t2"])
            print(f"\n[{label}] zero-strength inputs on the grid: "
                  f"{len(zero_points)}, all at temperature == t1 "
                  f"({params['t1']}); the 'else cool_high' fallback branch "
                  "was never reached")


class MembershipLimitTests(unittest.TestCase):
    """Exact values at the breakpoints of the membership functions. These use
    the controller's own helper functions."""

    def test_F16_temperature_memberships_default(self):
        t1, t2, t3 = 24.0, 30.0, 36.0
        self.assertEqual(fc._left_shoulder(18, 18, t1), 1.0)
        self.assertEqual(fc._left_shoulder(21, 18, t1), 0.5)
        self.assertEqual(fc._left_shoulder(t1, 18, t1), 0.0)
        self.assertEqual(fc._triangle(t1, t1, t2, t3), 0.0)
        self.assertEqual(fc._triangle(27, t1, t2, t3), 0.5)
        self.assertEqual(fc._triangle(t2, t1, t2, t3), 1.0)
        self.assertEqual(fc._triangle(33, t1, t2, t3), 0.5)
        self.assertEqual(fc._triangle(t3, t1, t2, t3), 0.0)
        self.assertEqual(fc._right_shoulder(t2, t2, t3), 0.0)
        self.assertEqual(fc._right_shoulder(33, t2, t3), 0.5)
        self.assertEqual(fc._right_shoulder(t3, t2, t3), 1.0)
        self.assertEqual(fc._right_shoulder(45, t2, t3), 1.0)

    def test_F16_occupancy_memberships(self):
        self.assertEqual(fc._left_shoulder(0, 0, 20), 1.0)
        self.assertEqual(fc._left_shoulder(10, 0, 20), 0.5)
        self.assertEqual(fc._left_shoulder(20, 0, 20), 0.0)
        self.assertEqual(fc._triangle(10, 10, 50, 85), 0.0)
        self.assertEqual(fc._triangle(30, 10, 50, 85), 0.5)
        self.assertEqual(fc._triangle(50, 10, 50, 85), 1.0)
        self.assertEqual(fc._triangle(85, 10, 50, 85), 0.0)
        self.assertEqual(fc._right_shoulder(60, 60, 100), 0.0)
        self.assertEqual(fc._right_shoulder(80, 60, 100), 0.5)
        self.assertEqual(fc._right_shoulder(100, 60, 100), 1.0)

    def test_F16_humidity_high_membership(self):
        self.assertEqual(fc._right_shoulder(65, 65, 100), 0.0)
        self.assertEqual(fc._right_shoulder(82.5, 65, 100), 0.5)
        self.assertEqual(fc._right_shoulder(100, 65, 100), 1.0)

    def test_F16_every_rule_strength_stays_between_0_and_1(self):
        for params in (DEFAULT_PARAMS, GA_PARAMS):
            for row in collect_strengths(valid_grid(params), params):
                for strength in row:
                    self.assertTrue(0.0 <= strength <= 1.0)


class FanAndOutputLimitTests(unittest.TestCase):
    @staticmethod
    def run_controller(humidity, consequent, occupancy=50, temperature=27,
                       tariff="low"):
        """All three consequents equal, so cooling equals that value."""
        params = {"cool_low": consequent, "cool_medium": consequent,
                  "cool_high": consequent}
        return fc.fuzzy_controller(pd.Series({
            "temperature_c": temperature, "humidity_pct": humidity,
            "occupancy_count": occupancy, "tariff_level": tariff}),
            params=params)

    def test_F17_fan_thresholds_at_30_and_70(self):
        # 27/50/50 fires only R05 with strength 0.5, so cooling is exact.
        expected = [(29.99, "low"), (30.0, "medium"), (69.99, "medium"),
                    (70.0, "high")]
        for value, fan in expected:
            with self.subTest(cooling=value):
                out = self.run_controller(50, value)
                self.assertEqual(out["cooling_pct"], value)
                self.assertEqual(out["fan_level"], fan)

    def test_F18_humidity_bump_starts_at_80(self):
        cases = [  # (cooling, humidity, expected fan)
            (10.0, 79.99, "low"), (10.0, 80.0, "medium"),
            (50.0, 79.99, "medium"), (50.0, 80.0, "high"),
            (85.0, 79.99, "high"), (85.0, 80.0, "high"),
        ]
        for value, humidity, fan in cases:
            with self.subTest(cooling=value, humidity=humidity):
                out = self.run_controller(humidity, value)
                self.assertEqual(out["cooling_pct"], value)
                self.assertEqual(out["fan_level"], fan)

    def test_F19_empty_room_gives_zero_cooling_and_fan_off(self):
        for params in (None, GA_PARAMS):
            for temperature in (18, 30, 45):
                for humidity in (20, 85, 100):
                    for tariff in ("low", "medium", "high"):
                        out = fc.fuzzy_controller(pd.Series({
                            "temperature_c": temperature,
                            "humidity_pct": humidity, "occupancy_count": 0,
                            "tariff_level": tariff}), params=params)
                        self.assertEqual(out["cooling_pct"], 0.0)
                        self.assertEqual(out["fan_level"], "off")

    def test_F20_outputs_stay_in_range_over_the_valid_input_range(self):
        for params in (None, GA_PARAMS):
            checked = 0
            for temperature in range(18, 46):
                for humidity in (20, 40, 60, 80, 100):
                    for occupancy in (0, 1, 25, 50, 75, 100):
                        out = fc.fuzzy_controller(pd.Series({
                            "temperature_c": temperature,
                            "humidity_pct": humidity,
                            "occupancy_count": occupancy,
                            "tariff_level": "medium"}), params=params)
                        self.assertTrue(0 <= out["cooling_pct"] <= 100)
                        self.assertIn(out["fan_level"],
                                      ("off", "low", "medium", "high"))
                        self.assertEqual(out["fan_level"] == "off",
                                         occupancy == 0)
                        checked += 1
            self.assertEqual(checked, 28 * 5 * 6)

    def test_F21_temperature_parameter_order_is_enforced(self):
        bad = [{"t1": 30.0, "t2": 30.0, "t3": 36.0},   # t1 not below t2
               {"t1": 18.0, "t2": 30.0, "t3": 36.0},   # t1 not above 18
               {"t1": 24.0, "t2": 30.0, "t3": 45.0},   # t3 not below 45
               {"t1": 24.0, "t2": 36.0, "t3": 30.0}]   # t2 above t3
        for params in bad:
            with self.subTest(params=params):
                with self.assertRaises(ValueError):
                    fc.fuzzy_cooling(25, 50, 50, params)

    def test_F21_saved_ga_parameters_are_accepted(self):
        value = fc.fuzzy_cooling(25, 50, 50, GA_PARAMS)
        self.assertTrue(0 <= value <= 100)


if __name__ == "__main__":
    unittest.main()
