# SC01 — Intelligent Campus Climate and Energy Controller
## Final Technical Report

**Project type:** Soft Computing Capstone
**Team:** Vansh Sharma, Manshi Tiwari, Lakshya Sharma, Akash Dubey

## 1. Abstract

This project develops an interactive controller that recommends room cooling intensity, fan level, and an energy-management action using temperature, relative humidity, occupancy, and electricity tariff. It compares three approaches: a deterministic rule-based baseline, a fuzzy controller, and a Genetic Algorithm (GA)-tuned fuzzy controller.

The project includes synthetic-data generation, input validation, controller evaluation, visualizations, and a Streamlit dashboard. The three-controller evaluation uses 10,000 common synthetic scenarios.

The system is a software simulation. Its results demonstrate controller behaviour under defined assumptions; they do not establish real-world energy savings, thermal comfort, or HVAC performance.

## 2. Problem Statement and Objectives

Campus facility managers need understandable recommendations for managing room climate while considering occupancy and electricity tariffs.

The project objectives are to:

- Define and validate consistent input and output variables.
- Generate reproducible climate and occupancy scenarios.
- Implement a deterministic baseline controller.
- Implement a fuzzy controller and tune its parameters using a GA.
- Compare all three controllers using the same scenarios.
- Provide an interactive interface and reproducible evaluation results.

## 3. System Inputs and Outputs

### 3.1 Inputs

| Field | Meaning | Valid domain |
|---|---|---|
| `scenario_id` | Unique scenario identifier | Non-empty and unique |
| `temperature_c` | Room temperature | 18–45 °C |
| `humidity_pct` | Relative humidity | 0–100% |
| `occupancy_count` | Number of occupants | Non-negative integer |
| `tariff_level` | Electricity tariff category | `low`, `medium`, `high` |

### 3.2 Outputs

| Field | Meaning | Values |
|---|---|---|
| `cooling_pct` | Recommended cooling intensity | 0–100% |
| `fan_level` | Recommended fan level | `off`, `low`, `medium`, `high` |
| `energy_action` | Energy-management recommendation | `normal`, `save`, `avoid_peak` |

These outputs are recommendations rather than measurements of actual electricity consumption.

## 4. Dataset and Preparation

The project uses 10,000 synthetically generated scenarios. The data generator uses random seed 42, supporting reproducibility when the code and dependency versions remain unchanged.

The principal data files and scripts are:

- Raw data: `data/raw/generated_scenarios.csv`
- Processed data: `data/processed/cleaned_input.csv`
- Generator: `src/generate_scenarios.py`
- Preparation pipeline: `src/prepare_data.py`
- Validator: `src/validate_data.py`
- Inspection notebook: `notebooks/01_data_inspection.ipynb`
- Quality report: `data/reports/data_quality_report.md`

The recorded data-quality checks report:

- 10,000 rows and five columns.
- Zero missing values.
- Zero duplicate scenario identifiers.
- Zero duplicate complete rows.
- Temperature range: 18.00–44.99 °C.
- Humidity range: 20.01–99.99%.
- Occupancy range: 0–100 people.
- Tariff distribution: 3,519 low, 3,506 medium, and 2,975 high.

The dataset is synthetic and is not collected from a real campus or operational HVAC system.

## 5. Controller Methods

### 5.1 Rule-Based Baseline Controller

The baseline controller uses fixed decision rules. When occupancy is zero, it recommends zero cooling and turns the fan off. For occupied rooms, cooling intensity is determined by temperature thresholds. High humidity can increase the fan level, and a high electricity tariff triggers the `avoid_peak` action.

This deterministic controller serves as the reference for comparing the other approaches.

### 5.2 Fuzzy Controller

The fuzzy controller provides cooling and fan recommendations based on the scenario inputs. Its implementation is located in `src/fuzzy_controller.py`.

The controller's recommendations are evaluated against the baseline using common input scenarios. The implementation and its configured rules determine the actual behaviour of the controller.

### 5.3 Genetic Algorithm-Tuned Fuzzy Controller

The GA-tuned fuzzy controller uses an evolutionary optimization process to search for controller parameters. The current configuration uses a population of 24, 20 generations, and 400 training samples.

The fitness objective uses error against a synthetic cooling-demand heuristic, with a penalty associated with cooling under high-tariff conditions.

The optimizer and its saved outputs are:

- Optimizer: `src/ga_tune_fuzzy.py`
- Best parameters: `results/step6/ga_best_params.json`
- Fitness history: `results/step6/ga_fitness_history.csv`
- Controller results: `results/step6/ga_fuzzy_results.csv`

The fitness score is a simulated objective, not a direct measurement of electricity consumption, comfort, or safety.

## 6. Experimental Results

The three-controller evaluation covers **10,000 common synthetic scenarios**. All three controllers were evaluated using the same scenario dataset.

### 6.1 Cooling Recommendations

| Metric | Baseline | Fuzzy | GA-tuned fuzzy |
|---|---:|---:|---:|
| Average cooling output | 62.23% | 70.72% | 47.60% |
| Minimum cooling output | 0% | 0% | 0% |
| Maximum cooling output | 90% | 90% | 72.09% |

