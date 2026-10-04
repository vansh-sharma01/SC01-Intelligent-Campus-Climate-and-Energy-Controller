import pandas as pd
import sys

FILE = sys.argv[1] if len(sys.argv) > 1 else "data/raw/generated_scenarios.csv"

REQUIRED = [
    "scenario_id",
    "temperature_c",
    "humidity_pct",
    "occupancy_count",
    "tariff_level"
]

NUMERIC = [
    "temperature_c",
    "humidity_pct",
    "occupancy_count"
]

try:
    df = pd.read_csv(FILE)

    print("File:", FILE)
    print("Shape:", df.shape)
    print("Missing values:")
    print(df.isna().sum())

    missing_columns = [c for c in REQUIRED if c not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    if df[REQUIRED].isna().any().any():
        raise ValueError("Missing value found")

    for column in NUMERIC:
        df[column] = pd.to_numeric(df[column], errors="raise")

    if df["scenario_id"].astype(str).str.strip().eq("").any():
        raise ValueError("Empty scenario ID found")

    if df["scenario_id"].duplicated().any():
        raise ValueError("Duplicate scenario_id found")

    if not df["temperature_c"].between(18, 45).all():
        raise ValueError("Temperature must be between 18 and 45°C")

    if not df["humidity_pct"].between(20, 100).all():
        raise ValueError("Humidity must be between 20 and 100%")

    if not df["occupancy_count"].between(0, 100).all():
        raise ValueError("Occupancy must be between 0 and 100")

    valid_tariffs = ["low", "medium", "high"]

    if not df["tariff_level"].isin(valid_tariffs).all():
        raise ValueError("Invalid tariff level")

    print("\nDATA VALIDATION PASSED")

except (ValueError, KeyError) as e:
    print("\nDATA VALIDATION FAILED")
    print("Reason:", e)
    sys.exit(1)
