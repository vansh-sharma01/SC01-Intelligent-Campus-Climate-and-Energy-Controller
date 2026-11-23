"""Step 6 reference result generator.

Run from the repository root:

    python src/make_step6_reference.py

Reads the test cases in data/test/step6_cases.csv and calls the existing
controllers DIRECTLY (baseline_controller and fuzzy_controller, the latter
with default parameters and with the saved GA parameters). It deliberately
does not use app/app.py or src/product_inference.py, so the result is an
independent reference to compare the interface's CSV downloads against.

Writes results/step6_testing/reference_predictions.csv (one row per case and
controller). Earlier result files are never modified.
"""

import json
import sys
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))

from baseline_controller import baseline_controller  # noqa: E402
from fuzzy_controller import fuzzy_controller  # noqa: E402

CASES_FILE = ROOT / "data" / "test" / "step6_cases.csv"
GA_PARAMS_FILE = ROOT / "results" / "step6" / "ga_best_params.json"
OUT_FILE = ROOT / "results" / "step6_testing" / "reference_predictions.csv"

COLUMNS = [
    "case_id", "controller", "temperature_c", "humidity_pct",
    "occupancy_count", "tariff_level", "cooling_pct", "fan_level",
    "energy_action",
]


def main():
    cases = pd.read_csv(CASES_FILE)
    ga_params = json.loads(GA_PARAMS_FILE.read_text())["parameters"]

    rows = []
    for case in cases.itertuples(index=False):
        values = {
            "temperature_c": float(case.temperature_c),
            "humidity_pct": float(case.humidity_pct),
            "occupancy_count": int(case.occupancy_count),
            "tariff_level": case.tariff_level,
        }
        cooling, fan, action = baseline_controller(
            values["temperature_c"], values["humidity_pct"],
            values["occupancy_count"], values["tariff_level"])
        outputs = {"baseline": (float(cooling), fan, action)}
        for name, params in (("fuzzy", None), ("ga_fuzzy", ga_params)):
            out = fuzzy_controller(pd.Series(values), params=params)
            outputs[name] = (float(out["cooling_pct"]), out["fan_level"],
                             out["energy_action"])
        for controller in ("baseline", "fuzzy", "ga_fuzzy"):
            cooling, fan, action = outputs[controller]
            rows.append({
                "case_id": case.case_id, "controller": controller,
                **values, "cooling_pct": round(cooling, 2),
                "fan_level": fan, "energy_action": action,
            })

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=COLUMNS).to_csv(OUT_FILE, index=False)
    print(f"Reference rows written: {len(rows)} "
          f"({len(cases)} cases x 3 controllers)")
    print(f"Saved to: {OUT_FILE.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
