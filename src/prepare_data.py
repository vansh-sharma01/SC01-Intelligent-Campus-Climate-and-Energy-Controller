import pandas as pd
import os


INPUT_FILE = "data/raw/sample_input.csv"
OUTPUT_DIR = "data/processed"


def clean_data(df):
    clean_df = df.copy()

    numeric_columns = [
        "temperature_c",
        "humidity_pct",
        "occupancy_count"
    ]

    for column in numeric_columns:
        clean_df[column] = pd.to_numeric(clean_df[column], errors="coerce")
        clean_df[column] = clean_df[column].fillna(clean_df[column].median())

    clean_df = clean_df.drop_duplicates().reset_index(drop=True)

    return clean_df


def validate_data(df):
    required_columns = [
        "scenario_id",
        "temperature_c",
        "humidity_pct",
        "occupancy_count",
        "tariff_level"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    if df["scenario_id"].duplicated().any():
        raise ValueError("Duplicate scenario IDs found")

    if df["temperature_c"].isna().any():
        raise ValueError("Invalid temperature values found")

    if df["humidity_pct"].isna().any():
        raise ValueError("Invalid humidity values found")

    if df["occupancy_count"].isna().any():
        raise ValueError("Invalid occupancy values found")

    if not df["temperature_c"].between(18, 45).all():
        raise ValueError("Temperature outside allowed range 18-45 C")

    if not df["humidity_pct"].between(20, 100).all():
        raise ValueError("Humidity outside allowed range 20-100 percent")

    if not df["occupancy_count"].between(0, 100).all():
        raise ValueError("Occupancy outside allowed range 0-100")

    valid_tariffs = {"low", "medium", "high"}

    if not df["tariff_level"].isin(valid_tariffs).all():
        raise ValueError("Invalid tariff level found")

    return True


def main():
    df = pd.read_csv(INPUT_FILE)

    print("Raw rows:", len(df))

    clean_df = clean_data(df)

    print("Cleaned rows:", len(clean_df))
    print("Duplicates removed:", len(df) - len(clean_df))

    validate_data(clean_df)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_file = os.path.join(
        OUTPUT_DIR,
        "cleaned_input.csv"
    )

    clean_df.to_csv(output_file, index=False)

    print("VALIDATION PASSED")
    print(f"Cleaned data saved to {output_file}")


if __name__ == "__main__":
    main()
