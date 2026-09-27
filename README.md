# SC01 – Intelligent Campus Climate and Energy Controller

## Project Overview

SC01 is an Intelligent Campus Climate and Energy Controller designed to recommend suitable room cooling and energy actions based on environmental and occupancy conditions.

The system takes room temperature, humidity, occupancy, and electricity tariff as inputs and produces recommendations

The first version uses a simple rule-based baseline controller. In later stages, this baseline will be compared with Soft Computing approaches such as fuzzy logic.

## Problem Statement

Given:

* Room temperature
* Humidity
* Occupancy count
* Electricity tariff level

The system should recommend:

* Cooling percentage
* Fan level
* Energy action

The intended user is a **campus facility manager** who needs simple recommendations for managing classroom or room climate while considering energy usage.

## Input Variables

| Variable          | Meaning                      | Unit / Values           |
| ----------------- | ---------------------------- | ----------------------- |
| `scenario_id`     | Unique scenario identifier   | Text                    |
| `temperature_c`   | Room temperature             | °C                      |
| `humidity_pct`    | Relative humidity            | %                       |
| `occupancy_count` | Number of people in the room | Integer                 |
| `tariff_level`    | Electricity tariff category  | `low`, `medium`, `high` |

## Output Variables

| Variable        | Meaning                   | Values                         |
| --------------- | ------------------------- | ------------------------------ |
| `cooling_pct`   | Recommended cooling level | 0–100%                         |
| `fan_level`     | Recommended fan level     | `off`, `low`, `medium`, `high` |
| `energy_action` | Recommended energy action | `normal`, `save`, `avoid_peak` |

## Baseline Controller

The current baseline uses simple deterministic rules.

Main rules:

1. If occupancy is zero, cooling is set to 0 and the fan is off.
2. If temperature is below 24°C, cooling is set to 10%.
3. If temperature is between 24°C and 30°C, cooling is set to 50%.
4. If temperature is above 30°C, cooling is set to 90%.
5. If humidity is above 75%, the fan level is increased by one band.
6. If the tariff is high, the energy action is `avoid_peak`; otherwise it is `normal`.

The detailed pseudocode is available in:

`docs/baseline-pseudocode.md`

## Project Structure

```text
SC01-Intelligent-Campus-Climate-and-Energy-Controller/
│
├── data/
│   ├── sample_input.csv
│   └── test/
│       └── invalid_input.csv
│
├── docs/
│   ├── STEP-1.md
│   └── baseline-pseudocode.md
│
├── src/
│   └── validate_data.py
│
├── .gitignore
└── README.md
```

## Validation

The validation program checks:

* Required columns
* Missing values
* Numeric input fields
* Temperature range
* Humidity range
* Occupancy values
* Valid tariff levels
* Duplicate scenario IDs

Run the validation from the project root using:

```bash
python src/validate_data.py
```

A valid dataset should finish with:

```text
STEP 1 DATA CHECK PASSED
```

An intentionally invalid dataset should produce a clear validation error.

## Team Workflow

### Team Members

* Vansh Sharma
* Manshi Tiwari
* Lakshya Sharma
* Akash Dubey

### Git Workflow

Each team member should:

1. Work on an assigned project task.
2. Make a meaningful change.
3. Test the change locally.
4. Commit the change with a clear commit message.
5. Push the commit to the shared GitHub repository.

Example:

```bash
git status
git add .
git commit -m "Describe the completed task"
git push origin main
```

The team should review important changes before the Step 1 faculty demonstration.

## Development Plan

### Step 1 – Baseline and Project Contract

* Define the project problem.
* Define inputs and outputs.
* Prepare starter data.
* Validate the data.
* Define baseline rules.
* Prepare test cases.
* Prepare the Product V1 screen sketch.
* Record validation and demonstration evidence.

### Step 2 – Data and Scenario Pipeline

The next stage will expand the small starter dataset into a reproducible scenario dataset suitable for further development.

### Future Soft Computing Controller

After the baseline is established, the project can be extended with Soft Computing methods such as fuzzy logic and compared against the baseline controller.

## Current Status

**Step 1 development is in progress.**

Completed components include the starter dataset, validation program, and baseline pseudocode. Remaining Step 1 documentation, product sketch, test-case documentation, and evidence will be completed before the faculty demonstration.

