"""Step 6 - fresh scenario-coverage run with the CURRENT fuzzy controller.

Run from the repository root:

    python src/run_step6_scenario_coverage.py

Why this exists: results/step4/scenario_coverage_results.csv was produced by an
earlier version of the fuzzy controller and no longer matches it. That file is
left untouched (earlier evidence is preserved) and is NOT used as current
evidence. This script re-runs the 10 hand-made scenarios in
data/test/scenario_coverage.csv through the current controller and writes:

  results/step6_testing/scenario_coverage_current.csv    current outputs
  results/step6_testing/step4_saved_vs_current.csv       row-by-row difference
  results/step6_testing/scenario_rule_coverage.csv       rules fired per scenario

It also reports how many of the 11 fuzzy rules those 10 scenarios exercise.
The scenarios are hand-defined test inputs, not real campus measurements.
"""

import sys
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))

from fuzzy_controller import fuzzy_controller  # noqa: E402
from test_fuzzy_rule_coverage import RULE_NAMES, collect_strengths  # noqa: E402

INPUT_FILE = ROOT / "data" / "test" / "scenario_coverage.csv"
SAVED_STEP4 = ROOT / "results" / "step4" / "scenario_coverage_results.csv"
OUT_DIR = ROOT / "results" / "step6_testing"


def main():
    scenarios = pd.read_csv(INPUT_FILE)
    outputs = scenarios.apply(fuzzy_controller, axis=1)
    current = pd.concat([scenarios, outputs], axis=1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    current.to_csv(OUT_DIR / "scenario_coverage_current.csv", index=False)

    print(f"Scenarios run with the current fuzzy controller: {len(current)}")
    print("Scenario types:",
          current["scenario_type"].value_counts().to_dict())
    missing = int(current[["cooling_pct", "fan_level",
                           "energy_action"]].isna().sum().sum())
    print(f"Missing output values: {missing}")

    # --- rule coverage of the 10 scenarios (occupied rooms only) ---------
    occupied = current[current["occupancy_count"] != 0]
    strengths = collect_strengths(
        list(zip(occupied["temperature_c"].astype(float),
                 occupied["humidity_pct"].astype(float),
                 occupied["occupancy_count"].astype(float))))
    fired = pd.DataFrame(
        [[int(s > 0) for s in row] for row in strengths],
        columns=[name.split()[0] for name in RULE_NAMES],
        index=occupied["scenario_id"].values)
    fired.index.name = "scenario_id"
    fired.to_csv(OUT_DIR / "scenario_rule_coverage.csv")
    counts = fired.sum()
    exercised = [rule for rule in counts.index if counts[rule] > 0]
    never = [rule for rule in counts.index if counts[rule] == 0]
    print(f"\nRules exercised by these {len(occupied)} occupied scenarios: "
          f"{len(exercised)} of {len(RULE_NAMES)}")
    print("  fired:", ", ".join(exercised))
    print("  never fired:", ", ".join(never) if never else "none")
    print("  (the dedicated rule-coverage tests in "
          "src/test_fuzzy_rule_coverage.py cover all 11 rules)")

    # --- saved Step 4 file versus the current controller -------------------
    saved = pd.read_csv(SAVED_STEP4)
    rows = []
    for _, old in saved.iterrows():
        new = current[current["scenario_id"] == old["scenario_id"]].iloc[0]
        same = (float(old["cooling_pct"]) == float(new["cooling_pct"])
                and old["fan_level"] == new["fan_level"]
                and old["energy_action"] == new["energy_action"])
        rows.append({
            "scenario_id": old["scenario_id"],
            "saved_step4_cooling_pct": old["cooling_pct"],
            "saved_step4_fan_level": old["fan_level"],
            "current_cooling_pct": new["cooling_pct"],
            "current_fan_level": new["fan_level"],
            "same": same,
        })
    comparison = pd.DataFrame(rows)
    comparison.to_csv(OUT_DIR / "step4_saved_vs_current.csv", index=False)
    different = comparison[~comparison["same"]]
    print(f"\nSaved Step 4 result rows that differ from the current "
          f"controller: {len(different)} of {len(comparison)}")
    for _, row in different.iterrows():
        print(f"  {row['scenario_id']}: saved "
              f"{row['saved_step4_cooling_pct']}/{row['saved_step4_fan_level']}"
              f" -> current {row['current_cooling_pct']}/"
              f"{row['current_fan_level']}")
    print("The Step 4 file was not modified and is not current evidence.")

    ok = len(current) == 10 and missing == 0
    print("\nRESULT:", "PASS (10 rows, no missing outputs)" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
