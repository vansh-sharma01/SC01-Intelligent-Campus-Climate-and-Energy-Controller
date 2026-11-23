# Step 6 - Testing and Validation

> **How this document was produced.** The test plan and expected behaviour were written before testing. Results were added after execution. Linux scripted results and Mac manual results are identified separately. Nothing in this file is a measurement of real energy savings or real indoor comfort; all controller data is synthetic.
>
> **Result summary:** Linux sandbox scripted checks: 72/72 PASS (including retests after fixes to R05, R07 and R08). Team Mac checks: M01-M07 all PASS. No remaining test rows are marked FAIL or NOT RUN.

## 1. Project and environment

- Team name: **TEAM ALGORITHM**
- Project: **SC01 - Intelligent Campus Climate and Energy Controller**
- Repository: https://github.com/vansh-sharma01/SC01-Intelligent-Campus-Climate-and-Energy-Controller
- Test branch: `step-6-testing`, created from the pushed `step-5-product-v1`.
- Source commit (output of `git rev-parse --short HEAD` when the branch was created): `c06d85b`. `main`, `step-5-product-v1` and `step-6-evaluation` are not modified by this step.
- Application under test: `app/app.py` (Streamlit), which calls `src/product_inference.py`, which calls the existing controllers. No controller code, saved GA parameter, dataset or earlier result file is changed in this step.
- Report date: 23 November 2026

| Environment | Python | Streamlit | pandas | numpy | Used for |
|---|---|---|---|---|---|
| Linux sandbox (primary) | 3.11.18 | 1.50.0 | 2.3.3 | 2.0.2 | All scripted and automated tests (rows marked `S`) |
| Linux sandbox (secondary) | 3.13.18 | 1.50.0 | 2.3.3 | 2.0.2 | Repeat of the unit tests only (row A05) |
| Team Mac | 3.9.6 | 1.50.0 | 2.3.3 | 2.0.2 | Environment check, full unit suite, consistency/rule coverage, and manual browser checks M04-M07 |

A run of the 62 existing tests was made once, when the branch was created, only to confirm a clean starting point. It is repeated and recorded properly as row A01.

## 2. How the application is launched and how the tests are run

Run from the repository root.

```bash
# application
python -m streamlit run app/app.py                 # http://localhost:8501
python -m streamlit run app/app.py --server.port 8502   # second copy, used for the missing-resource tests
```

```bash
# automated tests (all test files)
python -m unittest discover -s src -p "test_*.py" -v

# new Step 6 fuzzy rule-coverage tests only
python -m unittest discover -s src -p "test_fuzzy_rule_coverage.py" -v

# reference result, comparison and consistency checks
python src/make_step6_reference.py
python src/compare_step6_predictions.py --reference results/step6_testing/reference_predictions.csv docs/evidence/step6/downloads/*.csv
python src/check_product_consistency.py
python src/run_step6_scenario_coverage.py
```

The scripted browser runs used Playwright 1.63.0 with Chrome 153 (Linux sandbox) on the real running application. Scripted browser checks (rows marked `S` in groups L, N, B, I, R) use Playwright and real Google Chrome against the real running application: `src/run_step6_browser_checks.py` and `src/run_step6_resource_tests.py`. Playwright is a testing tool only and is **not** a dependency of the application.

**Method notes**

- *Expected behaviour is written here first.* Where a value can be worked out by hand from the controller rules it is written below. Otherwise the expected value is the row for the same inputs in the reference file `results/step6_testing/reference_predictions.csv`, which is produced by calling the existing controllers directly (without the interface).
- *Comparison rule* (`src/compare_step6_predictions.py`): `controller`, the four inputs, `fan_level` and `energy_action` must match exactly. `cooling_pct` must match within **0.01 percentage points**. The tolerance exists because Python 3.12 and later add floats more accurately than 3.11 and earlier, so a value sitting exactly on a rounding boundary can differ by 0.01 between Python versions (seen once in 30,000 scenarios in Step 5). Any difference larger than 0.01 is a failure.
- *Status values:* `PASS`, `FAIL`, `NOT RUN`. A test that checks rejection of bad input is `PASS` when the application shows the clear error and does not produce a recommendation.
- *Missing-GA behaviour under test (decision recorded before testing):* if the saved GA parameter file is missing or invalid, **Baseline and Fuzzy remain usable**, the GA-optimised option shows a clear, actionable error, and "Compare all three" shows that error with no partial result. The application never silently substitutes the ordinary fuzzy controller for the GA controller.
- *Fuzzy rule coverage* is measured without changing the controller: the test reads the rule strengths that the real `fuzzy_cooling()` function computes internally (the local `rules` list) using Python's profiling hook. The 11 rules are numbered R01-R11 in the order they appear in `src/fuzzy_controller.py`.

## 3. Planned tests

`Run` column: `S` = scripted/automated in the Linux sandbox, `M` = run by hand on the team's Mac. Inputs are temperature (°C) / humidity (%) / occupancy (people) / tariff.

**Reference input cases used below** (named so the rows stay short):

| Case | Inputs | Purpose |
|---|---|---|
| NORMAL | 25 / 55 / 50 / medium | The interface defaults |
| HOT-HUMID | 38 / 85 / 80 / high | Hot, humid, crowded room on a high tariff |
| EMPTY | 30 / 50 / 0 / low | Empty room |
| COOL | 21 / 45 / 15 / low | Cool, lightly used room |

