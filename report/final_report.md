# SC01 — Intelligent Campus Climate and Energy Controller
## Final Technical Report

**Project type:** Soft Computing capstone  
**Team:** Vansh Sharma, Manshi Tiwari, Lakshya Sharma, Akash Dubey

## 1. Abstract

This project develops an interactive controller that recommends room cooling intensity, fan level, and an energy-management action from temperature, relative humidity, occupancy, and electricity tariff. It compares a deterministic rule-based baseline, a fuzzy-inference controller, and a Genetic Algorithm (GA)-tuned fuzzy controller. A reproducible synthetic dataset, validation pipeline, controller evaluation scripts, visualizations, and a Streamlit interface support the experiments.

The project is a software simulation using synthetic scenarios. Its results demonstrate controller behavior under the defined assumptions; they do not establish real-world energy savings, thermal comfort, or HVAC performance.

## 2. Problem Statement and Objectives

Campus facility managers need understandable recommendations for room climate management that consider occupancy and electricity tariff.

The objectives are to:
- Define and validate a consistent set of input and output variables.
- Generate repeatable climate and occupancy scenarios.
- Implement a deterministic baseline controller.
- Implement a fuzzy controller and tune its parameters using a GA.
- Compare all three controllers on common scenarios.
- Provide an interactive interface and reproducible results.

## 3. System Inputs and Outputs

### Inputs

| Field | Meaning | Valid domain |
|---|---|---|
| `scenario_id` | Unique scenario identifier | Non-empty and unique |
| `temperature_c` | Room temperature | 18–45 °C |
| `humidity_pct` | Relative humidity | 0–100% |
| `occupancy_count` | Number of occupants | Non-negative count |
| `tariff_level` | Electricity tariff category | `low`, `medium`, `high` |

### Outputs

| Field | Meaning | Values |
|---|---|---|
| `cooling_pct` | Recommended cooling intensity | 0–100% |
| `fan_level` | Recommended fan level | `off`, `low`, `medium`, `high` |
| `energy_action` | Energy-management recommendation | `normal`, `save`, `avoid_peak` |

The outputs are recommendations, not measured electricity consumption.

## 4. Dataset and Preparation

The project uses 10,000 synthetically generated scenarios. The generator uses random seed 42. The raw dataset is retained separately from the processed dataset.

- Raw data: `data/raw/generated_scenarios.csv`
- Processed data: `data/processed/cleaned_input.csv`
- Generator: `src/generate_scenarios.py`
- Preparation pipeline: `src/prepare_data.py`
- Validator: `src/validate_data.py`
- Notebook: `notebooks/01_data_inspection.ipynb`
- Quality report: `data/reports/data_quality_report.md`

The recorded dataset checks report:
- 10,000 rows and five columns.
- Zero missing values.
- Zero duplicate scenario identifiers.
- Zero duplicate complete rows.
- Temperature range: 18.00–44.99 °C.
- Humidity range: 20.01–99.99%.
- Occupancy range: 0–100 people.
- Tariff counts: 3,519 low, 3,506 medium, and 2,975 high.

The generated data is not collected from a real campus. Its fixed seed supports repeatability when the generation code and dependencies remain unchanged.

## 5. Controller Methods

### 5.1 Rule-based baseline

The baseline uses fixed thresholds. An empty room receives zero cooling and an off fan. For occupied rooms, cooling is set according to temperature bands. High humidity can increase fan level, and a high tariff triggers the `avoid_peak` action.

This deterministic controller serves as the reference for the other methods.

### 5.2 Fuzzy controller

The fuzzy controller uses fuzzy inference to map room conditions to a cooling recommendation. Fuzzy membership functions and rules allow gradual transitions rather than relying exclusively on rigid temperature thresholds.

The implementation is in `src/fuzzy_controller.py`.

### 5.3 GA-tuned fuzzy controller

The Genetic Algorithm searches for improved fuzzy-controller parameters using a seeded evolutionary process. The current implementation uses a population of 24, 20 generations, and 400 training samples. Its fitness objective is based on error against a synthetic cooling-demand heuristic, with a small penalty for cooling under high-tariff conditions.