The GA-tuned fuzzy controller produced the lowest average cooling recommendation in this evaluation. This result reflects the simulated objective and controller configuration, not verified reductions in actual energy consumption.

### 6.2 Comparison Between Controllers

| Comparison | Cooling outputs differ | Fan levels differ | Energy actions differ |
|---|---:|---:|---:|
| Baseline vs. fuzzy | 6,951 | 5,361 | 0 |
| Baseline vs. GA-tuned fuzzy | 9,907 | 4,080 | 0 |
| Fuzzy vs. GA-tuned fuzzy | 9,907 | 2,100 | 0 |

The `avoid_peak` action occurred in 2,975 scenarios for each controller. Energy-action outputs were identical across the three controllers, while cooling and fan recommendations differed in many scenarios.

These results show that the controller methods produce different recommendations for the same simulated conditions. They do not establish which controller would perform best in a real building.

### 6.3 Evaluation Evidence

The primary evaluation files are:

- `results/step7/three_controller_comparison.csv`
- `results/step7/evaluation_summary.csv`

The three-controller comparison file contains 10,000 scenario rows, excluding the header.

The figures in `results/figures/` provide visual comparisons of cooling recommendations and fan levels. The existing figures cover five scenarios and should be presented as illustrative examples rather than visualizations of all 10,000 scenarios.

## 7. Software Interface

The interactive dashboard is implemented using Streamlit in `app/app.py`. It accepts temperature, humidity, occupancy, and tariff inputs and presents controller recommendations.

The dashboard includes:

- Interactive scenario inputs.
- Controller recommendations.
- A comparison of baseline, fuzzy, and GA-tuned fuzzy outputs.
- Explanations of recommendations.
- A cooling-output chart.

To launch the application locally from the repository root, run:

```bash
streamlit run app/app.py
```

The application was previously reported as deployed and browser-tested on 12 October 2026. Deployment availability should be checked before presenting the project.

- **Live application:** https://sc01-intelligent-campus-climate-and-energy-controller-bguednbl.streamlit.app/
- **Deployment branch:** `step-6-evaluation`
- **Entry point:** `app/app.py`
- **Dependencies:** `requirements.txt`

## 8. Validation and Reproducibility

The project includes the following validation and evaluation evidence:

- Valid and intentionally invalid input fixtures.
- Input validation for missing, invalid, and out-of-range values.
- Scenario coverage examples, including boundary and stress cases.
- A synthetic-data generation and preparation pipeline.
- A data-inspection notebook with saved outputs.
- Controller comparison and evaluation CSV files.
- Saved GA parameters and fitness history.
- Automated controller requirement tests.

The test suite `src/test_step4_requirements.py` contains 11 tests. The latest recorded execution completed successfully:

```text
Ran 11 tests
OK
```

The project also includes a three-controller evaluation over 10,000 scenarios. Re-run relevant checks if the source code, configuration, or dependencies change after these results were generated.

## 9. Limitations and Future Work

The project has several limitations:

1. The input scenarios and cooling-demand target are synthetic.
2. No measured electricity consumption or live HVAC sensor data is used.
3. The GA optimizes a heuristic objective rather than a validated physical energy model.
4. Lower cooling recommendations alone do not prove energy savings or acceptable thermal comfort.
5. Evaluation results depend on the implemented controller logic, generated scenarios, and selected objective.
6. Real-world deployment would require validation against building data, safety constraints, and suitable comfort and energy metrics.

Future work could include collecting measured building data, validating the controller against established comfort standards, developing a physical energy-consumption model, expanding stress testing, and conducting systematic user evaluation.

## 10. Conclusion

The Intelligent Campus Climate and Energy Controller combines synthetic-data preparation, input validation, a rule-based baseline, fuzzy-controller recommendations, GA-based parameter tuning, comparative evaluation, and a Streamlit dashboard.

The evaluation of 10,000 common scenarios shows that the three approaches can produce different cooling and fan recommendations. The GA-tuned fuzzy controller produced the lowest average cooling recommendation in the recorded simulation, while all three controllers produced identical energy-action outputs.

These findings demonstrate differences in simulated controller behaviour. Further validation using measured building data is necessary before drawing conclusions about actual energy efficiency, operating costs, or thermal comfort.

## 11. Repository Evidence

- Project requirements: `docs/STEP-1.md`
- Baseline pseudocode: `docs/baseline-pseudocode.md`
- Product V1 sketch: `docs/product-v1-sketch.png`
- Data documentation: `data/README.md`
- Data-quality report: `data/reports/data_quality_report.md`
- Data-inspection notebook: `notebooks/01_data_inspection.ipynb`
- Baseline results: `results/step3/baseline_results.csv`
- Fuzzy-controller results: `results/step4/fuzzy_results.csv`
- Scenario coverage: `results/step4/scenario_coverage_results.csv`
- Controller comparison: `results/step5/controller_comparison.csv`
- GA outputs: `results/step6/`
- Three-controller evaluation: `results/step7/`
- Visualizations: `results/figures/`
- Interactive application: `app/app.py`
- Automated tests: `src/test_step4_requirements.py`
