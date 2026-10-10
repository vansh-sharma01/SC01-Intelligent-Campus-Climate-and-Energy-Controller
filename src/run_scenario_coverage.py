
from pathlib import Path

import pandas as pd

from fuzzy_controller import fuzzy_controller


INPUT_FILE = Path("data/test/scenario_coverage.csv")
OUTPUT_FILE = Path("results/step4/scenario_coverage_results.csv")


def main():
    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "scenario_id",
        "temperature_c",
        "humidity_pct",
        "occupancy_count",
        "tariff_level",
        "scenario_type",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("No test scenarios found.")

    results = df.apply(fuzzy_controller, axis=1)
    output = pd.concat([df, results], axis=1)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_FILE, index=False)

    print("Scenario coverage executed successfully.")
    print(f"Input scenarios: {len(df)}")
    print(f"Results saved to: {OUTPUT_FILE}")
    print("\nScenario counts:")
    print(df["scenario_type"].value_counts().to_string())
    print("\nMissing output values:")
    print(
        output[
            ["cooling_pct", "fan_level", "energy_action"]
        ].isna().sum().to_string()
    )


if __name__ == "__main__":
    main()
