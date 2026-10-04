# Step 4 - Fuzzy Controller

## Purpose

Step 4 implements the Soft Computing method for the Intelligent Campus
Climate and Energy Controller.

The fuzzy controller takes room temperature, humidity, occupancy, and
electricity tariff as inputs and recommends cooling intensity, fan level,
and an energy-management action.

Unlike the Step 3 baseline, which uses fixed temperature thresholds, the
fuzzy controller uses overlapping membership functions and fuzzy inference
to produce gradual cooling recommendations.

## Inputs

| Input | Unit / Type | Range / Values |
|---|---|---|
| temperature | °C | 18–45 |
| humidity | % | 20–100 |
| occupancy | people | 0–100 for generated scenarios |
| tariff | category | low, medium, high |

The continuous inputs use fuzzy membership functions.

Tariff remains a categorical input because it represents an electricity
price band rather than a continuous physical measurement.

## Temperature Membership Functions

Temperature has three fuzzy sets:

- **comfortable**: approximately 18–24 °C
- **warm**: approximately 22–32 °C
- **hot**: approximately 30–45 °C

The membership functions overlap intentionally. A temperature near a
boundary can therefore have partial membership in more than one category.

## Humidity Membership Functions

Humidity has three fuzzy sets:

- **low**: approximately 20–50%
- **moderate**: approximately 40–80%
- **high**: approximately 70–100%

The overlap allows the controller to respond gradually to changing
humidity rather than using one hard humidity threshold.

## Occupancy Membership Functions

Occupancy has four fuzzy sets:

- **empty**: approximately 0–1 person
- **low**: approximately 0–40 people
- **medium**: approximately 25–75 people
- **high**: approximately 60–100 people

The generated Step 2 scenarios use 0–100 people.

## Cooling Output Membership Functions

Cooling intensity has four fuzzy sets:

- **off**: approximately 0–10%
- **low**: approximately 5–40%
- **medium**: approximately 30–75%
- **high**: approximately 65–100%

The fuzzy inference system defuzzifies the result to a continuous value
between 0 and 100%.

## Main Fuzzy Rules

The controller uses rules such as:

1. If occupancy is empty, cooling is off.
2. If temperature is comfortable and occupancy is low, cooling is low.
3. If temperature is comfortable and occupancy is medium, cooling is low.
4. If temperature is comfortable and occupancy is high, cooling is medium.
5. If temperature is warm and occupancy is low, cooling is medium.
6. If temperature is warm and occupancy is medium, cooling is medium.
7. If temperature is warm and occupancy is high, cooling is high.
8. If temperature is hot and occupancy is low, cooling is high.
9. If temperature is hot and occupancy is medium, cooling is high.
10. If temperature is hot and occupancy is high, cooling is high.
11. If humidity is high and temperature is warm, cooling is medium.
12. If humidity is high and temperature is hot, cooling is high.

The rules are combined using fuzzy inference and the cooling output is
defuzzified to obtain a continuous cooling percentage.

## Fan-Level Decision

The cooling result is converted into the required fan categories:

- cooling below 30% -> low fan
- cooling from 30% to below 70% -> medium fan
- cooling 70% or higher -> high fan

When humidity is above 75%, the fan level is increased by one band when
possible.

An empty room always has fan level `off`.

## Energy Action

Tariff and cooling demand determine the energy action:

- high tariff -> `avoid_peak`
- non-high tariff with low cooling demand -> `save`
- otherwise -> `normal`

An empty room uses an energy-saving action, with `avoid_peak` retained
for high tariff.

## Difference from Step 3 Baseline

The Step 3 baseline uses fixed thresholds:

- below 24 °C -> 10% cooling
- 24–30 °C -> 50% cooling
- above 30 °C -> 90% cooling

The Step 4 fuzzy controller instead uses overlapping membership functions
and fuzzy inference. Therefore, it can produce intermediate values such as
53.0%, 83.9%, and 21.9%.

## Step 4 Test Evidence

The five mandatory starter scenarios were executed successfully.

| Scenario | Temperature | Humidity | Occupancy | Tariff | Cooling | Fan | Energy |
|---|---:|---:|---:|---|---:|---|---|
| SC01-001 | 24 | 50 | 20 | low | 53.0% | medium | normal |
| SC01-002 | 36 | 85 | 45 | medium | 83.9% | high | normal |
| SC01-003 | 38 | 60 | 0 | high | 0.0% | off | avoid_peak |
| SC01-004 | 45 | 70 | 50 | high | 82.5% | high | avoid_peak |
| SC01-005 | 21 | 90 | 15 | low | 21.9% | medium | save |

The complete output is stored in:

`results/step4/fuzzy_results.csv`

## Limitations

The generated scenarios are synthetic testing scenarios, not real measured
campus HVAC data.

The membership-function boundaries are project assumptions based on the
documented environmental ranges. They are suitable for the M1 prototype
but should be tuned or validated against real building data in future work.

Genetic Algorithm optimisation of these fuzzy settings belongs to M2 and
is not part of this Step 4 implementation.