### 3.1 Launch

| ID | Run | Input or action | Expected behaviour | Actual result | Status |
|---|---|---|---|---|---|
| L01 | S | Start `python -m streamlit run app/app.py` and open the page in Chrome | Page loads; title "Intelligent Campus Climate..." shown; permanent "Simulation only" warning visible; four tabs (Recommendation, Evaluation results (synthetic), Campus energy benchmark, About & limitations); no traceback | Chrome 153 (Linux sandbox, Python 3.11.18 server): title shown; 'Simulation only' warning shown; four tabs present; no traceback. `L01-home.png` | PASS |

### 3.2 Normal use

| ID | Run | Input or action | Expected behaviour | Actual result | Status |
|---|---|---|---|---|---|
| N01 | S | NORMAL, controller = Baseline, Generate Recommendation | 50.00 % / Medium / Normal (rule: 24 < 25 <= 30 gives 50 % medium; humidity 55 is not above 75) | 50.00 / Medium / Normal (matches expected). `N01-normal-baseline.png` | PASS |
| N02 | S | NORMAL, controller = Fuzzy | 55.00 % / Medium / Normal (only rule R05 fires, strength 1/6, consequent 55) | 55.00 / Medium / Normal (matches expected). `N02-normal-fuzzy.png` | PASS |
| N03 | S | NORMAL, controller = GA-optimised Fuzzy | 31.41 % / Medium / Normal (temperature 25 is below the saved t1 = 27, so only R02 fires with consequent cool_medium = 31.409) | 31.41 / Medium / Normal (matches expected). `N03-normal-ga.png` | PASS |
| N04 | S | NORMAL, Compare all three controllers | One view with three results equal to N01-N03 | Baseline 50.00 / Medium / Normal; Fuzzy 55.00 / Medium / Normal; GA 31.41 / Medium / Normal. `N04-normal-compare.png` | PASS |
| N05 | S | After N04, press "Download this result as CSV" | File `sc01_product_v1_recommendation.csv` downloads; header = `controller,temperature_c,humidity_pct,occupancy_count,tariff_level,cooling_pct,fan_level,energy_action,notice`; 3 data rows (baseline, fuzzy, ga_fuzzy) equal to what is on screen; notice text present | Downloaded `sc01_product_v1_recommendation.csv`; header exactly as documented; controllers ['baseline', 'fuzzy', 'ga_fuzzy']; cooling in file ['50.00 %', '55.00 %', '31.41 %'] = on screen ['50.00 %', '55.00 %', '31.41 %']; notice present. Saved as `downloads/N05_NORMAL_compare.csv` | PASS |
| N06 | S | HOT-HUMID, Compare all three, download CSV | All three: energy action Avoid Peak. Baseline 90.00 % / High / Avoid Peak (temperature above 30 gives 90 % medium; humidity above 75 raises the fan one level). Fuzzy 90.00 % / High / Avoid Peak. GA-optimised: cooling between 31.41 and 72.09 (its consequent values), fan High (humidity at or above 80 raises the fan one level). Exact GA value = reference | Baseline 90.00 / High / Avoid Peak; Fuzzy 90.00 / High / Avoid Peak; GA 68.17 / High / Avoid Peak; CSV saved in `downloads/`. `N06-hot-humid-compare.png` | PASS |
| N07 | S | EMPTY, Compare all three, download CSV | All three: 0.00 % / Off / Normal | Baseline 0.00 / Off / Normal; Fuzzy 0.00 / Off / Normal; GA 0.00 / Off / Normal; CSV saved in `downloads/`. `N07-empty-room-compare.png` | PASS |
| N08 | S | COOL, Compare all three, download CSV | Baseline 10.00 % / Low / Normal; Fuzzy about 28.33 % / Low / Normal (hand calculation from R01 and R02); GA-optimised about 15.99 % / Low / Normal. Exact values = reference | Baseline 10.00 / Low / Normal; Fuzzy 28.33 / Low / Normal; GA 15.99 / Low / Normal; CSV saved in `downloads/`. `N08-cool-room-compare.png` | PASS |
| N09 | S | NORMAL with tariff Low, Medium, High (dropdown), Baseline | Energy action Normal, Normal, Avoid Peak; cooling and fan unchanged by tariff | Low: 50.00 / Medium / Normal; Medium: 50.00 / Medium / Normal; High: 50.00 / Medium / Avoid Peak | PASS |

### 3.3 Reference result and comparison script

| ID | Run | Input or action | Expected behaviour | Actual result | Status |
|---|---|---|---|---|---|
| C01 | S | `python src/make_step6_reference.py` | Writes `results/step6_testing/reference_predictions.csv` with one row per controller for every case in `data/test/step6_cases.csv`, using direct controller calls; does not touch the interface | 30 reference rows written (10 cases x 3 controllers) by direct controller calls. `results/step6_testing/reference_predictions.csv`, `terminal-C01-reference.txt`. All hand-worked values in this plan (N02, N03, N08, B01-B06, HOT-HUMID Fuzzy) agree with it; the GA value for HOT-HUMID is 68.17 (inside the expected 31.41-72.09). | PASS |
| C02 | S | `python src/compare_step6_predictions.py --reference ... docs/evidence/step6/downloads/*.csv` on all CSVs downloaded in N05-N08 and B01-B06 | Prints `PASS` and the number of rows compared; exit code 0 | `Files compared: 10; rows compared: 30` -> `PASS`, exit code 0 (run on the downloads of the final, after-fix browser run; the same result was obtained before the fix). `terminal-C02-comparison.txt` | PASS |
| C03 | S | Run the comparison script on a deliberately altered copy of one downloaded CSV (one fan level changed, one cooling value changed by 0.5, one by 0.005) | Fan-level and 0.5 differences are listed and the script exits with code 1; the 0.005 difference is accepted as within tolerance. (Proves the script can fail.) | Altered copy A (fan level changed): difference listed, exit 1. Copy B (cooling changed by 0.5): difference listed, exit 1. Copy C (cooling changed by 0.005): accepted, PASS, exit 0. `terminal-C03-negative-control.txt` | PASS |

