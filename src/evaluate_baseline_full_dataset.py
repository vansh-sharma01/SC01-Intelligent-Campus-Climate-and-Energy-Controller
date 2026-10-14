from pathlib import Path
import sys

import pandas as pd

# Allow this script to import the existing baseline controller.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_controller import baseline_controller

INPUT = Path("data/processed/cleaned_input.csv")
OUTPUT = Path("results/step3/full_dataset_baseline_results.csv")
SUMMARY = Path("results/step3/full_dataset_evaluation_summary.csv")

# Explicit project assumption, not a validated comfort standard.
COMFORT_MIN_C = 22.0
COMFORT_MAX_C = 26.0

required = {
    "scenario_id",
    "temperature_c",
    "humidity_pct",
    "occupancy_count",
    "tariff_level",
}

df = pd.read_csv(INPUT)

if not required.issubset(df.columns):
    raise ValueError(f"Missing columns: {sorted(required - set(df.columns))}")
if len(df) != 10000:
    raise ValueError(f"Expected 10,000 scenarios; found {len(df)}")
if df[list(required)].isna().any().any():
    raise ValueError("Input contains missing required values")
if df["scenario_id"].duplicated().any():
    raise ValueError("Duplicate scenario IDs found")

records = []

fan_proxy = {"off": 0.0, "low": 1 / 3, "medium": 2 / 3, "high": 1.0}

for row in df.to_dict(orient="records"):
    cooling, fan, action = baseline_controller(
        temperature_c=float(row["temperature_c"]),
        humidity_pct=float(row["humidity_pct"]),
        occupancy_count=int(row["occupancy_count"]),
        tariff_level=str(row["tariff_level"]),
    )

    occupied = int(row["occupancy_count"]) > 0
    outside_band = occupied and not (
        COMFORT_MIN_C <= float(row["temperature_c"]) <= COMFORT_MAX_C
    )

    # Relative control-demand proxy only; not kWh or measured energy.
    demand_proxy = (float(cooling) / 100.0) * fan_proxy[fan]

    records.append({
        **row,
        "baseline_cooling_pct": cooling,
        "baseline_fan_level": fan,
        "baseline_energy_action": action,
        "occupied": occupied,
        "outside_assumed_comfort_band": outside_band,
        "relative_control_demand_proxy": round(demand_proxy, 4),
    })

results = pd.DataFrame(records)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
results.to_csv(OUTPUT, index=False)

occupied_df = results[results["occupied"]]
outside_count = int(occupied_df["outside_assumed_comfort_band"].sum())

summary = pd.DataFrame([
    {"metric": "total_scenarios", "value": len(results)},
    {"metric": "occupied_scenarios", "value": len(occupied_df)},
    {"metric": "unoccupied_scenarios", "value": int((~results["occupied"]).sum())},
    {"metric": "comfort_band_min_c_assumption", "value": COMFORT_MIN_C},
    {"metric": "comfort_band_max_c_assumption", "value": COMFORT_MAX_C},
    {"metric": "occupied_scenarios_outside_comfort_band", "value": outside_count},
    {
        "metric": "occupied_scenarios_outside_band_pct",
        "value": round(100 * outside_count / len(occupied_df), 2)
        if len(occupied_df) else 0,
    },
    {
        "metric": "mean_relative_control_demand_proxy",
        "value": round(results["relative_control_demand_proxy"].mean(), 4),
    },
    {
        "metric": "scenarios_avoiding_peak",
        "value": int((results["baseline_energy_action"] == "avoid_peak").sum()),
    },
    {
        "metric": "energy_metric_limitation",
        "value": "Relative proxy only; not measured kWh or verified energy savings",
    },
    {
        "metric": "comfort_metric_limitation",
        "value": "Snapshot count, not time; 22-26 C is an assumed band",
    },
])

summary.to_csv(SUMMARY, index=False)

print(f"Scenarios evaluated: {len(results)}")
print(f"Occupied scenarios: {len(occupied_df)}")
print(f"Occupied scenarios outside assumed comfort band: {outside_count}")
print(f"Results saved: {OUTPUT}")
print(f"Summary saved: {SUMMARY}")
print("\nEvaluation summary:")
print(summary.to_string(index=False))
