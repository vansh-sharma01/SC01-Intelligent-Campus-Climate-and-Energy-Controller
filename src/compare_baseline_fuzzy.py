
from pathlib import Path

import pandas as pd
from baseline_controller import baseline_controller

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data/processed/cleaned_input.csv"
FUZZY = ROOT / "results/step4/full_dataset_fuzzy_results.csv"
OUT = ROOT / "results/step4/baseline_fuzzy_comparison.csv"
SUMMARY = ROOT / "results/step4/baseline_fuzzy_summary.csv"


def main():
    inputs = pd.read_csv(INPUT)
    fuzzy = pd.read_csv(FUZZY)

    required = [
        "scenario_id", "temperature_c", "humidity_pct",
        "occupancy_count", "tariff_level",
    ]
    outputs = ["cooling_pct", "fan_level", "energy_action"]

    if len(inputs) != 10000 or len(fuzzy) != 10000:
        raise ValueError("Expected 10,000 input and fuzzy-result rows.")

    for frame, columns in [(inputs, required), (fuzzy, required + outputs)]:
        if not set(columns).issubset(frame.columns):
            raise ValueError("A required column is missing.")
        if frame["scenario_id"].isna().any():
            raise ValueError("Missing scenario ID.")
        if frame["scenario_id"].duplicated().any():
            raise ValueError("Duplicate scenario ID.")

    paired = inputs.merge(
        fuzzy[required + outputs],
        on="scenario_id",
        suffixes=("_input", "_fuzzy"),
        validate="one_to_one",
    )

    if len(paired) != len(inputs):
        raise ValueError("Input and fuzzy scenario IDs do not match.")

    for col in required[1:]:
        left = paired[f"{col}_input"]
        right = paired[f"{col}_fuzzy"]
        if col in ("temperature_c", "humidity_pct"):
            equal = pd.to_numeric(left).eq(pd.to_numeric(right))
        else:
            equal = left.eq(right)
        if not equal.all():
            raise ValueError(f"Input mismatch: {col}")

    baseline = [
        baseline_controller(
            row.temperature_c,
            row.humidity_pct,
            row.occupancy_count,
            row.tariff_level,
        )
        for row in inputs.itertuples(index=False)
    ]

    paired["baseline_cooling_pct"] = [x[0] for x in baseline]
    paired["baseline_fan_level"] = [x[1] for x in baseline]
    paired["baseline_energy_action"] = [x[2] for x in baseline]

    paired = paired.rename(columns={
        "cooling_pct": "fuzzy_cooling_pct",
        "fan_level": "fuzzy_fan_level",
        "energy_action": "fuzzy_energy_action",
    })

    paired["cooling_difference_fuzzy_minus_baseline"] = (
        paired["fuzzy_cooling_pct"] - paired["baseline_cooling_pct"]
    ).round(1)

    diff = paired["cooling_difference_fuzzy_minus_baseline"]
    paired["cooling_comparison"] = "equal"
    paired.loc[diff < -0.05, "cooling_comparison"] = "fuzzy_lower"
    paired.loc[diff > 0.05, "cooling_comparison"] = "fuzzy_higher"

    paired["fan_matches"] = (
        paired["baseline_fan_level"] == paired["fuzzy_fan_level"]
    )
    paired["energy_action_matches"] = (
        paired["baseline_energy_action"] == paired["fuzzy_energy_action"]
    )

    paired = paired.sort_values("scenario_id")
    total = len(paired)

    summary = {
        "total_scenarios": total,
        "baseline_mean_cooling_pct": round(
            paired["baseline_cooling_pct"].mean(), 2),
        "fuzzy_mean_cooling_pct": round(
            paired["fuzzy_cooling_pct"].mean(), 2),
        "baseline_median_cooling_pct": round(
            paired["baseline_cooling_pct"].median(), 2),
        "fuzzy_median_cooling_pct": round(
            paired["fuzzy_cooling_pct"].median(), 2),
        "mean_cooling_difference_pct_points": round(diff.mean(), 2),
        "mean_absolute_cooling_difference_pct_points": round(
            diff.abs().mean(), 2),
        "fuzzy_lower_cooling_count": int((diff < -0.05).sum()),
        "fuzzy_equal_cooling_count": int((diff.abs() <= 0.05).sum()),
        "fuzzy_higher_cooling_count": int((diff > 0.05).sum()),
        "fan_match_count": int(paired["fan_matches"].sum()),
        "fan_match_pct": round(100 * paired["fan_matches"].mean(), 2),
        "energy_action_match_count": int(
            paired["energy_action_matches"].sum()),
        "energy_action_match_pct": round(
            100 * paired["energy_action_matches"].mean(), 2),
        "limitation": (
            "Synthetic scenarios; cooling percentage is a control-demand "
            "proxy, not measured HVAC energy use or verified energy savings."
        ),
    }

    for method in ("baseline", "fuzzy"):
        for level in ("off", "low", "medium", "high"):
            count = int((paired[f"{method}_fan_level"] == level).sum())
            summary[f"{method}_fan_{level}_count"] = count
            summary[f"{method}_fan_{level}_pct"] = round(
                100 * count / total, 2)

        for action in ("normal", "save", "avoid_peak"):
            count = int(
                (paired[f"{method}_energy_action"] == action).sum())
            summary[f"{method}_action_{action}_count"] = count
            summary[f"{method}_action_{action}_pct"] = round(
                100 * count / total, 2)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    paired.to_csv(OUT, index=False)
    pd.DataFrame([summary]).to_csv(SUMMARY, index=False)

    print("Paired scenarios compared:", total)
    print("Detailed results:", OUT.relative_to(ROOT))
    print("Summary:", SUMMARY.relative_to(ROOT))
    for key, value in summary.items():
        if key in (
            "baseline_mean_cooling_pct", "fuzzy_mean_cooling_pct",
            "baseline_median_cooling_pct", "fuzzy_median_cooling_pct",
            "mean_cooling_difference_pct_points",
            "mean_absolute_cooling_difference_pct_points",
            "fuzzy_lower_cooling_count", "fuzzy_equal_cooling_count",
            "fuzzy_higher_cooling_count", "fan_match_pct",
            "energy_action_match_pct",
        ):
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