### 3.4 Boundary values (each limit tested separately, other inputs = NORMAL, Compare all three, CSV downloaded)

| ID | Run | Input or action | Expected behaviour | Actual result | Status |
|---|---|---|---|---|---|
| B01 | S | Temperature = 18 | Accepted. Baseline 10.00 / Low / Normal; Fuzzy 55.00 / Medium / Normal; GA 31.41 / Medium / Normal | Baseline 10.00 / Low / Normal; Fuzzy 55.00 / Medium / Normal; GA 31.41 / Medium / Normal; CSV saved in `downloads/` | PASS |
| B02 | S | Temperature = 45 | Accepted. Baseline 90.00 / Medium / Normal; Fuzzy 90.00 / High / Normal; GA 72.09 / High / Normal | Baseline 90.00 / Medium / Normal; Fuzzy 90.00 / High / Normal; GA 72.09 / High / Normal; CSV saved in `downloads/`. `B02-boundary-temperature-45.png` | PASS |
| B03 | S | Humidity = 20 | Accepted. Baseline 50.00 / Medium / Normal; Fuzzy 55.00 / Medium / Normal; GA 31.41 / Medium / Normal | Baseline 50.00 / Medium / Normal; Fuzzy 55.00 / Medium / Normal; GA 31.41 / Medium / Normal; CSV saved in `downloads/` | PASS |
| B04 | S | Humidity = 100 | Accepted. Baseline 50.00 / High / Normal; Fuzzy 72.50 / High / Normal; GA 31.41 / High / Normal (humidity raises the fan one level) | Baseline 50.00 / High / Normal; Fuzzy 72.50 / High / Normal; GA 31.41 / High / Normal; CSV saved in `downloads/` | PASS |
| B05 | S | Occupancy = 0 | Accepted. All three 0.00 / Off / Normal | Baseline 0.00 / Off / Normal; Fuzzy 0.00 / Off / Normal; GA 0.00 / Off / Normal; CSV saved in `downloads/`. `B05-boundary-occupancy-0.png` | PASS |
| B06 | S | Occupancy = 100 | Accepted. Baseline 50.00 / Medium / Normal; Fuzzy 90.00 / High / Normal; GA 31.41 / Medium / Normal | Baseline 50.00 / Medium / Normal; Fuzzy 90.00 / High / Normal; GA 31.41 / Medium / Normal; CSV saved in `downloads/` | PASS |

### 3.5 Invalid input (one problem at a time unless stated, others = NORMAL, Baseline selected)

Every row: expected behaviour is a clear message naming the field and the valid range or what to enter, **no** recommendation or CSV button for that submit, no traceback, and the form stays usable.

