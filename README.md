# Intelligent Campus Climate and Energy Controller

## 1. Project Overview

The Intelligent Campus Climate and Energy Controller is a Soft Computing project that simulates climate-control decisions for campus rooms using temperature, humidity, occupancy, and electricity-tariff information.

The project implements and compares three approaches:

1. **Rule-based baseline controller** — uses fixed thresholds and deterministic rules.
2. **Fuzzy-logic controller** — uses fuzzy membership functions and weighted fuzzy-rule inference to determine cooling output.
3. **GA-tuned fuzzy controller** — uses a genetic algorithm to optimize fuzzy-controller parameters against a documented synthetic design objective.

The repository also contains synthetic data-generation and validation tools, controller comparison and evaluation scripts, visualizations, and a Streamlit dashboard.

**Data limitation:** The scenarios are synthetic. They are not real campus HVAC measurements. Cooling outputs and fitness scores are simulation results, not verified energy savings or measured comfort outcomes.

## 2. Project Objectives

- Generate reproducible climate and occupancy scenarios.
- Validate input data before controller execution.
- Implement a deterministic baseline controller.
- Implement fuzzy inference for cooling decisions.
- Tune fuzzy-controller parameters with a genetic algorithm.
- Compare the three controllers on consistent scenarios.
- Evaluate differences in cooling outputs, fan levels, and tariff actions.
- Provide visualizations and an interactive dashboard.
- Document limitations and preserve reproducible results.

## 3. Input Data Specification

Each scenario contains the following fields:

| Field | Description | Expected range or values |
|---|---|---|
| `scenario_id` | Unique scenario identifier | Non-empty and unique |
| `temperature_c` | Room temperature in Celsius | 18–45 |
| `humidity_pct` | Relative humidity percentage | 0–100 |
| `occupancy_count` | Number of occupants | Integer from 0–100 |
| `tariff_level` | Electricity tariff category | `low`, `medium`, `high` |

The temperature and humidity ranges define the simulation input domain. They do not imply that the generated scenarios are measurements from real rooms.

## 4. Dataset Generation and Preparation

The scenario generator is located at:

`src/generate_scenarios.py`

The data-preparation script is:

`src/prepare_data.py`

The input validator is:

`src/validate_data.py`

The project generates 10,000 reproducible synthetic scenarios using a fixed random seed. Raw and processed datasets are stored separately.

Expected data locations:

- `data/raw/generated_scenarios.csv`
- `data/processed/cleaned_input.csv`
- `data/sample_input.csv`
- `data/test/`
- `data/reports/data_quality_report.md`

The generated dataset is intended for development and simulation. The cleaning and validation workflow checks schema requirements, numeric fields, valid ranges, tariff categories, missing values, and duplicate identifiers.

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

## 5. Data Inspection Notebook

The notebook is located at:

`notebooks/01_data_inspection.ipynb`

It supports inspection of the processed dataset, including:

- Dataset shape and column types.
- Sample records.
- Missing-value checks.
- Duplicate-identifier checks.
- Descriptive statistics and value ranges.
- Tariff-category counts.
- Assertions for expected dataset properties.

Open the notebook in Jupyter and execute its cells to review the saved analysis and outputs.

## 6. Baseline Controller

The deterministic baseline implementation is located at:

`src/baseline_controller.py`

The baseline applies fixed rules to temperature and occupancy, adjusts the fan level according to humidity, and uses the tariff category to select an energy action.

The baseline is included as a reference against which the fuzzy and GA-tuned controllers can be compared.

The main baseline results are stored at:

`results/step3/baseline_results.csv`

## 7. Fuzzy-Logic Controller

The fuzzy controller is implemented in:

`src/fuzzy_controller.py`

It uses fuzzy membership values for temperature, humidity, and occupancy. Rule firing strengths are combined to calculate a weighted cooling output.

The controller returns:

- `cooling_pct`
- `fan_level`
- `energy_action`

The implementation retains the `fuzzy_controller(row, params=None)` interface so other project scripts can supply scenario rows and, where appropriate, tuned parameters.

An unoccupied room receives zero cooling and an `off` fan setting. Tariff-based actions are selected separately from the cooling inference.

Run the fuzzy controller:

```bash
python3 src/fuzzy_controller.py
```

The output is saved to:

`results/step4/fuzzy_results.csv`

## 8. Genetic-Algorithm Tuning

The genetic-algorithm optimizer is implemented in:

`src/ga_tune_fuzzy.py`

It tunes six parameters used by the fuzzy controller:

- Three temperature membership thresholds.
- Three cooling-output parameters.

The implementation uses a fixed random seed, a population of 24 candidates, and 20 generations. It includes tournament selection, crossover, mutation, and elitism.

### Fitness objective

The optimizer uses a synthetic cooling-demand heuristic as a reference target. Its fitness combines:

1. Root mean squared error between the controller output and the synthetic target.
2. A small penalty for cooling output in high-tariff scenarios.

This objective is a design assumption for simulation. It is not a validated thermal-comfort model and does not measure actual HVAC electricity consumption.

A lower fitness score indicates a better fit to this particular synthetic objective; it does not by itself demonstrate that a controller is safer, more comfortable, or more energy-efficient in a real building.

Run the optimizer:

```bash
python3 src/ga_tune_fuzzy.py
```

Generated outputs:

- `results/step6/ga_best_params.json` — best parameters, configuration, seed, and fitness definition.
- `results/step6/ga_fitness_history.csv` — fitness statistics for each generation.
- `results/step6/ga_fuzzy_results.csv` — GA-tuned controller outputs.

## 9. Three-Controller Comparison

The comparison script is:

`src/compare_controllers.py`

