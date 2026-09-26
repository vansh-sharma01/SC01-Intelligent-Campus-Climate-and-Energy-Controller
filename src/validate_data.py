import pandas as pd

FILE = "data/sample_input.csv"

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

df = pd.read_csv(FILE)

print("Shape:", df.shape)
print("Columns:", list(df.columns))
print("Missing values:")
print(df.isna().sum())

# Check required columns
missing_columns = [c for c in REQUIRED if c not in df.columns]

if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

# Check missing values
if df[REQUIRED].isna().any().any():
    raise ValueError("Missing value found")

# Check numeric columns
for column in NUMERIC:
    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValueError(f"{column} must be numeric")

# Check temperature
if not df["temperature_c"].between(0, 50).all():
    raise ValueError("Temperature must be between 0 and 50°C")

# Check humidity
if not df["humidity_pct"].between(0, 100).all():
    raise ValueError("Humidity must be between 0 and 100%")

# Check occupancy
if (df["occupancy_count"] < 0).any():
    raise ValueError("Occupancy cannot be negative")

# Check tariff
valid_tariffs = ["low", "medium", "high"]

if not df["tariff_level"].isin(valid_tariffs).all():
    raise ValueError("Invalid tariff level")

# Check unique IDs
if df["scenario_id"].duplicated().any():
    raise ValueError("Duplicate scenario_id found")

print("\nSTEP 1 DATA CHECK PASSED")
