import pandas as pd
import numpy as np
import os

RANDOM_SEED = 42
NUM_SCENARIOS = 10000

def generate_scenarios():
    np.random.seed(RANDOM_SEED)

    scenario_ids = [f"SC{i:05d}" for i in range(1, NUM_SCENARIOS + 1)]

    temperatures = np.random.uniform(18, 45, NUM_SCENARIOS)
    humidity = np.random.uniform(20, 100, NUM_SCENARIOS)
    occupancy = np.random.randint(0, 101, NUM_SCENARIOS)

    tariffs = np.random.choice(
        ["low", "medium", "high"],
        size=NUM_SCENARIOS,
        p=[0.35, 0.35, 0.30]
    )

    df = pd.DataFrame({
        "scenario_id": scenario_ids,
        "temperature_c": temperatures.round(2),
        "humidity_pct": humidity.round(2),
        "occupancy_count": occupancy,
        "tariff_level": tariffs
    })

    return df

def main():
    df = generate_scenarios()

    os.makedirs("data/raw", exist_ok=True)

    output_file = "data/raw/generated_scenarios.csv"
    df.to_csv(output_file, index=False)

    print("SCENARIO GENERATION COMPLETE")
    print("Total scenarios:", len(df))
    print("Random seed:", RANDOM_SEED)
    print("Output file:", output_file)
    print("\nFirst 5 scenarios:")
    print(df.head())

if __name__ == "__main__":
    main()