| ID | Run | Input or action | Expected behaviour | Actual result | Status |
|---|---|---|---|---|---|
| I01 | S | Temperature = 46 (above limit) | Error: temperature outside 18-45 | "Temperature: 46 °C is outside the valid range 18-45 °C." No result, no CSV button, no traceback. `I01-invalid-temperature-46.png` | PASS |
| I02 | S | Temperature = 17 (below limit) | Error: temperature outside 18-45 | "Temperature: 17 °C is outside the valid range 18-45 °C." No result, no CSV button, no traceback. | PASS |
| I03 | S | Temperature = 45.01 (just above limit) | Error: temperature outside 18-45 | "Temperature: 45.01 °C is outside the valid range 18-45 °C." No result, no CSV button, no traceback. | PASS |
| I04 | S | Temperature = 17.99 (just below limit) | Error: temperature outside 18-45 | "Temperature: 17.99 °C is outside the valid range 18-45 °C." No result, no CSV button, no traceback. | PASS |
| I05 | S | Humidity = 101 | Error: humidity outside 20-100 | "Humidity: 101 % is outside the valid range 20-100 %." No result, no CSV button, no traceback. | PASS |
| I06 | S | Humidity = 19 | Error: humidity outside 20-100 | "Humidity: 19 % is outside the valid range 20-100 %." No result, no CSV button, no traceback. | PASS |
| I07 | S | Occupancy = -1 | Error: occupancy outside 0-100 | "Occupancy: -1 people is outside the valid range 0-100 people." No result, no CSV button, no traceback. | PASS |
| I08 | S | Occupancy = 101 | Error: occupancy outside 0-100 | "Occupancy: 101 people is outside the valid range 0-100 people." No result, no CSV button, no traceback. | PASS |
| I09 | S | Occupancy = 20.5 | Error: whole number of people required | "Occupancy: enter a whole number of people." No result, no CSV button, no traceback. | PASS |
| I10 | S | Temperature = `abc` (text) | Error: enter a number | "Temperature: enter a number." No result, no CSV button, no traceback. `I10-invalid-temperature-text.png` | PASS |
| I11 | S | Occupancy = `many` (text) | Error: enter a number | "Occupancy: enter a number." No result, no CSV button, no traceback. | PASS |
| I12 | S | Humidity left blank | Error: enter a value | "Humidity: enter a value (20-100 %)." No result, no CSV button, no traceback. `I12-invalid-humidity-blank.png` | PASS |
| I13 | S | Temperature left blank | Error: enter a value | "Temperature: enter a value (18-45 °C)." No result, no CSV button, no traceback. | PASS |
| I14 | S | Temperature = `nan` | Error: finite number required | "Temperature: use a finite number (not NaN or infinity)." No result, no CSV button, no traceback. | PASS |
| I15 | S | Occupancy = `inf` | Error: finite number required | "Occupancy: use a finite number (not NaN or infinity)." No result, no CSV button, no traceback. | PASS |
| I16 | S | Three problems at once: temperature `abc`, humidity 200, occupancy -5 | One message per field (three), all shown together; no recommendation | "Temperature: enter a number." / "Humidity: 200 % is outside the valid range 20-100 %." / "Occupancy: -5 people is outside the valid range 0-100 people." (three messages together; no result). `I16-invalid-three-fields.png` | PASS |
| I17 | S | Valid result on screen, then submit an invalid value (temperature 46) | The old result is removed; only the error is shown (no stale recommendation or CSV button) | Before: 50.00 / Medium / Normal with CSV button. After invalid submit: no metrics, no CSV button, only the error. `I17-stale-result-cleared.png` | PASS |
| I18 | S | After I17, correct the value and submit | Error disappears; a normal recommendation appears (recovery) | After correction:  50.00 / Medium / Normal; error gone. | PASS |
| I19 | S | Invalid tariff (`extreme`, blank, `None`), missing field names, booleans (checked in the inference layer because the tariff is a dropdown and cannot be typed) | `InputValidationError` naming each bad field; no controller called | The 39 inference-layer tests, including `test_unknown_tariff`, `test_text_where_number_expected` (text and booleans), `test_missing_keys`, `test_blank_and_none_values`, `test_all_problems_reported_together`, `test_invalid_input_never_reaches_a_controller`: all OK. `terminal-F-witness-strengths-and-I19.txt` | PASS |

### 3.6 Missing resources (temporary copy of the project, port 8502; the real repository files are never touched)

| ID | Run | Input or action | Expected behaviour | Actual result | Status |
|---|---|---|---|---|---|
| R01 | S, M | Delete `results/step6/ga_best_params.json` in the temporary copy; choose GA-optimised Fuzzy; submit NORMAL | Clear error naming `results/step6/ga_best_params.json` and saying to restore it; no recommendation, no traceback and no absolute path shown | "A controller could not be loaded: Saved GA parameters not found: results/step6/ga_best_params.json. Restore results/step6/ga_best_params.json (do not re-run the GA here)." No result, no traceback, no absolute path. `R01-missing-ga-file.png` | PASS |
| R02 | S | Same missing file; choose Compare all three | Same clear error; no partial result (documented behaviour) | "A controller could not be loaded: Saved GA parameters not found: results/step6/ga_best_params.json. Restore results/step6/ga_best_params.json (do not re-run the GA here)." No result, no traceback, no absolute path. `R02-missing-ga-compare.png` | PASS |
| R03 | S | Same missing file; Baseline and Fuzzy | Both still produce recommendations equal to N01 and N02 | Baseline 50.00 / Medium / Normal; Fuzzy 55.00 / Medium / Normal. | PASS |
| R04 | S, M | **Restore** the file in the same temporary copy (no restart); GA-optimised Fuzzy, NORMAL | Recommendation returns: 31.41 % / Medium / Normal, equal to N03 | File copied back into the temporary copy without restarting the server: 31.41 / Medium / Normal; error gone. `R04-restored-ga-file.png` | PASS |
| R05 | S | Replace the file by invalid JSON (`{not json`); choose GA-optimised Fuzzy | Clear error saying the file cannot be read; no recommendation; no traceback | First run (before fix): FAIL - message was "A controller could not be loaded: Saved GA parameters in ga_best_params.json are unreadable or incomplete: JSONDecodeError('Expecting property name enclosed in double quotes: line 1 column 2 (char 1)')" (no instruction on what to do; raw exception text). After fix:  "A controller could not be loaded: Saved GA parameters in ga_best_params.json are unreadable or incomplete (JSONDecodeError). Restore results/step6/ga_best_params.json from the repository (do not re-run the GA here)." - PASS. See section 5 (D1). `R05-corrupt-ga-file.png`, `R05-corrupt-ga-file_BEFORE_FIX.png` | PASS (after fix) |
| R06 | S | Restore the valid file after R05 | GA-optimised works again (recovery) | 31.41 / Medium / Normal after restoring the valid file, no restart. | PASS |
| R07 | S | Remove `results/step7/three_controller_comparison.csv` in the temporary copy; open Evaluation results tab and Recommendation tab | Evaluation tab shows an error message; Recommendation tab still works | First run (before fix): FAIL - the error showed the full local path `/tmp/.../results/step7/...`. After fix:  "Saved evaluation files could not be read (FileNotFoundError). Check that the CSV files in results/step7/ are present and complete (see the README)."; Recommendation tab still gave 50.00 / Medium / Normal. See section 5 (D2). `R07-step7_missing.png`, `R07-step7_missing_BEFORE_FIX.png` | PASS (after fix) |
| R08 | S | Remove `data/external/galgotias/campus_energy_benchmark.csv` in the temporary copy; open Campus energy benchmark tab and Recommendation tab | Benchmark tab shows an error message; Recommendation tab still works | First run (before fix): FAIL - same absolute-path problem. After fix:  "Benchmark file could not be read (FileNotFoundError). Check that data/external/galgotias/campus_energy_benchmark.csv is present and complete (see the README)."; Recommendation tab still gave 50.00 / Medium / Normal. See section 5 (D2). `R08-benchmark_missing.png` | PASS (after fix) |

