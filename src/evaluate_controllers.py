import pandas as pd
import os


input_file = "results/step5/controller_comparison.csv"
output_file = "results/step6/evaluation_summary.csv"

df = pd.read_csv(input_file)

cooling_difference = (
    df["baseline_cooling_pct"] != df["fuzzy_cooling_pct"]
)

fan_difference = (
    df["baseline_fan_level"] != df["fuzzy_fan_level"]
)

energy_difference = (
    df["baseline_energy_action"] != df["fuzzy_energy_action"]
)

summary = pd.DataFrame({
    "metric": [
        "total_scenarios",
        "cooling_differences",
        "fan_differences",
        "energy_action_differences",
        "average_baseline_cooling",
        "average_fuzzy_cooling"
    ],
    "value": [
        len(df),
        cooling_difference.sum(),
        fan_difference.sum(),
        energy_difference.sum(),
        df["baseline_cooling_pct"].mean(),
        df["fuzzy_cooling_pct"].mean()
    ]
})

os.makedirs("results/step6", exist_ok=True)
summary.to_csv(output_file, index=False)

print("Controller evaluation completed successfully.")
print(summary.to_string(index=False))
print(f"Results saved to {output_file}")
