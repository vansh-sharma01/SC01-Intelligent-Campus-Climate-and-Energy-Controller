# SC01 - Baseline Pseudocode

## Purpose

This baseline controller provides a simple rule-based recommendation
for room cooling and energy usage. It will later be compared with
the Soft Computing fuzzy controller.

## Inputs

- temperature_c: Room temperature in degrees Celsius
- humidity_pct: Relative humidity in percentage
- occupancy_count: Number of people in the room
- tariff_level: Electricity tariff level (low, medium, high)

## Outputs

- cooling_pct: Recommended cooling percentage (0-100)
- fan_level: Recommended fan level (off, low, medium, high)
- energy_action: Energy recommendation (normal, save, avoid_peak)

## Baseline Rules

1. If occupancy_count is 0:
   - Set cooling_pct to 0.
   - Set fan_level to off.

2. Otherwise, if temperature_c is below 24:
   - Set cooling_pct to 10%.

3. Otherwise, if temperature_c is between 24 and 30:
   - Set cooling_pct to 50%.

4. Otherwise:
   - Set cooling_pct to 90%.

5. If humidity_pct is above 75%:
   - Increase fan_level by one level.

6. If tariff_level is high:
   - Set energy_action to avoid_peak.
   - Otherwise set energy_action to normal.

## Pseudocode

READ one valid input row

IF the row is invalid:
    SHOW a clear error
ELSE:
    IF occupancy_count is 0:
        cooling_pct = 0
        fan_level = off
    ELSE IF temperature_c < 24:
        cooling_pct = 10
        fan_level = low
    ELSE IF temperature_c <= 30:
        cooling_pct = 50
        fan_level = medium
    ELSE:
        cooling_pct = 90
        fan_level = high

    IF humidity_pct > 75:
        INCREASE fan_level by one band

    IF tariff_level == high:
        energy_action = avoid_peak
    ELSE:
        energy_action = normal

    PRINT cooling_pct
    PRINT fan_level
    PRINT energy_action

SAVE the result for later comparison

## Important Assumptions

- The temperature thresholds are temporary baseline thresholds.
- The humidity threshold of 75% is a temporary assumption.
- The baseline is a simple rule-based controller, not fuzzy logic,
  an ANN, or a Genetic Algorithm.
