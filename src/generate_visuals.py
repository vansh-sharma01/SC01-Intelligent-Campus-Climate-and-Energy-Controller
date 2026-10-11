from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

BASELINE_FILE = ROOT / "results" / "step3" / "baseline_results.csv"
FUZZY_FILE = ROOT / "results" / "step4" / "fuzzy_results.csv"
OUTPUT_DIR = ROOT / "results" / "figures"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Load the actual controller results.
baseline = pd.read_csv(BASELINE_FILE)
fuzzy = pd.read_csv(FUZZY_FILE)

# Compare only the five mandatory scenarios present in both files.
comparison = baseline.merge(
    fuzzy,
    on="scenario_id",
    how="inner",
    suffixes=("_baseline", "_fuzzy"),
    validate="one_to_one",
)

if len(comparison) != len(baseline):
    raise ValueError(
        "Not every baseline scenario has a matching fuzzy result."
    )

comparison = comparison.sort_values("scenario_id")

# Verify that the input conditions match for both controllers.
for column in [
    "temperature_c",
    "humidity_pct",
    "occupancy_count",
    "tariff_level",
]:
    if not (
        comparison[f"{column}_baseline"]
        == comparison[f"{column}_fuzzy"]
    ).all():
        raise ValueError(f"Scenario inputs differ: {column}")


# Visual 1: Cooling recommendation comparison.
x = range(len(comparison))
width = 0.36

fig, ax = plt.subplots(figsize=(10, 6))

ax.bar(
    [i - width / 2 for i in x],
    comparison["cooling_pct_baseline"],
    width,
    label="Baseline",
)

ax.bar(
    [i + width / 2 for i in x],
    comparison["cooling_pct_fuzzy"],
    width,
    label="Fuzzy",
)

ax.set_title("Baseline vs Fuzzy Cooling Recommendations")
ax.set_xlabel("Scenario ID")
ax.set_ylabel("Cooling recommendation (%)")
ax.set_xticks(list(x))
ax.set_xticklabels(comparison["scenario_id"])
ax.set_ylim(0, 110)
ax.legend()
ax.grid(axis="y", alpha=0.3)

fig.tight_layout()
fig.savefig(
    OUTPUT_DIR / "cooling_comparison.png",
    dpi=200,
    bbox_inches="tight",
)
plt.close(fig)


# Visual 2: Fan-level recommendations by scenario.
fan_order = ["off", "low", "medium", "high"]
fan_values = {level: index for index, level in enumerate(fan_order)}

baseline_fan = comparison["fan_level_baseline"].map(fan_values)
fuzzy_fan = comparison["fan_level_fuzzy"].map(fan_values)

fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(
    list(x),
    baseline_fan,
    marker="o",
    linewidth=2,
    label="Baseline",
)

ax.plot(
    list(x),
    fuzzy_fan,
    marker="s",
    linewidth=2,
    label="Fuzzy",
)

ax.set_title("Fan-Level Recommendations by Scenario")
ax.set_xlabel("Scenario ID")
ax.set_ylabel("Fan level")
ax.set_xticks(list(x))
ax.set_xticklabels(comparison["scenario_id"])
ax.set_yticks(range(len(fan_order)))
ax.set_yticklabels(fan_order)
ax.set_ylim(-0.3, 3.3)
ax.legend()
ax.grid(alpha=0.3)

fig.tight_layout()
fig.savefig(
    OUTPUT_DIR / "fan_level_comparison.png",
    dpi=200,
    bbox_inches="tight",
)
plt.close(fig)


print("VISUAL GENERATION PASSED")
print(f"Scenarios compared: {len(comparison)}")
print(f"Chart 1: {OUTPUT_DIR / 'cooling_comparison.png'}")
print(f"Chart 2: {OUTPUT_DIR / 'fan_level_comparison.png'}")