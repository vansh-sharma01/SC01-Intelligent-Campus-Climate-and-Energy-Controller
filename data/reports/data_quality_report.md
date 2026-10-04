# Step 2: Data Quality Report

## 1. Dataset Overview

The SC01 project uses 10,000 synthetically generated campus climate and energy scenarios for testing and evaluating the baseline and fuzzy controllers.

These records are generated test data and are not real campus measurements.

* **Raw dataset:** `data/raw/generated_scenarios.csv`
* **Processed dataset:** `data/processed/cleaned_input.csv`
* **Generator:** `src/generate_scenarios.py`
* **Random seed:** 42
* **Raw dataset shape:** 10,000 rows × 5 columns
* **Processed dataset shape:** 10,000 rows × 5 columns

## 2. Missing Values

| Column          | Missing Values |
| --------------- | -------------: |
| scenario_id     |              0 |
| temperature_c   |              0 |
| humidity_pct    |              0 |
| occupancy_count |              0 |
| tariff_level    |              0 |

**Result:** No missing values were found.

## 3. Duplicate Records

* Duplicate scenario IDs: 0
* Duplicate complete rows: 0
* Rows removed during preparation: 0

**Result:** No duplicates were found.

## 4. Numeric Data Ranges

| Feature         | Minimum | Maximum | Unit   |
| --------------- | ------: | ------: | ------ |
| temperature_c   |   18.00 |   44.99 | °C     |
| humidity_pct    |   20.01 |   99.99 | %      |
| occupancy_count |       0 |     100 | People |

All observed values fall within the project's configured validation limits.

## 5. Tariff Distribution

Actual counts from the generated dataset:

| Tariff Level | Scenario Count |
| ------------ | -------------: |
| Low          |          3,519 |
| Medium       |          3,506 |
| High         |          2,975 |
| **Total**    |     **10,000** |

The generator uses target probabilities of 35% low, 35% medium, and 30% high. Actual counts vary according to random sampling.

## 6. Scenario Coverage

The generated dataset includes variation in:

* Temperature
* Humidity
* Occupancy
* Electricity tariff

The dataset contains low and high values within the configured ranges, including zero occupancy and full occupancy.

The separate invalid test fixture is located at:

`data/test/invalid_input.csv`

It contains an invalid temperature value (`abc`) for validation testing.

The generated dataset is intended for software testing and controller evaluation, not as a representation of measured campus conditions.

## 7. Data Preparation Process

The preparation pipeline is implemented in:

`src/prepare_data.py`

Process:

1. Load the generated raw CSV.
2. Convert numeric columns to numeric types.
3. Remove duplicate complete rows.
4. Check required columns.
5. Validate scenario IDs and missing values.
6. Check numeric ranges and tariff categories.
7. Save the processed dataset.

Output:

`data/processed/cleaned_input.csv`

The raw dataset is retained unchanged by the preparation process.

## 8. Reproducibility

To regenerate the synthetic dataset:

```bash
python3 src/generate_scenarios.py
```

The fixed random seed is 42.

To prepare and validate the generated data:

```bash
python3 src/prepare_data.py
```

## 9. Validation Summary

* [x] 10,000 generated scenarios
* [x] Required five input columns present
* [x] No missing values
* [x] No duplicate scenario IDs
* [x] Numeric ranges within configured limits
* [x] Valid tariff categories
* [x] Processed CSV generated
* [x] Notebook executed with saved outputs
* [x] Validation passed

**Overall result: DATA QUALITY CHECK PASSED**

**Dataset status:** Synthetic testing data, not real-world campus observations.
