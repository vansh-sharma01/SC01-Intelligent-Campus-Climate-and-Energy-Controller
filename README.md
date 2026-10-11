# SC01 – Intelligent Campus Climate and Energy Controller

## 1. Project Overview

SC01 is an Intelligent Campus Climate and Energy Controller that recommends room cooling, fan settings, and energy actions based on environmental conditions, occupancy, and electricity tariff.

The project compares a deterministic rule-based baseline controller with a fuzzy-logic controller. It also provides a Streamlit interface for interactive testing and scripts for generating comparison visualizations.

**Intended user:** Campus facility managers who need interpretable recommendations for managing classroom or room climate while considering energy use.

**Important limitation:** This project produces recommendations using synthetic scenarios and defined controller rules. It is a prototype, not a validated real-world building-control system.

## 2. Problem Statement

Given a room's environmental conditions, occupancy, and electricity tariff, the system recommends:

- Cooling percentage.
- Fan operating level.
- Energy-management action.

The project investigates how a fuzzy-logic controller's recommendations differ from a fixed-threshold baseline.

## 3. Input and Output Variables

### Inputs

| Variable | Description | Unit or permitted values |
|---|---|---|
| `scenario_id` | Unique scenario identifier | Text |
| `temperature_c` | Room temperature | °C |
| `humidity_pct` | Relative humidity | % |
| `occupancy_count` | Number of people in the room | Non-negative integer |
| `tariff_level` | Electricity tariff category | `low`, `medium`, `high` |

### Outputs

| Variable | Description | Values |
|---|---|---|
| `cooling_pct` | Recommended cooling level | 0–100% |
| `fan_level` | Recommended fan operating level | `off`, `low`, `medium`, `high` |
| `energy_action` | Recommended energy action | `normal`, `save`, `avoid_peak` |

## 4. Controllers

### Rule-Based Baseline

The baseline uses deterministic rules:

1. If occupancy is zero, cooling is set to 0% and the fan is switched off.
2. If the room temperature is below 24°C, cooling is set to 10%.
3. If the temperature is from 24°C through 30°C, cooling is set to 50%.
4. If the temperature is above 30°C, cooling is set to 90%.
5. If humidity is above 75%, the fan level is increased by one level, subject to the controller's defined limits.
6. If the tariff is `high`, the energy action is `avoid_peak`; otherwise, the baseline action is `normal`.

See `docs/baseline-pseudocode.md` for the baseline logic.

### Fuzzy-Logic Controller

The fuzzy controller uses fuzzy membership and rule-based reasoning to produce cooling and fan recommendations. Its outputs may differ from those of the fixed-threshold baseline.

The controllers provide recommendations for experimentation; their outputs should not be interpreted as proof of actual energy savings.

## 5. Dataset and Data Quality

The project includes a reproducible synthetic scenario dataset.

- Raw dataset: `data/raw/generated_scenarios.csv`
- Expected dataset size: 10,000 scenarios and 5 input columns.
- Generation script: `src/generate_scenarios.py`
- Random seed: 42.
- Preparation script: `src/prepare_data.py`
- Cleaned dataset: `data/processed/cleaned_input.csv`
- Quality report: `data/reports/data_quality_report.md`
- Inspection notebook: `notebooks/01_data_inspection.ipynb`

The generated scenarios are **synthetic testing data, not real campus measurements**. The quality report documents the dataset's ranges, tariff distribution, missing values, duplicates, and preparation results.

The preparation pipeline is intended to preserve the raw input and write the prepared data separately.

For dataset details and assumptions, see `data/README.md` and `data/reports/data_quality_report.md`.

## 6. Scenario Coverage and Testing

The project includes normal, boundary, and stress test scenarios.

- Scenario definitions: `data/test/scenario_coverage.csv`
- Invalid test cases: `data/test/invalid_scenarios.csv`
- Additional invalid input: `data/test/invalid_input.csv`
- Coverage execution script: `src/run_scenario_coverage.py`
- Coverage results: `results/step4/scenario_coverage_results.csv`

The invalid fixtures are intended to check rejection of out-of-range temperatures, invalid humidity, negative occupancy, unsupported tariff values, and missing or malformed input data.

A test should be considered passed only after its actual execution and expected outcome have been verified.

## 7. Interactive Dashboard

The Streamlit dashboard lets a user enter room conditions and compare baseline and fuzzy-controller recommendations.

From the project root, run:

```bash
streamlit run app/app.py
```

The terminal will display a local URL. Open that URL in your browser to use the interface. Stop the server with `Ctrl+C` in the terminal when finished.

## 8. Generate Comparison Visualizations

Run the visualization script from the project root:

```bash
python3 src/generate_visuals.py
```

