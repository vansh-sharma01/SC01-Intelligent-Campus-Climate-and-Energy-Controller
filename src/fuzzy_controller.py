import os

import numpy as np
import pandas as pd


DEFAULT_PARAMS = {
    "t1": 24.0,
    "t2": 30.0,
    "t3": 36.0,
    "cool_low": 15.0,
    "cool_medium": 55.0,
    "cool_high": 90.0,
}


def _left_shoulder(x, start, end):
    if x <= start:
        return 1.0
    if x >= end:
        return 0.0
    return (end - x) / (end - start)


def _right_shoulder(x, start, end):
    if x <= start:
        return 0.0
    if x >= end:
        return 1.0
    return (x - start) / (end - start)


def _triangle(x, left, peak, right):
    if x <= left or x >= right:
        return 0.0
    if x == peak:
        return 1.0
    if x < peak:
        return (x - left) / (peak - left)
    return (right - x) / (right - peak)


def _memberships(x, low_end, mid_left, mid_peak, mid_right, high_start, high_end):
    return {
        "low": _left_shoulder(x, low_end - 6, low_end),
        "medium": _triangle(x, mid_left, mid_peak, mid_right),
        "high": _right_shoulder(x, high_start, high_end),
    }


def fuzzy_cooling(temperature, humidity, occupancy, params=None):
    p = {**DEFAULT_PARAMS, **(params or {})}

    t1, t2, t3 = p["t1"], p["t2"], p["t3"]
    if not (18 < t1 < t2 < t3 < 45):
        raise ValueError("Temperature parameters must satisfy 18 < t1 < t2 < t3 < 45")

    temp = {
        "low": _left_shoulder(temperature, 18, t1),
        "medium": _triangle(temperature, t1, t2, t3),
        "high": _right_shoulder(temperature, t2, t3),
    }
    occ = {
        "low": _left_shoulder(occupancy, 0, 20),
        "medium": _triangle(occupancy, 10, 50, 85),
        "high": _right_shoulder(occupancy, 60, 100),
    }
    humid = {
        "low": _left_shoulder(humidity, 20, 40),
        "medium": _triangle(humidity, 25, 50, 80),
        "high": _right_shoulder(humidity, 65, 100),
    }

    low = p["cool_low"]
    medium = p["cool_medium"]
    high = p["cool_high"]

    # Zero-order Sugeno rules: each rule contributes a firing strength
    # and a crisp cooling consequent; weighted average gives the output.
    rules = [
        (min(temp["low"], occ["low"]), low),
        (min(temp["low"], occ["medium"]), medium),
        (min(temp["low"], occ["high"]), medium),
        (min(temp["medium"], occ["low"]), medium),
        (min(temp["medium"], occ["medium"]), medium),
        (min(temp["medium"], occ["high"]), high),
        (min(temp["high"], occ["low"]), medium),
        (min(temp["high"], occ["medium"]), high),
        (min(temp["high"], occ["high"]), high),
        (min(temp["medium"], humid["high"]), high),
        (min(temp["low"], humid["high"], occ["high"]), medium),
    ]

    denominator = sum(weight for weight, _ in rules)
    if denominator == 0:
        cooling = low if temperature < t2 else high
    else:
        cooling = sum(weight * value for weight, value in rules) / denominator

    return float(np.clip(cooling, 0, 100))


def fuzzy_controller(row, params=None):
    temperature = float(row["temperature_c"])
    humidity = float(row["humidity_pct"])
    occupancy = float(row["occupancy_count"])
    tariff = str(row["tariff_level"]).lower()

    if occupancy == 0:
        cooling = 0.0
        fan = "off"
    else:
        cooling = fuzzy_cooling(temperature, humidity, occupancy, params)
        if cooling < 30:
            fan = "low"
        elif cooling < 70:
            fan = "medium"
        else:
            fan = "high"

        if humidity >= 80 and fan == "low":
            fan = "medium"
        elif humidity >= 80 and fan == "medium":
            fan = "high"

    return pd.Series({
        "cooling_pct": round(cooling, 2),
        "fan_level": fan,
        "energy_action": "avoid_peak" if tariff == "high" else "normal",
    })


if __name__ == "__main__":
    input_file = "data/sample_input.csv"
    output_file = "results/step4/fuzzy_results.csv"

    df = pd.read_csv(input_file)
    results = df.apply(fuzzy_controller, axis=1)
    output = pd.concat([df, results], axis=1)

    os.makedirs("results/step4", exist_ok=True)
    output.to_csv(output_file, index=False)
    print(f"Fuzzy inference completed. Results saved to {output_file}")