### 3.7 Automated tests and scripts

| ID | Run | Input or action | Expected behaviour | Actual result | Status |
|---|---|---|---|---|---|
| A01 | S | `python -m unittest discover -s src -p "test_*.py" -v` (Python 3.11) | All tests OK; command, number of tests and result recorded (62 existing + the new Step 6 tests) | Python 3.11.18: **Ran 95 tests ... OK** (62 existing + 28 rule-coverage + 5 regression tests added in Step 6). Before the Step 6 changes the same command gave 62 OK. `terminal-A01-unittest-python3.11.txt` | PASS |
| A02 | S | `python -m unittest discover -s src -p "test_fuzzy_rule_coverage.py" -v` | All new rule-coverage tests OK | **Ran 28 tests ... OK**; also shown to fail when the controller is deliberately broken (section 5, check F-M). `terminal-A02-rule-coverage-tests.txt` | PASS |
| A03 | S | `python src/check_product_consistency.py` | Interface layer matches direct controllers (45/45) and the saved 10,000-scenario Step 7 results (30,000 comparisons; fan/action exact, cooling within 0.01) | Part A 45/45 match; Part B 30,000 comparisons, 30,000 exact, 0 fan/action mismatches -> PASS (run in a temporary copy so the tracked Product V1 evidence files were not overwritten). `terminal-A03-consistency-check.txt` | PASS |
| A04 | S | `python src/run_step6_scenario_coverage.py` | Runs the 10 coverage scenarios with the current controller into a **new** file `results/step6_testing/scenario_coverage_current.csv`; reports how many of the 11 rules those 10 scenarios fire; lists which saved Step 4 rows differ from the current controller. The old Step 4 file is left untouched and is not used as current evidence | 10 rows, no missing outputs; the 9 occupied scenarios fire **5 of 11 rules** (R05, R06, R08, R09, R10); **5 of the 10 saved Step 4 rows differ** from the current controller. New files in `results/step6_testing/`; Step 4 file untouched. `terminal-A04-scenario-coverage.txt` | PASS |
| A05 | S | Repeat A01 on Python 3.13 | All tests OK on the second interpreter | Python 3.13.18: **Ran 95 tests ... OK**. `terminal-A05-unittest-python3.13.txt` | PASS |

### 3.8 Fuzzy controller rule coverage and limits (`src/test_fuzzy_rule_coverage.py`)

Default parameters t1/t2/t3 = 24/30/36. Memberships: temperature low = 1 up to 18, falling to 0 at t1; medium = triangle t1-t2-t3; high = 0 up to t2, rising to 1 at t3. Occupancy low = 1 at 0 falling to 0 at 20; medium = triangle 10-50-85; high = 0 up to 60 rising to 1 at 100. Humidity high = 0 up to 65 rising to 1 at 100. Rule strength = the minimum of its parts.

