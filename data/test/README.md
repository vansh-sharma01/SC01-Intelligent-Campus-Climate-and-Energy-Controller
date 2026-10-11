# Test Scenario Documentation

## 1. Purpose

These test scenarios verify the fuzzy controller's behavior under normal operating conditions, boundary conditions, and high-demand stress conditions. Separate invalid-input tests verify that the data validator rejects incorrect data.

## 2. Valid Scenario Coverage

The file `scenario_coverage.csv` contains 10 synthetic test scenarios:

| Scenario type | Count | Purpose |
|---|---:|---|
| Normal | 3 | Test typical operating conditions |
| Boundary | 4 | Test input limits and important thresholds |
| Stress | 3 | Test high-temperature, high-humidity, and high-occupancy conditions |
| **Total** | **10** | |

These scenarios are manually defined test cases, not real campus measurements or a random sample of campus operations.

## 3. Fuzzy Controller Results

The controller outputs for all 10 scenarios are saved in `../../results/step4/scenario_coverage_results.csv`.

Verification confirmed:
- 10 result rows were generated.
- No output values are missing.
- Fan levels and energy actions are stored in separate columns.
- All 10 scenarios produced controller outputs.

## 4. Invalid-Input Tests

The file `invalid_scenarios.csv` contains five invalid cases:

- `INVALID-TEMP`: temperature exceeds the permitted range.
- `INVALID-HUMIDITY`: humidity exceeds the permitted range.
- `INVALID-OCCUPANCY`: occupancy is negative.
- `INVALID-TARIFF`: tariff level is unsupported.
- `INVALID-MISSING`: humidity is missing.

Each case was tested individually using `src/validate_data.py`. All five were rejected as expected.

The separate file `invalid_input.csv` also tests a non-numeric temperature value (`abc`), which the validator rejects.

## 5. Reproducibility

Run these commands from the repository root.

### Generate fuzzy-controller results

```bash
python3 src/run_scenario_coverage.py
```

This reads `data/test/scenario_coverage.csv`, applies the fuzzy controller to all scenarios, and writes the results to `results/step4/scenario_coverage_results.csv`.

### Verify scenario counts

```bash
python3 -c "import pandas as pd; d=pd.read_csv('data/test/scenario_coverage.csv'); print(d['scenario_type'].value_counts()); print('Total scenarios:', len(d))"
```

### Test invalid input rejection

```bash
python3 src/validate_data.py data/test/invalid_input.csv
```

This command is expected to exit with a failure because the input contains a non-numeric temperature (`abc`). The five cases in `invalid_scenarios.csv` were also tested individually, and all five were rejected.

The original generated dataset under `data/raw/` was not modified by these tests.
