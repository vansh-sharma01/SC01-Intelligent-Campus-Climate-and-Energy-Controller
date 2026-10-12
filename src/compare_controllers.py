import json
import os

import pandas as pd

from baseline_controller import baseline_controller
from fuzzy_controller import fuzzy_controller


input_file = "data/sample_input.csv"
params_file = "results/step6/ga_best_params.json"
output_file = "results/step7/three_controller_comparison.csv"

df = pd.read_csv(input_file)

with open(params_file, "r") as file:
    ga_params = json.load(file)["parameters"]

baseline_results = pd.DataFrame(
    df.apply(
        lambda row: baseline_controller(
            row["temperature_c"],
            row["humidity_pct"],
            row["occupancy_count"],
            row["tariff_level"],
        ),
        axis=1,
    ).tolist(),
    columns=["cooling_pct", "fan_level", "energy_action"],
)

fuzzy_results = df.apply(fuzzy_controller, axis=1).reset_index(drop=True)

ga_results = df.apply(
    lambda row: fuzzy_controller(row, params=ga_params),
    axis=1,
).reset_index(drop=True)

comparison = pd.DataFrame({"scenario_id": df["scenario_id"]})

for prefix, results in [
    ("baseline", baseline_results),
    ("fuzzy", fuzzy_results),
    ("ga_fuzzy", ga_results),
]:
    for column in ["cooling_pct", "fan_level", "energy_action"]:
        comparison[f"{prefix}_{column}"] = results[column]

os.makedirs("results/step7", exist_ok=True)
comparison.to_csv(output_file, index=False)

print("Three-controller comparison completed.")
print(f"Scenarios compared: {len(comparison)}")
print(f"Results saved to {output_file}")
print("\nCooling output summary:")
print(
    comparison[
        [
            "baseline_cooling_pct",
            "fuzzy_cooling_pct",
            "ga_fuzzy_cooling_pct",
        ]
    ].describe().round(2)
)
print("\nEnergy-action counts:")
for column in [
    "baseline_energy_action",
    "fuzzy_energy_action",
    "ga_fuzzy_energy_action",
]:
    print(f"\n{column}:")
    print(comparison[column].value_counts().to_string())
