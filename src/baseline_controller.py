import pandas as pd


TEST_CASES = [
    {
        "scenario_id": "SC01-001",
        "temperature_c": 24,
        "humidity_pct": 50,
        "occupancy_count": 20,
        "tariff_level": "low",
    },
    {
        "scenario_id": "SC01-002",
        "temperature_c": 36,
        "humidity_pct": 85,
        "occupancy_count": 45,
        "tariff_level": "medium",
    },
    {
        "scenario_id": "SC01-003",
        "temperature_c": 38,
        "humidity_pct": 60,
        "occupancy_count": 0,
        "tariff_level": "high",
    },
    {
        "scenario_id": "SC01-004",
        "temperature_c": 45,
        "humidity_pct": 70,
        "occupancy_count": 50,
        "tariff_level": "high",
    },
    {
        "scenario_id": "SC01-005",
        "temperature_c": 21,
        "humidity_pct": 90,
        "occupancy_count": 15,
        "tariff_level": "low",
    },
]


def baseline_controller(
    temperature_c,
    humidity_pct,
    occupancy_count,
    tariff_level,
):
    if occupancy_count == 0:
        cooling_pct = 0
        fan_level = "off"
    elif temperature_c < 24:
        cooling_pct = 10
        fan_level = "low"
    elif temperature_c <= 30:
        cooling_pct = 50
        fan_level = "medium"
    else:
        cooling_pct = 90
        fan_level = "medium"

    if humidity_pct > 75 and fan_level != "off":
        fan_levels = ["off", "low", "medium", "high"]
        current_index = fan_levels.index(fan_level)

        if current_index < len(fan_levels) - 1:
            fan_level = fan_levels[current_index + 1]

    if tariff_level == "high":
        energy_action = "avoid_peak"
    else:
        energy_action = "normal"

    return cooling_pct, fan_level, energy_action


def main():
    results = []

    for case in TEST_CASES:
        cooling, fan, action = baseline_controller(
            case["temperature_c"],
            case["humidity_pct"],
            case["occupancy_count"],
            case["tariff_level"],
        )

        results.append(
            {
                "scenario_id": case["scenario_id"],
                "temperature_c": case["temperature_c"],
                "humidity_pct": case["humidity_pct"],
                "occupancy_count": case["occupancy_count"],
                "tariff_level": case["tariff_level"],
                "cooling_pct": cooling,
                "fan_level": fan,
                "energy_action": action,
            }
        )

    results_df = pd.DataFrame(results)

    print("\nSTEP 1 BASELINE TEST CASE RESULTS")
    print("=" * 70)
    print(results_df.to_string(index=False))
    print("=" * 70)
    print("All five mandatory test cases executed successfully.")


if __name__ == "__main__":
    main()
