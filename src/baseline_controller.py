import pandas as pd
import os


TEST_CASES = [
    {
        "scenario_id": "SC01-001",
        "temperature_c": 24,
        "humidity_pct": 50,
        "occupancy_count": 20,
        "tariff_level": "low",
        "expected": (50, "medium", "normal"),
    },
    {
        "scenario_id": "SC01-002",
        "temperature_c": 36,
        "humidity_pct": 85,
        "occupancy_count": 45,
        "tariff_level": "medium",
        "expected": (90, "high", "normal"),
    },
    {
        "scenario_id": "SC01-003",
        "temperature_c": 38,
        "humidity_pct": 60,
        "occupancy_count": 0,
        "tariff_level": "high",
        "expected": (0, "off", "avoid_peak"),
    },
    {
        "scenario_id": "SC01-004",
        "temperature_c": 45,
        "humidity_pct": 70,
        "occupancy_count": 50,
        "tariff_level": "high",
        "expected": (90, "medium", "avoid_peak"),
    },
    {
        "scenario_id": "SC01-005",
        "temperature_c": 21,
        "humidity_pct": 90,
        "occupancy_count": 15,
        "tariff_level": "low",
        "expected": (10, "medium", "normal"),
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
    passed = 0

    for case in TEST_CASES:
        cooling, fan, action = baseline_controller(
            case["temperature_c"],
            case["humidity_pct"],
            case["occupancy_count"],
            case["tariff_level"],
        )

        actual = (cooling, fan, action)
        expected = case["expected"]

        status = "PASS" if actual == expected else "FAIL"

        if status == "PASS":
            passed += 1

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
                "status": status,
            }
        )

    results_df = pd.DataFrame(results)

    os.makedirs("results/step3", exist_ok=True)

    output_file = "results/step3/baseline_results.csv"
    results_df.to_csv(output_file, index=False)

    print("\nSTEP 3 BASELINE CONTROLLER TEST RESULTS")
    print("=" * 80)
    print(results_df.to_string(index=False))
    print("=" * 80)
    print(f"Tests passed: {passed}/{len(TEST_CASES)}")

    if passed == len(TEST_CASES):
        print("STEP 3 BASELINE CONTROLLER PASSED")
    else:
        print("STEP 3 BASELINE CONTROLLER FAILED")

    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
