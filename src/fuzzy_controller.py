import pandas as pd
import os


def fuzzy_controller(row):
    temperature = row["temperature_c"]
    humidity = row["humidity_pct"]
    occupancy = row["occupancy_count"]
    tariff = row["tariff_level"]

    if occupancy == 0:
        cooling = 0
        fan = "off"
    elif temperature < 24:
        cooling = 20
        fan = "low"
    elif temperature <= 30:
        cooling = 60
        fan = "medium"
    else:
        cooling = 90
        fan = "high"

    if humidity > 75 and fan != "off":
        if fan == "low":
            fan = "medium"
        elif fan == "medium":
            fan = "high"

    if tariff == "high":
        energy_action = "avoid_peak"
    else:
        energy_action = "normal"

    return pd.Series({
        "cooling_pct": cooling,
        "fan_level": fan,
        "energy_action": energy_action
    })


if __name__ == "__main__":
    input_file = "data/sample_input.csv"
    output_file = "results/step4/fuzzy_results.csv"

    df = pd.read_csv(input_file)
    results = df.apply(fuzzy_controller, axis=1)

    output = pd.concat([df, results], axis=1)

    os.makedirs("results/step4", exist_ok=True)
    output.to_csv(output_file, index=False)

    print("Fuzzy controller executed successfully.")
    print(f"Results saved to {output_file}")
