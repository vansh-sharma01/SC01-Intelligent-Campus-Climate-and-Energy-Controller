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

VALID_TARIFFS = {"low", "medium", "high"}


def validate_data(file_path):
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")

    df = pd.read_csv(path)

    print("File:", path)
    print("Shape:", df.shape)
    print("Columns:", list(df.columns))

    missing_columns = [
        column for column in REQUIRED
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    if df.empty:
        raise ValueError("Dataset is empty")

    print("Missing values:")
    print(df[REQUIRED].isna().sum())

    if df[REQUIRED].isna().any().any():
        raise ValueError("Missing value found")

    if df["scenario_id"].astype(str).str.strip().eq("").any():
        raise ValueError("Empty scenario_id found")

    for column in NUMERIC:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df[NUMERIC].isna().any().any():
        raise ValueError("Numeric fields contain invalid or missing values")

    if not df["temperature_c"].between(18, 45).all():
        raise ValueError("Temperature must be between 18 and 45°C")

    if not df["humidity_pct"].between(0, 100).all():
        raise ValueError("Humidity must be between 0 and 100%")

    if not df["occupancy_count"].between(0, 100).all():
        raise ValueError("Occupancy must be between 0 and 100")

    if not df["occupancy_count"].mod(1).eq(0).all():
        raise ValueError("Occupancy must be a whole number")

    if not df["tariff_level"].isin(VALID_TARIFFS).all():
        raise ValueError("Invalid tariff level")

    if df["scenario_id"].duplicated().any():
        raise ValueError("Duplicate scenario_id found")

    print("\nSTEP 1 DATA CHECK PASSED")
    return True


if __name__ == "__main__":
    input_file = (
        sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_FILE
    )

    validate_data(input_file)
