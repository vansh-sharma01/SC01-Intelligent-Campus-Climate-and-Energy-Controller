
import sys
from pathlib import Path

import pandas as pd


DEFAULT_FILE = "data/sample_input.csv"

REQUIRED = [
    "scenario_id",
    "temperature_c",
    "humidity_pct",
    "occupancy_count",
    "tariff_level",
]

NUMERIC = [
    "temperature_c",
    "humidity_pct",
    "occupancy_count",
]


def validate_data(file_path):
    path = Path(file_path)

    # Check whether the input file exists.
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")

    # Load the dataset.
    df = pd.read_csv(path)

    print("File:", path)
    print("Shape:", df.shape)
    print("Columns:", list(df.columns))
    print("Missing values:")
    print(df.isna().sum())

    # Check required columns.
    missing_columns = [
        column for column in REQUIRED
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    # Check missing values.
    if df[REQUIRED].isna().any().any():
        raise ValueError("Missing value found")

    # Check scenario IDs are not empty.
    if df["scenario_id"].astype(str).str.strip().eq("").any():
        raise ValueError("Empty scenario_id found")

    # Check numeric fields.
    for column in NUMERIC:
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise ValueError(f"{column} must be numeric")

    # Check temperature range: 18–45°C.
    if not df["temperature_c"].between(18, 45).all():
        raise ValueError(
            "Temperature must be between 18 and 45°C"
        )

    # Check relative humidity range: 0–100%.
    if not df["humidity_pct"].between(0, 100).all():
        raise ValueError(
            "Humidity must be between 0 and 100%"
        )

    # Check occupancy is non-negative.
    if (df["occupancy_count"] < 0).any():
        raise ValueError("Occupancy cannot be negative")

    # Check tariff categories.
    valid_tariffs = ["low", "medium", "high"]

    if not df["tariff_level"].isin(valid_tariffs).all():
        raise ValueError("Invalid tariff level")

    # Check scenario IDs are unique.
    if df["scenario_id"].duplicated().any():
        raise ValueError("Duplicate scenario_id found")

    print("\nDATA VALIDATION PASSED")
    return True


if __name__ == "__main__":
    input_file = (
        sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_FILE
    )

    validate_data(input_file)
