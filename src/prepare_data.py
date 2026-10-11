
import os

import pandas as pd


INPUT_FILE = "data/raw/generated_scenarios.csv"
OUTPUT_DIR = "data/processed"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cleaned_input.csv")

REQUIRED_COLUMNS = [
    "scenario_id",
    "temperature_c",
    "humidity_pct",
    "occupancy_count",
    "tariff_level",
]

NUMERIC_COLUMNS = [
    "temperature_c",
    "humidity_pct",
    "occupancy_count",
]

VALID_TARIFFS = {"low", "medium", "high"}


def clean_data(df):
    """Convert numeric fields and remove duplicate complete rows."""
    clean_df = df.copy()

    for column in NUMERIC_COLUMNS:
        clean_df[column] = pd.to_numeric(
            clean_df[column],
            errors="coerce",
        )

    clean_df = clean_df.drop_duplicates().reset_index(drop=True)

    return clean_df


def validate_data(df):
    """Validate the dataset's required fields and value ranges."""
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("Dataset is empty")

    if df[REQUIRED_COLUMNS].isna().any().any():
        raise ValueError("Missing or invalid values found")

    if df["scenario_id"].astype(str).str.strip().eq("").any():
        raise ValueError("Empty scenario_id found")

    if df["scenario_id"].duplicated().any():
        raise ValueError("Duplicate scenario IDs found")

    if not df["temperature_c"].between(18, 45).all():
        raise ValueError(
            "Temperature outside allowed range 18-45°C"
        )

    if not df["humidity_pct"].between(0, 100).all():
        raise ValueError(
            "Humidity outside allowed range 0-100%"
        )

    if not df["occupancy_count"].between(0, 100).all():
        raise ValueError(
            "Occupancy outside allowed range 0-100"
        )

    if not df["tariff_level"].isin(VALID_TARIFFS).all():
        raise ValueError("Invalid tariff level found")

    return True


def main():
    if not os.path.isfile(INPUT_FILE):
        raise FileNotFoundError(
            f"Raw dataset not found: {INPUT_FILE}"
        )

    # Load the original raw dataset.
    df = pd.read_csv(INPUT_FILE)

    print("Raw rows:", len(df))

    # Clean and validate the data.
    clean_df = clean_data(df)

    print("Cleaned rows:", len(clean_df))
    print("Duplicates removed:", len(df) - len(clean_df))

    validate_data(clean_df)

    # Save processed data separately; do not overwrite the raw file.
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    clean_df.to_csv(OUTPUT_FILE, index=False)

    print("VALIDATION PASSED")
    print("Cleaned data saved to", OUTPUT_FILE)


if __name__ == "__main__":
    main()

