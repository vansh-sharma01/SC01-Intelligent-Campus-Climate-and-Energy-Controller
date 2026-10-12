# SC01 Step 3 — Baseline Controller

## 1. Objective

Step 3 establishes a deterministic, rule-based baseline for the
Intelligent Campus Climate and Energy Controller. This baseline serves
as a reference for comparing the fuzzy and GA-tuned fuzzy controllers.

## 2. Inputs and Outputs

Inputs:
- `scenario_id`: unique scenario identifier
- `temperature_c`: room temperature in degrees Celsius
- `humidity_pct`: relative humidity percentage
- `occupancy_count`: number of people in the room
- `tariff_level`: `low`, `medium`, or `high`

Outputs:
- `cooling_pct`: recommended cooling level from 0 to 100
- `fan_level`: `off`, `low`, `medium`, or `high`
- `energy_action`: `normal` or `avoid_peak` under the baseline rules

## 3. Baseline Method

The implementation is in `src/baseline_controller.py`.

1. If occupancy is zero, set cooling to 0% and the fan to `off`.
2. Otherwise, if temperature is below 24°C, set cooling to 10%.
3. For temperatures from 24°C through 30°C, set cooling to 50%.
4. Above 30°C, set cooling to 90%.
5. If relative humidity is above 75%, increase the fan level by one
   band, subject to the controller's defined limits.
6. If the tariff is `high`, set the energy action to `avoid_peak`;
   otherwise, set it to `normal`.

## 4. Results and Evidence

The five required baseline scenarios and their recorded outputs are
stored in `results/step3/baseline_results.csv`.

All five recorded scenarios have status `PASS`. They cover a normal
room, hot and humid conditions, zero occupancy, a high-temperature
boundary, and a cool but humid room.

The CSV is recorded evidence for these five baseline cases. It does
not, by itself, demonstrate real-world building performance.

## 5. Limitations

The controller uses fixed thresholds and simplified rules. These
thresholds are project assumptions, not validated HVAC control
standards. The scenarios are synthetic rather than measurements from
a real campus building.

The controller has not been validated against measured electricity
consumption or a validated thermal-comfort model. Its recommendations
must not be interpreted as proof of energy savings, comfort, or
suitability for direct control of real HVAC equipment.

## 6. Reproducibility

From the repository root, run the baseline controller and regenerate
the five-case results CSV:

```bash
python3 src/baseline_controller.py
```

The script prints each test result and saves the output to
`results/step3/baseline_results.csv`.

Related documentation:
- `docs/STEP-1.md`
- `data/README.md`

The later fuzzy and GA-tuned fuzzy controllers are documented and
evaluated separately in the repository.

## 7. Completion Evidence

- [x] Baseline implementation is present.
- [x] Five baseline scenarios are recorded.
- [x] Results CSV contains a status for each scenario.
- [x] Method and limitations are documented here.
