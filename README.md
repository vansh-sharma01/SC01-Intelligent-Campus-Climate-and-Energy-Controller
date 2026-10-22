# Intelligent Campus Climate and Energy Controller

## 1. Project Overview

The Intelligent Campus Climate and Energy Controller is a Soft Computing project that simulates climate-control decisions for campus rooms using temperature, humidity, occupancy, and electricity-tariff information.

The project implements and compares three approaches:

- **Rule-based baseline controller:** Uses fixed thresholds and deterministic rules.
- **Fuzzy-logic controller:** Uses fuzzy membership functions and weighted fuzzy-rule inference to determine cooling output.
- **GA-tuned fuzzy controller:** Uses a genetic algorithm to optimize fuzzy-controller parameters against a synthetic design objective.

The repository includes data-generation and validation tools, controller comparison and evaluation scripts, visualizations, a final report, and an interactive Streamlit dashboard.

## 2. Team Members

| Name | Role |
|---|---|
| Vansh Sharma | Team Leader |
| Manshi Tiwari | Team Member |
| Lakshya Sharma | Team Member |
| Akash Dubey | Team Member |

## 3. Project Objectives

- Generate reproducible climate and occupancy scenarios.
- Validate input data before controller execution.
- Implement a deterministic baseline controller and a fuzzy-logic controller.
- Optimize fuzzy-controller parameters using a genetic algorithm.
- Compare all three controllers using the same scenarios.
- Evaluate cooling outputs, fan levels, and tariff-related actions.
- Generate visualizations and provide an interactive dashboard.
- Maintain reproducible results and document the simulation's limitations.

## 4. Input Data Specification

Each scenario contains the following fields:

| Field | Description | Expected range or values |
|---|---|---|
| `scenario_id` | Unique scenario identifier | Non-empty and unique |
| `temperature_c` | Room temperature in Celsius | 18–45 |
| `humidity_pct` | Relative humidity percentage | 20–100 |
| `occupancy_count` | Number of occupants | Integer from 0–100 |
| `tariff_level` | Electricity tariff category | `low`, `medium`, `high` |

These ranges define the project's simulation input domain.

## 5. Dataset Generation and Preparation

The data pipeline consists of three scripts:

- `src/generate_scenarios.py` — Generates synthetic scenarios.
- `src/prepare_data.py` — Prepares the processed dataset.
- `src/validate_data.py` — Checks input-data quality and validity.

The project generates 10,000 synthetic scenarios using a fixed random seed. Raw and processed datasets are stored separately.

Principal data files:

```text
data/raw/generated_scenarios.csv
data/processed/cleaned_input.csv
data/sample_input.csv
data/test/
data/reports/data_quality_report.md
```

The validation workflow checks the schema, numeric fields, permitted ranges, tariff categories, missing values, and duplicate identifiers.

Run the data pipeline from the repository root:

```bash
python3 src/generate_scenarios.py
python3 src/prepare_data.py
python3 src/validate_data.py data/processed/cleaned_input.csv
```

To validate the sample dataset:

```bash
python3 src/validate_data.py data/sample_input.csv
```

## 6. Data Inspection Notebook

The notebook `notebooks/01_data_inspection.ipynb` supports dataset exploration and includes:

- Dataset shape and column types.
- Sample records and descriptive statistics.
- Missing-value and duplicate-identifier checks.
- Value ranges and tariff-category counts.
- Assertions for expected dataset properties.

Open the notebook in Jupyter to review the analysis and its outputs.

## 7. Baseline Controller

The baseline controller is implemented in `src/baseline_controller.py`.

It applies fixed rules to temperature and occupancy, adjusts the fan level according to humidity, and selects an energy action based on the electricity tariff.

The baseline serves as the reference for evaluating the fuzzy and GA-tuned fuzzy controllers.

Output file:

```text
results/step3/baseline_results.csv
```

## 8. Fuzzy-Logic Controller

The fuzzy controller is implemented in `src/fuzzy_controller.py`.

It uses fuzzy membership values for temperature, humidity, and occupancy. Rule firing strengths are combined to calculate a weighted cooling output.

The controller returns:

- `cooling_pct`
- `fan_level`
- `energy_action`

The function `fuzzy_controller(row, params=None)` allows other project scripts to supply scenario rows and, where applicable, tuned parameters.

An unoccupied room receives zero cooling and an off fan setting. Tariff-related actions are handled separately from the cooling inference.

Run the controller:

```bash
python3 src/fuzzy_controller.py
```

Output file:

```text
results/step4/fuzzy_results.csv
```

## 9. Genetic-Algorithm Tuning

The optimizer is implemented in `src/ga_tune_fuzzy.py`.

It tunes six fuzzy-controller parameters:

- Three temperature membership thresholds.
- Three cooling-output parameters.

The genetic algorithm uses a fixed random seed, a population of 24 candidates, and 20 generations. Its operations include tournament selection, crossover, mutation, and elitism.

### Fitness objective

The optimizer uses a synthetic cooling-demand heuristic as its reference target. The fitness objective combines the root mean squared error between the controller output and the synthetic target with a penalty for cooling output in high-tariff scenarios.

The objective represents a simulation design assumption rather than a validated thermal-comfort model or a measurement of electricity consumption.

Run the optimizer:

```bash
python3 src/ga_tune_fuzzy.py
```

Generated outputs:

| File | Purpose |
|---|---|
| `results/step6/ga_best_params.json` | Best parameters, configuration, seed, and fitness definition |
| `results/step6/ga_fitness_history.csv` | Fitness statistics for each generation |
| `results/step6/ga_fuzzy_results.csv` | GA-tuned controller outputs |

## 10. Three-Controller Comparison

