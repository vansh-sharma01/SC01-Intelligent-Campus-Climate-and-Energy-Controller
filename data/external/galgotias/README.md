# Galgotias University Campus Energy Benchmark

## Primary source

Galgotias University, NIRF 2026 submission.

Official source:
https://www.galgotiasuniversity.edu.in/public/uploads/media/hPCbMYYPBCpGctNFiHjaDSfa0wPYd5Vbh3ihvSc6.pdf

## Dataset

File: campus_energy_benchmark.csv

Coverage:
- Academic years: 2022-23, 2023-24, 2024-25
- Institution: Galgotias University
- Scope: Campus-level energy consumption and renewable generation.

## Original reported fields

- Total electricity consumed (kWh)
- Renewable energy installed (kWp)
- Renewable energy generated (kWh)
- Total built-up area (sq. ft.)

## Derived fields

1. Electricity consumption per sq. ft.
   = Total electricity consumed / Built-up area

2. Renewable generation percentage
   = Renewable energy generated / Total electricity consumed * 100

## Limitations

- These are campus-level figures, not classroom-level measurements.
- They do not represent HVAC-only electricity consumption.
- They do not directly validate SC01 controller performance.
- SC01 controller comparisons continue to use the same
  10,000 synthetic scenarios.
- No actual energy savings from SC01 are claimed using this dataset.
