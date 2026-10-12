import os

import pandas as pd


input_file = "results/step7/three_controller_comparison.csv"
output_file = "results/step7/evaluation_summary.csv"

df = pd.read_csv(input_file)

controllers = {
    "baseline": "baseline",
    "fuzzy": "fuzzy",
    "ga_fuzzy": "ga_fuzzy",
}

rows = [
    {"metric": "total_scenarios", "controller": "all", "value": len(df)}
]

for label, prefix in controllers.items():
    rows.extend([
        {
            "metric": "average_cooling_output_pct",
            "controller": label,
            "value": round(df[f"{prefix}_cooling_pct"].mean(), 2),
        },
        {
            "metric": "minimum_cooling_output_pct",
            "controller": label,
            "value": round(df[f"{prefix}_cooling_pct"].min(), 2),
        },
        {
            "metric": "maximum_cooling_output_pct",
            "controller": label,
            "value": round(df[f"{prefix}_cooling_pct"].max(), 2),
        },
        {
            "metric": "fan_level_distribution",
            "controller": label,
            "value": df[f"{prefix}_fan_level"].value_counts().to_dict(),
        },
        {
            "metric": "avoid_peak_scenarios",
            "controller": label,
            "value": int((df[f"{prefix}_energy_action"] == "avoid_peak").sum()),
        },
    ])

for left, right in [
    ("baseline", "fuzzy"),
    ("baseline", "ga_fuzzy"),
    ("fuzzy", "ga_fuzzy"),
]:
    for metric, suffix in [
        ("cooling_output_differences", "cooling_pct"),
        ("fan_level_differences", "fan_level"),
        ("energy_action_differences", "energy_action"),
    ]:
        rows.append({
            "metric": metric,
            "controller": f"{left}_vs_{right}",
            "value": int(
                (df[f"{left}_{suffix}"] != df[f"{right}_{suffix}"]).sum()
            ),
        })

summary = pd.DataFrame(rows)

os.makedirs("results/step7", exist_ok=True)
summary.to_csv(output_file, index=False)

print("Three-controller evaluation completed.")
print(summary.to_string(index=False))
print(f"Results saved to {output_file}")
print(
    "\nNote: cooling output is a simulated controller command, "
    "not measured energy consumption or verified energy savings."
)