The script compares the baseline and fuzzy results and checks that the scenarios and shared inputs match before generating the charts.

Generated files:

- `results/figures/cooling_comparison.png`
- `results/figures/fan_level_comparison.png`

The charts are useful for comparing controller outputs; they do not independently establish real-world energy savings.

## 9. Evaluate the Controllers

The evaluation script is:

```bash
python3 src/evaluate_controllers.py
```

The evaluation output is saved under:

`results/step6/evaluation_summary.csv`

The existing evaluation compares baseline and fuzzy-controller results. It should not be confused with the official SC01 roadmap's later genetic-algorithm tuning stage.

## 10. Setup and Validation

Use Python 3 and run the following commands from the repository root.

Install the project's declared dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Validate the default starter dataset:

```bash
python3 src/validate_data.py
```

Validate the generated 10,000-row dataset:

```bash
python3 src/validate_data.py data/raw/generated_scenarios.csv
```

Prepare the dataset:

```bash
python3 src/prepare_data.py
```

Run scenario coverage:

```bash
python3 src/run_scenario_coverage.py
```

Generate comparison charts:

```bash
python3 src/generate_visuals.py
```

Run controller evaluation:

```bash
python3 src/evaluate_controllers.py
```

Run the interactive dashboard:

```bash
streamlit run app/app.py
```

Run commands from the repository root so that relative file paths resolve correctly. An invalid-data validation command is expected to return a non-zero exit status when the supplied input violates validation rules.

## 11. Project Structure

```text
SC01-Intelligent-Campus-Climate-and-Energy-Controller/
├── app/
│   └── app.py
├── data/
│   ├── raw/
│   │   └── generated_scenarios.csv
│   ├── processed/
│   │   └── cleaned_input.csv
│   ├── reports/
│   │   └── data_quality_report.md
│   ├── test/
│   │   ├── README.md
│   │   ├── invalid_input.csv
│   │   ├── invalid_scenarios.csv
│   │   └── scenario_coverage.csv
│   ├── sample_input.csv
│   └── README.md
├── docs/
│   ├── STEP-1.md
│   └── baseline-pseudocode.md
├── notebooks/
│   └── 01_data_inspection.ipynb
├── results/
│   ├── figures/
│   │   ├── cooling_comparison.png
│   │   └── fan_level_comparison.png
│   ├── step3/
│   │   └── baseline_results.csv
│   ├── step4/
│   │   ├── fuzzy_results.csv
│   │   └── scenario_coverage_results.csv
│   ├── step5/
│   │   └── controller_comparison.csv
│   └── step6/
│       └── evaluation_summary.csv
├── src/
│   ├── baseline_controller.py
│   ├── evaluate_controllers.py
│   ├── fuzzy_controller.py
│   ├── generate_scenarios.py
│   ├── generate_visuals.py
│   ├── prepare_data.py
│   ├── run_scenario_coverage.py
│   └── validate_data.py
├── requirements.txt
└── README.md
```

This is a summary of the principal project files, not an exhaustive listing of every repository file.

## 12. Team Workflow

### Team Members

- Vansh Sharma
- Manshi Tiwari
- Lakshya Sharma
- Akash Dubey

### Git Workflow

Each team member should make a meaningful contribution, test the change, commit it with a clear message, and push it to the appropriate shared branch.

Before committing, inspect the working tree and check for whitespace errors:

```bash
git status
git diff --check
```

Stage only the files intended for the commit. Review the staged changes before committing and pushing.

## 13. Development Status and Remaining Roadmap

### Implemented components

- Project inputs, outputs, and baseline rules.
- Reproducible synthetic scenario generation and data preparation.
- Dataset validation and data-quality reporting.
- Baseline and fuzzy controllers.
- Baseline-versus-fuzzy comparison and evaluation outputs.
- Normal, boundary, and stress scenario coverage artifacts.
- Streamlit dashboard and comparison-chart generation.

These components have been developed in the repository; each test and deliverable must still be verified against its relevant guide and evidence requirements.

### Remaining official SC01 roadmap work

The official roadmap contains additional requirements beyond the existing controller evaluation:

1. Verify the Product V1 interface and collect the required demonstration evidence.
2. Implement and document genetic-algorithm tuning of fuzzy membership functions or rules.
3. Compare the baseline, fuzzy controller, and GA-tuned fuzzy controller using consistent scenarios and appropriate evaluation metrics.
4. Conduct parameter experiments and difficult-case testing.
5. Complete deployment, final report, presentation, demonstration video, and viva preparation as required.

The current baseline-versus-fuzzy evaluation does **not** establish that the GA-tuning stage is complete. The project should only be declared complete when the required roadmap deliverables and evidence have been checked.

