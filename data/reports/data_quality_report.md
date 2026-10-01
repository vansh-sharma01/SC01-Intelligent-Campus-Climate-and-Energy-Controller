# Step 2 Data Quality Report

## 1. Dataset Overview

The dataset used for the Intelligent Campus Climate and Energy Controller
contains synthetic climate, occupancy, and electricity tariff scenarios.

The raw dataset is stored at:

`data/raw/sample_input.csv`

The processed dataset is stored at:

`data/processed/cleaned_input.csv`

The raw dataset contains 20 scenarios.

## 2. Fields

| Field | Type | Description |
|---|---|---|
| `scenario_id` | Text | Unique scenario identifier |
| `temperature_c` | Numeric | Room temperature in °C |
| `humidity_pct` | Numeric | Relative humidity percentage |
| `occupancy_count` | Integer | Number of occupants |
| `tariff_level` | Category | `low`, `medium`, or `high` |

## 3. Missing Values

All required fields were checked for missing values.

Result:

- `scenario_id`: 0 missing
- `temperature_c`: 0 missing
- `humidity_pct`: 0 missing
- `occupancy_count`: 0 missing
- `tariff_level`: 0 missing

## 4. Duplicate Checks

Duplicate scenario IDs:

- 0

Duplicate complete rows:

- 0

Therefore, all 20 starter scenarios have unique scenario IDs and no
duplicate rows.

## 5. Value Ranges

| Field | Minimum | Maximum |
|---|---:|---:|
| `temperature_c` | 18 °C | 45 °C |
| `humidity_pct` | 20% | 100% |
| `occupancy_count` | 0 | 100 |

The observed values are within the documented starter-scenario ranges.

## 6. Tariff Distribution

| Tariff Level | Number of Scenarios |
|---|---:|
| `low` | 7 |
| `medium` | 5 |
| `high` | 8 |
| **Total** | **20** |

All three documented tariff categories are represented.

## 7. Scenario Coverage

The starter dataset includes scenarios covering different combinations
of temperature, humidity, occupancy, and tariff conditions.

The project will use additional reproducible scenarios for normal,
boundary, stress, and invalid-case testing as the Step 2 pipeline is
expanded.

## 8. Validation

The reusable validation and preparation program is:

`src/prepare_data.py`

It checks:

- Required columns are present.
- Numeric climate and occupancy fields can be validated.
- Required values are valid.
- Scenario IDs are unique.
- Temperature is within 18–45 °C.
- Humidity is within 20–100%.
- Occupancy is within 0–100.
- Tariff level is `low`, `medium`, or `high`.

The preparation program successfully processed the 20-row starter dataset.

Execution result:

`VALIDATION PASSED`

## 9. Processing Result

The preparation script created:

`data/processed/cleaned_input.csv`

Raw data remains unchanged in:

`data/raw/sample_input.csv`

## 10. Data Source and Limitations

The starter dataset is synthetic and was created for project development,
testing, and validation.

It is not a collection of real measurements from a campus building.

Environmental assumptions are supported by background references documented
in `data/README.md`.

## 11. Next Step

The next stage of Step 2 will expand the reproducible scenario pipeline
with normal, boundary, stress, and invalid test cases and larger
documented scenario coverage for Soft Computing experiments.