| ID | Run | Input or action | Expected behaviour | Actual result | Status |
|---|---|---|---|---|---|
| F01 | S | Witness for R01 (temp low AND occupancy low): 21 / 50 / 5 | R01 strength 0.5 | Measured strength of R01 = 0.5 (test OK). `terminal-F-witness-strengths-and-I19.txt` | PASS |
| F02 | S | Witness for R02 (temp low AND occupancy medium): 21 / 50 / 30 | R02 strength 0.5 | Measured strength of R02 = 0.5 (test OK). `terminal-F-witness-strengths-and-I19.txt` | PASS |
| F03 | S | Witness for R03 (temp low AND occupancy high): 21 / 50 / 80 | R03 strength 0.5 | Measured strength of R03 = 0.5 (test OK). `terminal-F-witness-strengths-and-I19.txt` | PASS |
| F04 | S | Witness for R04 (temp medium AND occupancy low): 27 / 50 / 5 | R04 strength 0.5 | Measured strength of R04 = 0.5 (test OK). `terminal-F-witness-strengths-and-I19.txt` | PASS |
| F05 | S | Witness for R05 (temp medium AND occupancy medium): 27 / 50 / 50 | R05 strength 0.5 | Measured strength of R05 = 0.5 (test OK). `terminal-F-witness-strengths-and-I19.txt` | PASS |
| F06 | S | Witness for R06 (temp medium AND occupancy high): 27 / 50 / 100 | R06 strength 0.5 | Measured strength of R06 = 0.5 (test OK). `terminal-F-witness-strengths-and-I19.txt` | PASS |
| F07 | S | Witness for R07 (temp high AND occupancy low): 33 / 50 / 5 | R07 strength 0.5 | Measured strength of R07 = 0.5 (test OK). `terminal-F-witness-strengths-and-I19.txt` | PASS |
| F08 | S | Witness for R08 (temp high AND occupancy medium): 33 / 50 / 50 | R08 strength 0.5 | Measured strength of R08 = 0.5 (test OK). `terminal-F-witness-strengths-and-I19.txt` | PASS |
| F09 | S | Witness for R09 (temp high AND occupancy high): 40 / 50 / 100 | R09 strength 1.0 | Measured strength of R09 = 1.0 (test OK). `terminal-F-witness-strengths-and-I19.txt` | PASS |
| F10 | S | Witness for R10 (temp medium AND humidity high): 30 / 82.5 / 5 | R10 strength 0.5 | Measured strength of R10 = 0.5 (test OK). `terminal-F-witness-strengths-and-I19.txt` | PASS |
| F11 | S | Witness for R11 (temp low AND humidity high AND occupancy high): 21 / 100 / 100 | R11 strength 0.5 | Measured strength of R11 = 0.5 (test OK). `terminal-F-witness-strengths-and-I19.txt` | PASS |
| F12 | S | Count rule firings across all 10,000 synthetic scenarios (occupied rooms) | No dead rule: each of R01-R11 fires (strength > 0) at least once; the counts are printed | All 11 rules fire in the 9,907 occupied scenarios; counts R01-R11: 427, 1656, 921, 800, 3283, 1816, 1017, 4008, 2173, 1949, 407 (R11 least). Test OK. `terminal-A02-rule-coverage-tests.txt` | PASS |
| F13 | S | Same check with the saved GA parameters, over a grid of the whole valid input range | No dead rule under the GA parameters either | All 11 rules fire under the saved GA parameters (8,700-point grid; least-used R11 = 360 points). Test OK. Same check with default parameters (extra test F13b) OK. | PASS |
| F14 | S | Zero-strength fallback: temperature exactly equal to t1 (24.0 with default parameters, 27.0 with the GA parameters), occupancy 50 | Total firing strength is 0; the controller returns its fallback `cool_low` (15.0 default, 8.276 GA) with fan Low; no error | Default: total strength 0 at 24.0/50/50, cooling 15.0, fan Low. GA: total 0 at 27.0/50/50, cooling 8.28 (= cool_low), fan Low. Points 0.01 either side of t1 fire normally. Tests OK. | PASS |
| F15 | S | Grid scan of the whole valid input range | The zero-strength case occurs only when temperature equals t1; the `else high` fallback branch is never reached for valid inputs (recorded as a known limit if confirmed) | 300 zero-strength grid points for each parameter set, all exactly at temperature == t1; the `else cool_high` branch was never reached. Test OK. Recorded as a known limit (section 6). | PASS |
| F16 | S | Membership limits at exact breakpoints (temperature 18, t1, t2, t3, 45; occupancy 0, 10, 20, 50, 60, 85, 100; humidity 65, 100) | Values are exactly 0 or 1 at shoulders and peaks; 0.5 at the midpoints; never below 0 or above 1 | Exact values at all tested breakpoints (0, 0.5, 1) and all rule strengths within [0, 1] on the grid. Tests OK. | PASS |
| F17 | S | Fan thresholds using parameters with all three consequents equal to X: X = 29.99, 30.0, 69.99, 70.0 (humidity 50) | Fan Low, Medium, Medium, High | Cooling 29.99/30.0/69.99/70.0 -> fan Low/Medium/Medium/High. Test OK. | PASS |
| F18 | S | Humidity bump at the same X values with humidity 79.99 and 80.0 | No bump at 79.99; at 80.0 Low becomes Medium, Medium becomes High, High stays High | No bump at 79.99; bump from 80.0 (Low->Medium, Medium->High, High stays High). Test OK. | PASS |
| F19 | S | Occupancy 0 with any temperature, humidity and tariff | Cooling 0.00, fan Off | 0.00 % / Off for every tested temperature, humidity and tariff, default and GA parameters. Test OK. | PASS |
| F20 | S | Grid scan of the whole valid input range, default and GA parameters | Cooling always within 0-100; fan always one of Off/Low/Medium/High (Off only for empty rooms) | 840 points per parameter set: cooling within 0-100, fan always valid, Off only when occupancy is 0. Test OK. | PASS |
| F21 | S | Invalid temperature parameters (t1 >= t2, t1 <= 18, t3 >= 45) and the saved GA parameters | Invalid ones raise `ValueError`; the saved GA parameters are accepted | Four invalid parameter sets raised ValueError; saved GA parameters accepted. Tests OK. | PASS |

### 3.9 Hand-run tests on the team's Mac

These checks were performed by the team leader on the Mac. Terminal logs and manual observations are stored under `docs/evidence/step6/mac/`.

