# Starter Dataset Documentation

## Purpose

This file documents the fields, units, sources, and assumptions used in the
starter dataset for the Intelligent Campus Climate and Energy Controller.

## Dataset File

The starter dataset is stored in:

`data/sample_input.csv`

The dataset contains 20 starter scenarios used for initial validation and
baseline controller testing.

## Fields

| Field | Meaning | Unit / Type | Valid Range / Values |
|---|---|---|---|
| `scenario_id` | Unique identifier for each scenario | Text | Unique value |
| `temperature_c` | Room temperature | °C | 18–45 °C for starter scenarios |
| `humidity_pct` | Relative humidity | % | 20–100% |
| `occupancy_count` | Number of people present in the room | People / integer | 0 to room capacity |
| `tariff_level` | Electricity tariff category | Category | `low`, `medium`, `high` |

## Output Fields

The controller will produce the following recommendations:

| Output | Meaning | Values |
|---|---|---|
| `cooling_pct` | Recommended cooling intensity | 0–100% |
| `fan_level` | Recommended fan level | `off`, `low`, `medium`, `high` |
| `energy_action` | Recommended energy-management action | `normal`, `save`, `avoid_peak` |

## Data Source

The starter dataset is a **synthetic project fixture** created for development,
testing, and validation.

It is not collected from a live campus building and should not be treated as
real measured campus data.

## Assumptions

1. Temperature is measured in degrees Celsius.
2. Humidity represents relative humidity as a percentage.
3. Occupancy is represented as a whole-number count of people.
4. Occupancy cannot be negative.
5. A room with zero occupants can use an energy-saving rule.
6. The starter room capacity is assumed to be sufficient for the provided
   occupancy values.
7. Tariff level is represented using three categories: `low`, `medium`, and
   `high`.
8. Starter temperature values are designed to cover comfortable, warm, hot,
   and boundary conditions.
9. The dataset is intended for testing the baseline controller before larger
   scenario generation begins.
10. The starter dataset does not represent actual energy consumption or actual
    HVAC measurements.

## Validation Rules

The validation program checks that:

- Required columns are present.
- Required values are not missing.
- Temperature is numeric.
- Humidity is numeric.
- Occupancy is numeric.
- Temperature is within the accepted validation range.
- Humidity is between 0 and 100%.
- Occupancy is not negative.
- Tariff level is `low`, `medium`, or `high`.
- Each `scenario_id` is unique.

## Invalid Test Data

An intentionally invalid dataset is stored at:

`data/test/invalid_input.csv`

It contains an invalid temperature value (`abc`) to verify that the validation
program correctly rejects malformed data.

## Future Data

After Step 1 approval, the project may generate a larger reproducible dataset
containing 10,000 or more scenarios for Soft Computing experiments.

## Reference Sources

The starter dataset is synthetic and was created for project development and
testing. The following references are used to support the environmental
assumptions and terminology used in the project:

- ASHRAE Standard 55:
  https://www.ashrae.org/technical-resources/bookstore/standard-55-thermal-environmental-conditions-for-human-occupancy

- U.S. Environmental Protection Agency - Indoor Air Quality:
  https://www.epa.gov/indoor-air-quality-iaq

- Bureau of Energy Efficiency, India:
  https://beeindia.gov.in/

These sources provide background information related to thermal comfort,
indoor environmental conditions, and energy efficiency. They do not provide
the actual rows in `sample_input.csv`.

The 20-row starter dataset is a synthetic fixture created by the project team.
                                                                                                                                                                                                    
