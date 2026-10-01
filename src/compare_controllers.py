import pandas as pd
import os

from baseline_controller import baseline_controller
from fuzzy_controller import fuzzy_controller


input_file = "data/sample_input.csv"
output_file = "results/step5/controller_comparison.csv"

df = pd.read_csv(input_file)

baseline_results = df.apply(
    lambda row: baseline_controller(
        row["temperature_c"],
        row["humidity_pct"],
        row["occupancy_count"],
        row["tariff_level"]
    ),
    axis=1
)

fuzzy_results = df.apply(fuzzy_controller, axis=1)

baseline_results = pd.DataFrame(
    baseline_results.tolist(),
    columns=["cooling_pct", "fan_level", "energy_action"]
)

comparison = pd.DataFrame({
    "scenario_id": df["scenario_id"],
    "baseline_cooling_pct": baseline_results["cooling_pct"],
    "fuzzy_cooling_pct": fuzzy_results["cooling_pct"],
    "baseline_fan_level": baseline_results["fan_level"],
    "fuzzy_fan_level": fuzzy_results["fan_level"],
    "baseline_energy_action": baseline_results["energy_action"],
    "fuzzy_energy_action": fuzzy_results["energy_action"]
})

os.makedirs("results/step5", exist_ok=True)
comparison.to_csv(output_file, index=False)

print("Controller comparison completed successfully.")
print(f"Results saved to {output_file}")