| ID | Run | Input or action | Expected behaviour | Actual result | Status |
|---|---|---|---|---|---|
| M01 | M | Record environment, branch and package versions | Branch `step-6-testing`; versions recorded | Commit `c06d85b`; branch `step-6-testing`; Python 3.9.6; Streamlit 1.50.0; pandas 2.3.3; NumPy 2.0.2. `mac/M01-environment.txt` | PASS |
| M02 | M | `python -m unittest discover -s src -p "test_*.py" -v` | All tests OK; count recorded | 95 tests ran; all 95 passed. `mac/M02-unittest.txt` | PASS |
| M03 | M | Product consistency check and fuzzy rule-coverage tests | Consistency and coverage checks pass on the Mac environment | In a temporary repository copy, layer vs direct controllers: 45/45 match; layer vs saved Step 7 results: 30,000/30,000 exact. Rule-coverage test suite: 28/28 passed. `mac/M03-consistency.txt`, `mac/M03-rule-coverage.txt` | PASS |
| M04 | M | Launch app, NORMAL, Compare all three, download CSV and compare it with the reference | Same values as N04; comparison script prints PASS | Baseline 50.00% / Medium / Normal; Fuzzy 55.00% / Medium / Normal; GA-optimised Fuzzy 31.41% / Medium / Normal. Downloaded CSV: 3/3 rows matched reference. `mac/M04-csv-comparison.txt`, `mac/M04-M07-manual-browser-checks.txt` | PASS |
| M05 | M | Boundary by hand: temperature 45 | Same as B02 | Baseline 90.00% / Medium / Normal; Fuzzy 90.00% / High / Normal; GA-optimised Fuzzy 72.09% / High / Normal. `mac/M04-M07-manual-browser-checks.txt` | PASS |
| M06 | M | Invalid by hand: temperature `abc`, then humidity blank | Same as I10 and I12 | Temperature error: `Temperature: enter a number.` Blank humidity error: `Humidity: enter a value (20-100 %).` No stale recommendation was displayed. `mac/M04-M07-manual-browser-checks.txt` | PASS |
| M07 | M | Missing GA file on a temporary copy (port 8502), then restore it | Same as R01 and R04 | Missing-file error was actionable; Baseline remained usable. After restoring the GA parameter file in the temporary copy, GA recovered without restarting Streamlit. Temporary copy used; working repository resource was not removed. `mac/M04-M07-manual-browser-checks.txt` | PASS |

## 4. Evidence

Linux evidence below was produced by real scripted runs on the Linux sandbox (Python 3.11.18 unless stated). Mac evidence is separately identified in `docs/evidence/step6/mac/`; the M04-M07 file is a written record of manual observations, not screenshots.

**`docs/evidence/step6/`**

| Evidence | Files |
|---|---|
| Environment, commit and launch | `terminal-L01-environment-and-launch.txt` |
| Screenshots of the real running app (Chrome) | `L01-home.png`, `N01`-`N04`, `N06`-`N08`, `B02`, `B05`, `I01`, `I10`, `I12`, `I16`, `I17` (`*.png`); missing-resource screenshots `R01`, `R02`, `R04`, `R05`, `R07`, `R08` |
| Browser run log (every value typed and every output read) | `browser_checks_log.json`, `terminal-browser-checks.txt` |
| CSV files downloaded from the app | `downloads/N05_NORMAL_compare.csv`, `N06_HOT-HUMID_compare.csv`, `N07_EMPTY_compare.csv`, `N08_COOL_compare.csv`, `B01`-`B06_compare.csv` |
| Reference, comparison and negative control | `terminal-C01-reference.txt`, `terminal-C02-comparison.txt`, `terminal-C03-negative-control.txt` |
| Missing-resource run | `resource_tests_log.json`, `terminal-resource-tests.txt`, `resource_server_*.log` |
| Automated tests | `terminal-A01-unittest-python3.11.txt`, `terminal-A02-rule-coverage-tests.txt`, `terminal-A03-consistency-check.txt`, `terminal-A04-scenario-coverage.txt`, `terminal-A05-unittest-python3.13.txt`, `terminal-F-witness-strengths-and-I19.txt` |
| Team Mac checks | `mac/M01-environment.txt`, `mac/M02-unittest.txt`, `mac/M03-consistency.txt`, `mac/M03-rule-coverage.txt`, `mac/M04-csv-comparison.txt`, `mac/M04-M07-manual-browser-checks.txt` |
| Deliberate-fault check of the rule-coverage tests | `terminal-F-mutation-check.txt` |
| Failing runs kept for the record (before the fixes) | `*_BEFORE_FIX.*`, `terminal-fix-regression-tests.txt` |

**`results/step6_testing/`**: `reference_predictions.csv`, `scenario_coverage_current.csv`, `step4_saved_vs_current.csv`, `scenario_rule_coverage.csv`.

**New or changed code in this step:** new `src/test_fuzzy_rule_coverage.py`, `src/test_step6_resource_messages.py`, `src/make_step6_reference.py`, `src/compare_step6_predictions.py`, `src/run_step6_scenario_coverage.py`, `src/run_step6_browser_checks.py`, `src/run_step6_resource_tests.py`, `data/test/step6_cases.csv`; changed `src/product_inference.py` (message text only) and `app/app.py` (two error messages only). No controller logic, saved GA parameter, dataset or earlier result file was changed; only error-message text was changed in the existing application files.

## 5. Failures, fixes and retests

### 5.1 Defects found in the application and fixed

