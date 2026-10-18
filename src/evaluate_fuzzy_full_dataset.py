
import os
import time

import pandas as pd
from skfuzzy import control as ctrl

from fuzzy_controller import FUZZY_SYSTEM


INPUT_FILE = "data/processed/cleaned_input.csv"
STARTER_INPUT = "data/sample_input.csv"
REFERENCE_FILE = "results/step4/fuzzy_results.csv"
OUTPUT_FILE = "results/step4/full_dataset_fuzzy_results.csv"
SUMMARY_FILE = "results/step4/full_dataset_fuzzy_summary.csv"


REQUIRED_COLUMNS = [
    "scenario_id",
    "temperature_c",
    "humidity_pct",
    "occupancy_count",
    "tariff_level",
]


def evaluate_with_simulation(row, simulation):
    """Evaluate one scenario using a reusable fuzzy inference simulation."""
    temperature = float(row["temperature_c"])
    humidity = float(row["humidity_pct"])
    occupancy = int(row["occupancy_count"])
    tariff = row["tariff_level"]

    # An unoccupied room does not require cooling or fan operation.
    if occupancy == 0:
        return pd.Series({
            "cooling_pct": 0.0,
            "fan_level": "off",
            "energy_action": (
                "avoid_peak" if tariff == "high" else "save"
            ),
        })

    simulation.input["temperature"] = temperature
    simulation.input["humidity"] = humidity
    simulation.input["occupancy"] = occupancy
    simulation.compute()

    cooling_value = round(
        max(0.0, min(100.0, float(simulation.output["cooling"]))),
        1,
    )

    if cooling_value < 30:
        fan_level = "low"
    elif cooling_value < 70:
        fan_level = "medium"
    else:
        fan_level = "high"

    # Increase the fan level when humidity is high.
    if humidity > 75 and fan_level == "low":
        fan_level = "medium"
    elif humidity > 75 and fan_level == "medium":
        fan_level = "high"

    if tariff == "high":
        energy_action = "avoid_peak"
    elif cooling_value <= 30:
        energy_action = "save"
    else:
        energy_action = "normal"

    return pd.Series({
        "cooling_pct": cooling_value,
        "fan_level": fan_level,
        "energy_action": energy_action,
    })


