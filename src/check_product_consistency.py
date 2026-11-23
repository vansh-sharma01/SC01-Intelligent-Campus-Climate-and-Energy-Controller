"""Product V1 consistency check.

Run from the repository root:

    python src/check_product_consistency.py

Part A - the interface's inference layer (src/product_inference.py) versus
direct calls to the existing controllers, for the Step 1 test cases, a normal
case, and independent boundary cases, for all three controllers. These must
match exactly.

Part B - the inference layer versus the saved Step 7 evaluation file
(results/step7/three_controller_comparison.csv) for all 10,000 synthetic
scenarios. Fan level and energy action must match exactly; cooling must match
within 0.01 percentage points. (Python 3.12+ sums floats more accurately than
earlier versions, so a controller value sitting exactly on a rounding
boundary can differ by 0.01 between Python versions.)

This checks that the interface is wired to the real controllers. It does not
measure controller quality, energy savings or comfort.

Writes to results/product_v1/ only; Step 3-7 evidence is never modified.
"""

import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))

import product_inference as pi  # noqa: E402
from baseline_controller import TEST_CASES, baseline_controller  # noqa: E402
from fuzzy_controller import fuzzy_controller  # noqa: E402

OUT_DIR = ROOT / "results" / "product_v1"
SAVED_COMPARISON = ROOT / "results" / "step7" / "three_controller_comparison.csv"
SCENARIOS = ROOT / "data" / "processed" / "cleaned_input.csv"
COOLING_TOLERANCE = 0.01 + 1e-9


def direct_call(controller, values, ga_params):
    """Call the existing controllers without the inference layer."""
    if controller == "baseline":
        cooling, fan, action = baseline_controller(
            values["temperature_c"], values["humidity_pct"],
            values["occupancy_count"], values["tariff_level"],
        )
        return float(cooling), fan, action
    params = ga_params if controller == "ga_fuzzy" else None
    out = fuzzy_controller(pd.Series(values), params=params)
    return float(out["cooling_pct"]), out["fan_level"], out["energy_action"]


def check_cases():
    normal = {"temperature_c": 25, "humidity_pct": 55,
              "occupancy_count": 50, "tariff_level": "medium"}
    cases = [("normal", normal)]
    for case in TEST_CASES:
        cases.append((case["scenario_id"], {
            "temperature_c": case["temperature_c"],
            "humidity_pct": case["humidity_pct"],
            "occupancy_count": case["occupancy_count"],
            "tariff_level": case["tariff_level"],
        }))
    # Each boundary is tested on its own, with the other fields normal.
    for field, low, high in [
        ("temperature_c", 18, 45), ("humidity_pct", 20, 100),
        ("occupancy_count", 0, 100),
    ]:
        for label, value in (("min", low), ("max", high)):
            cases.append((f"boundary_{field}_{label}", {**normal, field: value}))
    for tariff in pi.TARIFFS:
        cases.append((f"tariff_{tariff}", {**normal, "tariff_level": tariff}))

    ga_params = pi.load_ga_params()
    rows = []
    for name, values in cases:
        for controller in pi.CONTROLLERS:
            via_layer = pi.recommend(values, controller, ga_params)
            d_cool, d_fan, d_act = direct_call(controller, values, ga_params)
            match = (via_layer["cooling_pct"] == d_cool
                     and via_layer["fan_level"] == d_fan
                     and via_layer["energy_action"] == d_act)
            rows.append({
                "case": name, "controller": controller,
                **values,
                "direct_cooling_pct": d_cool, "direct_fan_level": d_fan,
                "direct_energy_action": d_act,
                "layer_cooling_pct": via_layer["cooling_pct"],
                "layer_fan_level": via_layer["fan_level"],
                "layer_energy_action": via_layer["energy_action"],
                "match": match,
            })
    return pd.DataFrame(rows)


def check_saved_evaluation():
    saved = pd.read_csv(SAVED_COMPARISON)
    scenarios = pd.read_csv(SCENARIOS)
    if list(saved["scenario_id"]) != list(scenarios["scenario_id"]):
        raise RuntimeError("Saved comparison and scenario file are not aligned.")

    ga_params = pi.load_ga_params()
    exact = within_tol = category_mismatch = 0
    max_diff = 0.0
    differing = []
    for (_, scenario), (_, row) in zip(scenarios.iterrows(), saved.iterrows()):
        values = {
            "temperature_c": scenario["temperature_c"],
            "humidity_pct": scenario["humidity_pct"],
            "occupancy_count": scenario["occupancy_count"],
            "tariff_level": scenario["tariff_level"],
        }
        for result in pi.recommend_all(values, ga_params):
            name = result["controller"]
            diff = abs(result["cooling_pct"] - float(row[f"{name}_cooling_pct"]))
            same_cats = (result["fan_level"] == row[f"{name}_fan_level"]
                         and result["energy_action"] == row[f"{name}_energy_action"])
            if not same_cats:
                category_mismatch += 1
            elif diff == 0:
                exact += 1
            elif diff <= COOLING_TOLERANCE:
                within_tol += 1
                differing.append(f"{row['scenario_id']}/{name}: "
                                 f"layer {result['cooling_pct']} vs saved "
                                 f"{row[f'{name}_cooling_pct']}")
            max_diff = max(max_diff, diff)
    total = len(saved) * len(pi.CONTROLLERS)
    return {
        "scenarios": len(saved), "comparisons": total, "exact": exact,
        "within_0.01_cooling": within_tol, "category_mismatches": category_mismatch,
        "max_cooling_difference": round(max_diff, 6),
        "cooling_rounding_differences": differing,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cases = check_cases()
    cases.to_csv(OUT_DIR / "consistency_cases.csv", index=False)
    part_a_ok = bool(cases["match"].all())

    history = check_saved_evaluation()
    part_b_ok = (history["category_mismatches"] == 0
                 and history["max_cooling_difference"] <= COOLING_TOLERANCE)

    summary = {
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "part_a_layer_vs_direct": {
            "comparisons": len(cases), "matches": int(cases["match"].sum()),
            "passed": part_a_ok,
        },
        "part_b_layer_vs_saved_step7_evaluation": {**history, "passed": part_b_ok},
        "scope": ("Checks interface wiring only; not controller quality, "
                  "energy savings or comfort."),
    }
    (OUT_DIR / "consistency_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Python {summary['python']} | pandas {pd.__version__} | numpy {np.__version__}")
    print(f"Part A  layer vs direct controllers : "
          f"{summary['part_a_layer_vs_direct']['matches']}/{len(cases)} match "
          f"-> {'PASS' if part_a_ok else 'FAIL'}")
    print(f"Part B  layer vs saved Step 7 file  : {history['comparisons']} comparisons, "
          f"{history['exact']} exact, {history['within_0.01_cooling']} differ by <=0.01 "
          f"cooling, {history['category_mismatches']} fan/action mismatches "
          f"-> {'PASS' if part_b_ok else 'FAIL'}")
    for line in history["cooling_rounding_differences"]:
        print("   rounding difference:", line)
    print("Saved: results/product_v1/consistency_cases.csv, consistency_summary.json")
    return 0 if (part_a_ok and part_b_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
