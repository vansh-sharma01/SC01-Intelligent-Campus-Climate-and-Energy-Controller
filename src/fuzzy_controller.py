import os

import numpy as np
import pandas as pd
import skfuzzy as fuzz
from skfuzzy import control as ctrl


def build_fuzzy_system():
    temperature = ctrl.Antecedent(
        np.arange(18, 45.1, 0.1), "temperature"
    )
    humidity = ctrl.Antecedent(
        np.arange(20, 100.1, 0.1), "humidity"
    )
    occupancy = ctrl.Antecedent(
        np.arange(0, 101, 1), "occupancy"
    )

    cooling = ctrl.Consequent(
        np.arange(0, 100.1, 0.1), "cooling"
    )

    temperature["comfortable"] = fuzz.trimf(
        temperature.universe, [18, 18, 24]
    )
    temperature["warm"] = fuzz.trimf(
        temperature.universe, [22, 27, 32]
    )
    temperature["hot"] = fuzz.trimf(
        temperature.universe, [30, 45, 45]
    )

    humidity["low"] = fuzz.trimf(
        humidity.universe, [20, 20, 50]
    )
    humidity["moderate"] = fuzz.trimf(
        humidity.universe, [40, 60, 80]
    )
    humidity["high"] = fuzz.trimf(
        humidity.universe, [70, 100, 100]
    )

    occupancy["empty"] = fuzz.trimf(
        occupancy.universe, [0, 0, 1]
    )
    occupancy["low"] = fuzz.trimf(
        occupancy.universe, [0, 15, 40]
    )
    occupancy["medium"] = fuzz.trimf(
        occupancy.universe, [25, 50, 75]
    )
    occupancy["high"] = fuzz.trimf(
        occupancy.universe, [60, 100, 100]
    )

    cooling["off"] = fuzz.trimf(
        cooling.universe, [0, 0, 10]
    )
    cooling["low"] = fuzz.trimf(
        cooling.universe, [5, 20, 40]
    )
    cooling["medium"] = fuzz.trimf(
        cooling.universe, [30, 55, 75]
    )
    cooling["high"] = fuzz.trimf(
        cooling.universe, [65, 90, 100]
    )

    rules = [
        ctrl.Rule(
            occupancy["empty"],
            cooling["off"],
            label="empty_room"
        ),
        ctrl.Rule(
            temperature["comfortable"]
            & occupancy["low"],
            cooling["low"],
            label="comfortable_low_occupancy"
        ),
        ctrl.Rule(
            temperature["comfortable"]
            & occupancy["medium"],
            cooling["low"],
            label="comfortable_medium_occupancy"
        ),
        ctrl.Rule(
            temperature["comfortable"]
            & occupancy["high"],
            cooling["medium"],
            label="comfortable_high_occupancy"
        ),
        ctrl.Rule(
            temperature["warm"]
            & occupancy["low"],
            cooling["medium"],
            label="warm_low_occupancy"
        ),
        ctrl.Rule(
            temperature["warm"]
            & occupancy["medium"],
            cooling["medium"],
            label="warm_medium_occupancy"
        ),
        ctrl.Rule(
            temperature["warm"]
            & occupancy["high"],
            cooling["high"],
            label="warm_high_occupancy"
        ),
        ctrl.Rule(
            temperature["hot"]
            & occupancy["low"],
            cooling["high"],
            label="hot_low_occupancy"
        ),
        ctrl.Rule(
            temperature["hot"]
            & occupancy["medium"],
            cooling["high"],
            label="hot_medium_occupancy"
        ),
        ctrl.Rule(
            temperature["hot"]
            & occupancy["high"],
            cooling["high"],
            label="hot_high_occupancy"
        ),
        ctrl.Rule(
            humidity["high"] & temperature["warm"],
            cooling["medium"],
            label="high_humidity_warm"
        ),
        ctrl.Rule(
            humidity["high"] & temperature["hot"],
            cooling["high"],
            label="high_humidity_hot"
        ),
    ]

    system = ctrl.ControlSystem(rules)
    return system


FUZZY_SYSTEM = build_fuzzy_system()


def fuzzy_controller(row):
    temperature = float(row["temperature_c"])
    humidity = float(row["humidity_pct"])
    occupancy = int(row["occupancy_count"])
    tariff = row["tariff_level"]

    if occupancy == 0:
        return pd.Series({
            "cooling_pct": 0,
            "fan_level": "off",
            "energy_action": "avoid_peak" if tariff == "high" else "save"
        })

    simulation = ctrl.ControlSystemSimulation(FUZZY_SYSTEM)

    simulation.input["temperature"] = temperature
    simulation.input["humidity"] = humidity
    simulation.input["occupancy"] = occupancy

    simulation.compute()

    cooling_value = float(simulation.output["cooling"])
    cooling_value = round(np.clip(cooling_value, 0, 100), 1)

    if cooling_value < 30:
        fan_level = "low"
    elif cooling_value < 70:
        fan_level = "medium"
    else:
        fan_level = "high"

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