| # | Found by | What failed (first run) | What was changed | Repeat result |
|---|---|---|---|---|
| D1 | R05 | With an invalid-JSON GA file the app showed a message with the raw exception text and no instruction (`Saved GA parameters in ga_best_params.json are unreadable or incomplete: JSONDecodeError(...)`). The approved requirement was a clear, **actionable** GA error. | `src/product_inference.py`: the unreadable/incomplete, non-finite and wrong-order messages now name the exception type only and end with "Restore results/step6/ga_best_params.json from the repository (do not re-run the GA here)." The missing-file message was already actionable and is unchanged. | R05 PASS; four new regression tests (`test_step6_resource_messages.py`) fail on the original code and pass now. |
| D2 | R07, R08 | When the Step 7 CSV or the benchmark CSV was missing, the tab error showed the raw exception including the full local path (e.g. `/tmp/.../project/results/step7/...`). The controllers were unaffected. | `app/app.py`: the two tab errors now show the exception type and name the file or folder to check (repo-relative). | R07 and R08 PASS; new regression test fails on the original code and passes now. |

The "before" evidence (`resource_tests_log_BEFORE_FIX.json`, `*_BEFORE_FIX.png`, `terminal-fix-regression-tests.txt`) is kept. After the fixes the **whole** suite was re-run: 95/95 unit tests on Python 3.11 and 3.13, all 34 browser rows, all 8 resource rows, the reference comparison (30 rows) and the consistency check (30,000/30,000) all pass, so Product V1 behaviour was not changed.

### 5.2 Problems in the test scripts (not application defects)

- First browser run stopped at N02 because choosing "Fuzzy" in the dropdown also matched "GA-optimised Fuzzy"; the script now matches the option text exactly. The whole browser script was then re-run from the start.
- First missing-resource run reported failures on R04 and others because the page keeps every tab's content, so info boxes from other tabs were read as errors; the script now counts only real error messages. The tests were then re-run from the start. (The genuine failures that remained after this correction are D1 and D2 above.)

### 5.3 Deliberate-fault check of the new rule-coverage tests

The 28 rule-coverage tests passed on the first run. To show they can fail, they were run against a throwaway copy of the project with the controller deliberately broken (`terminal-F-mutation-check.txt`): making rule R03 unable to fire gave 5 failures; moving the fan threshold 70 to 75 gave 1 failure; moving the humidity bump 80 to 85 gave 2 failures; the restored copy gave 0. The real controller was never modified.

### 5.4 Extra observations (not planned rows)

- **X01:** after the GA parameters have been loaded once, deleting the file while the same server is still running does not change the result (the app reads them once per server process and keeps them). The missing-file and corrupt-file errors therefore appear when the file is damaged *before the server starts* or before the first GA request. This matches the documented design; see section 6.
- **Stale Step 4 coverage results (A04):** 5 of the 10 rows of `results/step4/scenario_coverage_results.csv` differ from the current fuzzy controller (for example TEST-NORMAL-001 is saved as 60 / medium but the current controller gives 15.0 / low). They were not used as evidence in this step and the file was left untouched; current outputs are in `results/step6_testing/scenario_coverage_current.csv`.
- TEST-NORMAL-001 (24 / 50 / 20) and TEST-BOUNDARY-003 (24 / 75 / 1) have temperature exactly 24.0 = t1, which is the one input where all temperature rules have zero strength; these two "normal/boundary" scenarios therefore exercise the controller's fallback rather than its rules.

## 6. Known limits

- All inputs and results are synthetic; no real energy saving or measured indoor comfort is claimed. The application does not send HVAC commands.
- The energy action `save` is defined in the schema but no controller produces it.
- The older batch validator `src/validate_data.py` accepts humidity 0-100 while Product V1 enforces 20-100.
- "Compare all three" fails as a whole when the GA parameter file is missing (decision recorded before testing); Baseline and Fuzzy remain usable.
- The GA parameters (and the CSV tables) are cached per server process; a file changed or restored while the server runs is only noticed in some cases (see X01 and R04, where restoring worked because the failed load is not cached). Restart the app after changing resource files.
- The zero-strength fallback is reached only when temperature equals t1 exactly (24.0 default, 27.0 GA). Its `else cool_high` branch is unreachable for valid inputs (F15).
- The 10 hand-made coverage scenarios exercise only 5 of the 11 fuzzy rules (A04); full rule coverage comes from `test_fuzzy_rule_coverage.py`.
- Cooling values are compared with a 0.01 tolerance because Python 3.12+ sums floats slightly differently from 3.11 and earlier; fan level and energy action are compared exactly.
- Automated tests were run on Linux (Python 3.11.18 and 3.13.18) and on the team's Mac (Python 3.9.6; 95/95 tests passed).
- Mac manual checks M04-M07 were performed by the team leader in the running Streamlit app. The detailed Mac record is operator-written evidence, not a browser recording or screenshot.
- Linux browser checks are scripted (Playwright + Chrome); the Mac checks provide a separate manual confirmation for the listed scenarios.
- The temporary-copy tests prove behaviour on a copy of the project; the real files were never deleted or changed.

## 7. Contributions

**Vansh Sharma (Team Leader):** directed the Step 6 testing work; reviewed the test plan and code changes; ran the Mac environment check, full 95-test suite, 28 rule-coverage tests, consistency checks in a temporary copy, normal comparison and CSV validation, maximum-temperature boundary check, invalid-input checks, and missing-GA/recovery check. Verified the recorded results before preparing this report.

**AI assistance:** Claude AI assisted with preparing the test plan, scripts and initial Linux sandbox runs. The team leader executed and verified the Mac checks recorded in this document.

**Other team members:** No specific Step 6 testing or validation deliverables from the other team members were provided or independently evidenced for this report; therefore, no Step 6 technical contribution is attributed to them.
