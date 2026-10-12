# Dataset Documentation — SC01

## 1. Purpose

This document describes the datasets used by the Intelligent Campus Climate and Energy Controller. The data supports input validation, baseline controller testing, fuzzy controller experiments, and scenario-based evaluation.

**Important:** All project datasets described here are synthetic testing data. They are not measurements collected from a live campus building.

## 2. Dataset Files

| File | Description | Records |
|---|---|---:|
| `data/sample_input.csv` | Starter dataset for initial validation and controller testing | 20 |
| `data/raw/generated_scenarios.csv` | Generated dataset for larger-scale experiments | 10,000 |
| `data/processed/cleaned_input.csv` | Processed output produced by the data preparation pipeline | 10,000 |
| `data/test/invalid_input.csv` | Test fixture containing a non-numeric temperature | 1 |
| `data/test/invalid_scenarios.csv` | Test cases containing invalid values | 5 |

The original generated dataset is retained in `data/raw/`. Data preparation writes the processed dataset to `data/processed/cleaned_input.csv`.

## 3. Fields and Units

| Field | Meaning | Unit / Type | Accepted Values |
|---|---|---|---|
| `scenario_id` | Unique scenario identifier | Text | Non-empty and unique |
| `temperature_c` | Room temperature | Degrees Celsius | 18–45°C |
| `humidity_pct` | Relative humidity | Percentage | 0–100% |
| `occupancy_count` | Number of people in the room | Non-negative number | 0 or greater |
| `tariff_level` | Electricity tariff category | Categorical text | `low`, `medium`, `high` |

The generated dataset uses temperatures between 18°C and 45°C, humidity between 0% and 100%, and occupancy counts between 0 and 100.

## 4. Controller Output Fields

| Output | Meaning | Values |
|---|---|---|
| `cooling_pct` | Recommended cooling intensity | 0–100% |
| `fan_level` | Recommended fan level | `off`, `low`, `medium`, `high` |
| `energy_action` | Recommended energy-management action | `normal`, `save`, `avoid_peak` |

These fields are controller outputs, not measured energy-consumption values.

## 5. Data Source and Generation

The starter dataset and generated scenarios are created for this project. The generated dataset is produced by:

`src/generate_scenarios.py`

The generation process uses a fixed random seed of **42** for repeatability. The generated tariff distribution is configured with target proportions of approximately 35% low, 35% medium, and 30% high.

The generated CSV contains 10,000 scenarios. The seed makes the generation process reproducible when the script and its generation logic remain unchanged.

No external dataset is claimed as the source of the generated records.

## 6. Assumptions and Limitations

1. Temperature is expressed in degrees Celsius.
2. Humidity represents relative humidity as a percentage.
3. Occupancy represents a non-negative count of people.
4. Scenario identifiers must be unique and non-empty.
5. The room may be unoccupied; zero occupancy is a valid scenario.
6. Tariff levels are represented by `low`, `medium`, and `high`.
7. The generated scenarios are intended for software testing and controller comparison.
8. Synthetic scenarios do not establish real-world HVAC performance or energy savings.
9. The datasets do not contain measured energy consumption or validated building sensor readings.
10. Results from these datasets should not be interpreted as proof of real-world performance without testing against suitable real measurements.

## 7. Validation Rules

The reusable validator is located at `src/validate_data.py`.

It checks:

- Required columns are present.
- Required values are not missing.
- Scenario identifiers are non-empty and unique.
- Temperature, humidity, and occupancy fields are numeric.
- Temperature is between 18°C and 45°C, inclusive.
- Humidity is between 0% and 100%, inclusive.
- Occupancy is non-negative.
- Tariff level is `low`, `medium`, or `high`.

## 8. Data Preparation and Repeatability

From the repository root, use these commands:

Generate the scenarios:

`python3 src/generate_scenarios.py`

Validate the generated dataset:

`python3 src/validate_data.py data/raw/generated_scenarios.csv`

Prepare the processed dataset:

`python3 src/prepare_data.py`

Validate the starter dataset:

`python3 src/validate_data.py data/sample_input.csv`

Inspect the dataset using the executed notebook:

`notebooks/01_data_inspection.ipynb`

The data quality summary is maintained at:

`data/reports/data_quality_report.md`

The preparation pipeline is intended to preserve the raw dataset and write its cleaned output separately.

## 9. Data Quality and Testing

The generated dataset has been checked for row count, missing values, duplicate scenario identifiers, numeric ranges, and tariff distribution. The corresponding results are recorded in `data/reports/data_quality_report.md`.

Additional normal, boundary, and stress scenarios are stored in `data/test/scenario_coverage.csv`. Invalid-input fixtures are stored under `data/test/`.

These fixtures test input handling and scenario coverage; they are not additional real-world observations.

## 10. Reference Sources

The following sources provide background on thermal comfort, indoor environmental conditions, and energy efficiency. They are **background references, not sources of the generated CSV rows**.

- ASHRAE Standard 55 — Thermal Environmental Conditions for Human Occupancy: https://www.ashrae.org/technical-resources/bookstore/standard-55-thermal-environmental-conditions-for-human-occupancy
- U.S. Environmental Protection Agency — Indoor Air Quality: https://www.epa.gov/indoor-air-quality-iaq
- Bureau of Energy Efficiency, India: https://beeindia.gov.in/

## 11. Data Integrity Statement

The project distinguishes synthetic scenarios from real measurements. The raw generated dataset is retained separately from the processed dataset, and the generation script and quality report document the workflow used for experiments.