The optimizer and saved outputs are:
- `src/ga_tune_fuzzy.py`
- `results/step6/ga_best_params.json`
- `results/step6/ga_fitness_history.csv`
- `results/step6/ga_fuzzy_results.csv`

The objective is a simulated proxy. A lower fitness score does not by itself prove better comfort, safety, or real energy efficiency.

## 6. Experimental Results

The recorded three-controller comparison covers 20 scenarios.

| Metric | Baseline | Fuzzy | GA-tuned fuzzy |
|---|---:|---:|---:|
| Mean cooling recommendation | 46.50% | 49.15% | 35.46% |
| `normal` energy actions | 12 | 12 | 12 |
| `avoid_peak` energy actions | 8 | 8 | 8 |

Cooling recommendations differed between:
- Baseline and fuzzy: 12 of 20 scenarios.
- Baseline and GA-tuned fuzzy: 17 of 20 scenarios.
- Fuzzy and GA-tuned fuzzy: 17 of 20 scenarios.

Fan recommendations differed between:
- Baseline and fuzzy: 6 of 20 scenarios.
- Baseline and GA-tuned fuzzy: 4 of 20 scenarios.
- Fuzzy and GA-tuned fuzzy: 4 of 20 scenarios.

The energy-action outputs were identical across the three controllers for these 20 scenarios.

Primary result files:
- `results/step7/three_controller_comparison.csv`
- `results/step7/evaluation_summary.csv`

The recorded visualization script produces cooling and fan comparison figures in `results/figures/`. The current figures cover five scenarios, while the three-controller evaluation covers 20; the figure scope should be stated when presenting them.

## 7. Software Interface

The interactive interface is implemented in `app/app.py` using Streamlit. It accepts room temperature, humidity, occupancy, and tariff inputs and presents controller recommendations.

To run the interface locally from the repository root:

```bash
streamlit run app/app.py
```

A successful local run does not establish that the application has been publicly deployed. Deployment status and any public URL must be verified separately.

## 8. Validation and Reproducibility

The project includes:
- Valid and intentionally invalid input fixtures.
- Scenario coverage examples.
- A reusable input validator.
- A generated and processed dataset.
- An executed data-inspection notebook with saved outputs.
- Controller comparison and evaluation CSV files.
- A fixed random seed in the data generator and GA workflow.

Previously recorded integrated checks passed for validation, fuzzy inference, GA tuning, three-controller comparison, evaluation, visualization generation, and `git diff --check`.

Re-run the relevant commands before final submission if any source code, configuration, or dependency versions change.

## 9. Limitations and Future Work

1. The climate scenarios and cooling-demand target are synthetic.
2. No measured energy-consumption or live HVAC sensor data is used.
3. The GA optimizes a heuristic objective, not a validated physical energy model.
4. Lower recommended cooling is not sufficient evidence of energy savings or acceptable thermal comfort.
5. The comparison covers a finite set of scenarios; broader boundary and stress-case evaluation remains useful.
6. Public deployment, deployment URL, demonstration recording, and final viva materials must be verified or completed separately if required by the submission rubric.

Future work should evaluate the controller against measured building data, define validated comfort and energy metrics, broaden stress testing, and document deployment and user testing.

## 10. Conclusion

The project brings together reproducible synthetic-data preparation, input validation, a deterministic baseline, fuzzy inference, GA-based parameter tuning, comparative evaluation, and a Streamlit interface. The recorded experiments show that controller recommendations can differ meaningfully across the methods. These findings are evidence of behavior within the simulation, not proof of real-world energy savings or comfort improvement.

## 11. Repository Evidence

- Project contract: `docs/STEP-1.md`
- Baseline pseudocode: `docs/baseline-pseudocode.md`
- Product V1 sketch: `docs/product-v1-sketch.png`
- Data documentation: `data/README.md`
- Data quality report: `data/reports/data_quality_report.md`
- Notebook: `notebooks/01_data_inspection.ipynb`
- Controller evaluation: `results/step7/`
- Visualizations: `results/figures/`
- Interactive interface: `app/app.py`