The comparison script is `src/compare_controllers.py`.

It evaluates the baseline, fuzzy, and GA-tuned fuzzy controllers on the same 10,000 synthetic scenarios, allowing their recommendations to be compared under consistent input conditions.

Run the comparison after generating the GA-tuned controller results:

```bash
python3 src/compare_controllers.py
```

Output file:

```text
results/step7/three_controller_comparison.csv
```

The file contains each scenario's inputs and the three controllers' cooling outputs, fan levels, and energy actions.

## 11. Controller Evaluation

The evaluation script is `src/evaluate_controllers.py`.

Run it after generating the three-controller comparison:

```bash
python3 src/evaluate_controllers.py
```

The evaluation summary is saved to:

```text
results/step7/evaluation_summary.csv
```

The evaluation reports:

- Number of scenarios compared.
- Average, minimum, and maximum cooling outputs.
- Fan-level distributions.
- High-tariff `avoid_peak` actions.
- Cooling-output, fan-level, and energy-action differences between controller pairs.

The reported values describe simulated controller behavior, not measured real-world energy consumption or indoor comfort.

## 12. Scenario Coverage and Invalid Inputs

Test scenarios are stored in `data/test/`. The test fixtures cover normal, boundary, stress, and invalid inputs.

Run the scenario-coverage script:

```bash
python3 src/run_scenario_coverage.py
```

Validate a sample input file:

```bash
python3 src/validate_data.py data/sample_input.csv
```

Invalid data should be rejected rather than silently accepted as a valid scenario.

## 13. Visualizations

Comparison visualizations are generated by `src/generate_visuals.py`.

Run:

```bash
python3 src/generate_visuals.py
```

Output files:

```text
results/figures/cooling_comparison.png
results/figures/fan_level_comparison.png
```

The current figures illustrate comparisons across five scenarios. They should be interpreted as examples rather than visualizations of the entire 10,000-scenario evaluation.

## 14. Streamlit Dashboard

The interactive application is located at `app/app.py`.

Start it from the repository root:

```bash
streamlit run app/app.py
```

The dashboard accepts temperature, humidity, occupancy, and tariff inputs and displays controller recommendations.

**Live application:** [Open the SC01 Dashboard](https://sc01-intelligent-campus-climate-and-energy-controller-bguednbl.streamlit.app/)

Deployment details:

- Hosting: Streamlit Community Cloud
- Deployment branch: `step-6-evaluation`
- Entry point: `app/app.py`
- Dependencies: `requirements.txt`

The public application was browser-tested on 12 October 2026.

## 15. Environment Setup

Use a supported Python 3 environment. Run the following commands from the repository root.

Create and activate a virtual environment on macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## 16. Recommended Execution Order

Run the following commands from the repository root to execute the main workflow:

```bash
python3 src/generate_scenarios.py
python3 src/prepare_data.py
python3 src/validate_data.py data/processed/cleaned_input.csv
python3 src/fuzzy_controller.py
python3 src/ga_tune_fuzzy.py
python3 src/compare_controllers.py
python3 src/evaluate_controllers.py
python3 src/generate_visuals.py
```

Start the dashboard separately:

```bash
streamlit run app/app.py
```

The comparison and evaluation scripts depend on outputs generated by earlier stages.

## 17. Repository Structure

```text
SC01-Intelligent-Campus-Climate-and-Energy-Controller/
├── app/
│   └── app.py
├── data/
│   ├── raw/
│   ├── processed/
│   ├── test/
│   ├── reports/
│   └── sample_input.csv
├── docs/
├── notebooks/
│   └── 01_data_inspection.ipynb
├── report/
│   └── final_report.md
├── results/
│   ├── figures/
│   ├── step3/
│   ├── step4/
│   ├── step5/
│   ├── step6/
│   └── step7/
├── src/
│   ├── baseline_controller.py
│   ├── compare_controllers.py
│   ├── evaluate_controllers.py
│   ├── fuzzy_controller.py
│   ├── ga_tune_fuzzy.py
│   ├── generate_scenarios.py
│   ├── generate_visuals.py
│   ├── prepare_data.py
│   ├── run_scenario_coverage.py
│   └── validate_data.py
├── requirements.txt
└── README.md
```

## 18. Current Implementation Status

The repository includes:

- Synthetic scenario generation and data preparation.
- Input-data validation and data-quality reporting.
- A deterministic baseline controller.
- A fuzzy-inference controller.
- Genetic-algorithm parameter tuning.
- Three-controller comparison and evaluation.
- Scenario-coverage tools and visualizations.
- A Streamlit dashboard.
- A final report and presentation.

## 19. Final Submission Checklist

- [x] Data pipeline and input validation implemented and checked.
- [x] Baseline and fuzzy-controller workflows implemented.
- [x] Genetic-algorithm tuning and saved parameters reviewed.
- [x] Three-controller comparison and evaluation artifacts generated and reviewed.
- [x] Input-boundary and validation checks performed; relevant automated tests passed.
- [x] Product V1 sketch and Product V2 dashboard artifacts included.
- [x] Product V2 deployed publicly and browser-tested.
- [x] Final report, presentation, and dashboard evidence committed and pushed.

## 20. Limitations and Project Summary

The project demonstrates a reproducible simulation workflow for comparing rule-based, fuzzy-inference, and genetic-algorithm-tuned fuzzy controllers.

The scenario data is synthetic, and the GA optimizer uses a heuristic cooling-demand objective. Fitness scores are not measurements of actual electricity consumption. A lower cooling recommendation does not automatically indicate lower energy use or acceptable indoor comfort.

The controllers have not been validated for direct control of real HVAC equipment. Real-world use would require validation with building data, a defensible comfort model, and measured energy outcomes.