def check_starter_scenarios():
    """Compare starter outputs with saved references by scenario ID."""
    starter = pd.read_csv(STARTER_INPUT)
    reference = pd.read_csv(REFERENCE_FILE)

    if not all(column in starter.columns for column in REQUIRED_COLUMNS):
        raise ValueError(
            "Starter input is missing one or more required columns."
        )

    required_reference_columns = [
        "scenario_id",
        "cooling_pct",
        "fan_level",
        "energy_action",
    ]

    if not all(
        column in reference.columns
        for column in required_reference_columns
    ):
        raise ValueError(
            "Reference results are missing required output columns."
        )

    if starter[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Starter input contains missing required values.")

    if reference[required_reference_columns].isnull().any().any():
        raise ValueError("Reference results contain missing required values.")

    if starter["scenario_id"].duplicated().any():
        raise ValueError("Starter input contains duplicate scenario IDs.")

    if reference["scenario_id"].duplicated().any():
        raise ValueError("Reference results contain duplicate scenario IDs.")

    starter_ids = set(starter["scenario_id"])
    reference_ids = set(reference["scenario_id"])

    if starter_ids != reference_ids:
        missing = sorted(starter_ids - reference_ids)
        unexpected = sorted(reference_ids - starter_ids)

        raise ValueError(
            "Starter/reference scenario IDs differ. "
            f"Missing references: {missing}; "
            f"unexpected references: {unexpected}"
        )

    simulation = ctrl.ControlSystemSimulation(
        FUZZY_SYSTEM,
        cache=True,
        flush_after_run=1,
    )

    evaluated = pd.DataFrame(
        [
            evaluate_with_simulation(row, simulation)
            for _, row in starter.iterrows()
        ]
    )

    evaluated.insert(
        0,
        "scenario_id",
        starter["scenario_id"].to_numpy(),
    )

    reference = reference[required_reference_columns].rename(
        columns={
            "cooling_pct": "cooling_pct_reference",
            "fan_level": "fan_level_reference",
            "energy_action": "energy_action_reference",
        }
    )

    evaluated = evaluated.rename(
        columns={
            "cooling_pct": "cooling_pct_evaluated",
            "fan_level": "fan_level_evaluated",
            "energy_action": "energy_action_evaluated",
        }
    )

    comparison = reference.merge(
        evaluated,
        on="scenario_id",
        how="inner",
        validate="one_to_one",
    )

    comparison["cooling_matches"] = (
        comparison["cooling_pct_reference"]
        - comparison["cooling_pct_evaluated"]
    ).abs() < 0.11

    comparison["fan_matches"] = (
        comparison["fan_level_reference"]
        == comparison["fan_level_evaluated"]
    )

    comparison["energy_matches"] = (
        comparison["energy_action_reference"]
        == comparison["energy_action_evaluated"]
    )

    comparison["all_match"] = comparison[
        ["cooling_matches", "fan_matches", "energy_matches"]
    ].all(axis=1)

    print("\nStarter scenario regression check:")
    print(
        comparison[
            [
                "scenario_id",
                "cooling_pct_reference",
                "cooling_pct_evaluated",
                "fan_matches",
                "energy_matches",
                "all_match",
            ]
        ].to_string(index=False)
    )

    if not comparison["all_match"].all():
        raise RuntimeError(
            "Starter scenario regression check failed. "
            "Do not accept the full-dataset evaluation."
        )

    print(f"All {len(comparison)} starter scenarios match.")
    return True


def main():
    start_time = time.time()

    # Confirm the optimized inference logic before full evaluation.
    check_starter_scenarios()

    df = pd.read_csv(INPUT_FILE)

    if not all(column in df.columns for column in REQUIRED_COLUMNS):
        raise ValueError(
            "Input dataset is missing one or more required columns."
        )

    if df.empty:
        raise ValueError("Input dataset is empty.")

    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Input dataset contains missing required values.")

    if df["scenario_id"].duplicated().any():
        raise ValueError("Input dataset contains duplicate scenario IDs.")

    if not df["tariff_level"].isin(["low", "medium", "high"]).all():
        raise ValueError("Input dataset contains invalid tariff levels.")

    if not df["occupancy_count"].between(0, 100).all():
        raise ValueError("Occupancy counts must be between 0 and 100.")

    if not df["occupancy_count"].mod(1).eq(0).all():
        raise ValueError("Occupancy counts must be whole numbers.")

    if not df["temperature_c"].between(18, 45).all():
        raise ValueError("Temperature values are outside the expected range.")

    if not df["humidity_pct"].between(20, 100).all():
        raise ValueError("Humidity values must be between 20 and 100%.")

    simulation = ctrl.ControlSystemSimulation(
        FUZZY_SYSTEM,
        cache=True,
        flush_after_run=1,
    )

    results = []
    total = len(df)

    for index, (_, row) in enumerate(df.iterrows(), start=1):
        results.append(evaluate_with_simulation(row, simulation))

        if index % 1000 == 0 or index == total:
            print(f"Processed {index:,}/{total:,} scenarios")

    output = pd.concat(
        [
            df.reset_index(drop=True),
            pd.DataFrame(results).reset_index(drop=True),
        ],
        axis=1,
    )

    os.makedirs("results/step4", exist_ok=True)
    output.to_csv(OUTPUT_FILE, index=False)

    summary = pd.DataFrame([{
        "total_scenarios": len(output),
        "occupied_scenarios": int(
            (output["occupancy_count"] > 0).sum()
        ),
        "unoccupied_scenarios": int(
            (output["occupancy_count"] == 0).sum()
        ),
        "mean_cooling_pct": round(
            float(output["cooling_pct"].mean()), 2
        ),
        "median_cooling_pct": round(
            float(output["cooling_pct"].median()), 2
        ),
        "low_fan_count": int(
            (output["fan_level"] == "low").sum()
        ),
        "medium_fan_count": int(
            (output["fan_level"] == "medium").sum()
        ),
        "high_fan_count": int(
            (output["fan_level"] == "high").sum()
        ),
        "off_fan_count": int(
            (output["fan_level"] == "off").sum()
        ),
        "avoid_peak_count": int(
            (output["energy_action"] == "avoid_peak").sum()
        ),
        "save_count": int(
            (output["energy_action"] == "save").sum()
        ),
        "normal_count": int(
            (output["energy_action"] == "normal").sum()
        ),
        "starter_scenarios_match": True,
        "elapsed_seconds": round(time.time() - start_time, 2),
        "limitation": (
            "Synthetic scenarios and controller outputs are not measured "
            "HVAC energy consumption or verified energy savings."
        ),
    }])

    summary.to_csv(SUMMARY_FILE, index=False)

    print(f"\nDetailed results: {OUTPUT_FILE}")
    print(f"Evaluation summary: {SUMMARY_FILE}")
    print(f"Elapsed time: {time.time() - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