It evaluates the following approaches on the same sample scenarios:

- Rule-based baseline.
- Fuzzy-logic controller.
- GA-tuned fuzzy controller.

Run the comparison after running the GA optimizer:

```bash
python3 src/compare_controllers.py
```

The output is saved to:

`results/step7/three_controller_comparison.csv`

The comparison file includes each controller's cooling output, fan level, and energy action for each scenario.

## 10. Controller Evaluation

The evaluation script is:

`src/evaluate_controllers.py`

Run it after generating the three-controller comparison:

```bash
python3 src/evaluate_controllers.py
```

The summary is saved to:

`results/step7/evaluation_summary.csv`

The evaluation reports:

- Number of scenarios compared.
- Average, minimum, and maximum cooling outputs.
- Fan-level distributions.
- Number of high-tariff `avoid_peak` actions.
- Cooling-output differences between controller pairs.
- Fan-level differences between controller pairs.
- Energy-action differences between controller pairs.

These metrics describe simulated controller behavior. They do not establish actual energy savings or equivalent indoor comfort.

## 11. Scenario Coverage and Invalid Inputs

Test scenarios are stored under:

`data/test/`

The test fixtures include normal, boundary, stress, and invalid input examples. They are intended to exercise input validation and controller behavior across a range of conditions.

Run the scenario-coverage script if it is present in the repository:

```bash
python3 src/run_scenario_coverage.py
```

Validate an input file using:

```bash
python3 src/validate_data.py data/sample_input.csv
```

Invalid data should be rejected rather than silently accepted as a valid scenario. Review the generated test outputs and error messages when extending the input domain or changing validation rules.

## 12. Visualizations

Comparison visualizations are generated by:

`src/generate_visuals.py`

Run:

```bash
python3 src/generate_visuals.py
```

The current visualization outputs include:

- `results/figures/cooling_comparison.png`
- `results/figures/fan_level_comparison.png`

Regenerate the visualizations after updating the relevant controller results. Confirm that the charts represent the current data and accurately identify which controllers are being compared.

## 13. Streamlit Dashboard

The interactive application is located at:

`app/app.py`

Start the dashboard from the repository root:

```bash
streamlit run app/app.py
```

The dashboard provides interactive scenario inputs, including temperature, humidity, occupancy, and tariff level, and displays controller recommendations.

### Public Deployment

The application is deployed on Streamlit Community Cloud and has been opened and tested through its public URL.

- **Live app:** https://sc01-intelligent-campus-climate-and-energy-controller-bguednbl.streamlit.app/
- **Deployment branch:** `step-6-evaluation`
- **Entry-point file:** `app/app.py`
- **Dependencies:** Installed from the repository's `requirements.txt`.

The public app was verified in a browser on 12 October 2026. Recheck the live URL before the final presentation.

The dashboard is a simulation interface. It is not connected to physical HVAC equipment and does not directly control a real building.

## 14. Environment Setup

Use a supported Python 3 environment. Run the following commands from the repository root.

Create and activate a virtual environment on macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the declared dependencies:

```bash
python3 -m pip install -r requirements.txt
```

If a required package is missing, update `requirements.txt` to include the dependency actually used by the implementation, then reinstall and verify the environment.

## 15. Recommended Execution Order

Run the project workflow in this order:

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

The dashboard can be started separately:

```bash
streamlit run app/app.py
```

Run commands from the repository root. The comparison and evaluation scripts depend on the outputs produced by earlier stages.

## 16. Repository Structure

The principal project files are organized as follows:

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

The exact files present may vary as the project evolves. Generated outputs should be retained when required by the submission rubric and should be reproducible from their source scripts.

## 17. Current Implementation Status

Implemented in the repository:

- Project inputs and output schema.
- Synthetic scenario generation and data preparation.
- Input-data validation and data-quality reporting.
- Deterministic baseline controller.
- Fuzzy-inference controller.
- Genetic-algorithm parameter tuning.
- Three-controller comparison.
- Comparative evaluation metrics.
- Scenario-coverage artifacts.
- Visualization generation.
- Streamlit dashboard.

The implementation status above describes repository components. It does not mean every academic requirement has been verified or every submission deliverable has been completed.

## 18. Final Submission Checklist

The following items have been completed based on the repository artifacts and checks performed during development:

- [x] Data pipeline and input validation implemented and checked.
- [x] Baseline controller and fuzzy-controller workflow implemented.
- [x] Genetic-algorithm tuning, fitness-history repeatability, and saved best parameters reviewed.
- [x] Three-controller comparison and evaluation artifacts generated and reviewed.
- [x] Boundary and input-validation checks performed; relevant automated tests passed.
- [x] Product V1 sketch and Product V2 dashboard artifacts included in the repository.
- [x] Product V2 deployed publicly and browser-tested.
- [x] Final report, presentation, and dashboard evidence committed and pushed.

## 19. Limitations

- Scenario data is synthetic rather than collected from real buildings.
- The cooling-demand reference used for GA optimization is heuristic.
- Fitness scores are not measurements of real energy consumption.
- Lower cooling commands do not automatically mean lower energy use or acceptable comfort.
- The controller has not been established as suitable for direct control of real HVAC equipment.
- Further validation with real data, a defensible comfort model, and measured energy outcomes would be required for real-world performance claims.

## 20. Project Summary

This project demonstrates a reproducible simulation workflow for comparing rule-based, fuzzy-inference, and genetic-algorithm-tuned fuzzy controllers. It includes data preparation, validation, optimization, comparison, evaluation, and an interactive interface.

The results should be interpreted within the limits of the synthetic dataset and stated optimization objective. Final project completion depends on verification of the official roadmap, testing requirements, and submission evidence.
