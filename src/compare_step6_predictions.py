"""Compare CSV files downloaded from the application with the reference.

Run from the repository root:

    python src/compare_step6_predictions.py \\
        --reference results/step6_testing/reference_predictions.csv \\
        docs/evidence/step6/downloads/*.csv

Matching rule (documented tolerance):
  * controller, the four inputs, fan_level and energy_action must match
    EXACTLY (text compared as written; inputs compared as numbers);
  * cooling_pct must match within 0.01 percentage points. Python 3.12+ adds
    floats more accurately than Python 3.11 and earlier, so a controller value
    sitting exactly on a rounding boundary can differ by 0.01 between Python
    versions. Anything larger than 0.01 is a difference.

Every row of every downloaded file must have a reference row with the same
controller and inputs, and its outputs must agree. Prints PASS, or lists every
difference and exits with code 1. Exit code 2 means the files could not be
read (a missing file or column is never reported as PASS).
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

COOLING_TOLERANCE = 0.01
KEY = ["controller", "temperature_c", "humidity_pct", "occupancy_count",
       "tariff_level"]
NUMERIC_KEY = ["temperature_c", "humidity_pct", "occupancy_count"]
REQUIRED = KEY + ["cooling_pct", "fan_level", "energy_action"]


def load(path):
    frame = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in frame.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    if frame.empty:
        raise ValueError(f"{path}: no data rows")
    for column in NUMERIC_KEY + ["cooling_pct"]:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    return frame


def key_of(row):
    return (row["controller"], float(row["temperature_c"]),
            float(row["humidity_pct"]), float(row["occupancy_count"]),
            str(row["tariff_level"]))


def compare(reference, actual, label):
    """Return a list of difference descriptions for one downloaded file."""
    ref_rows = {}
    for _, row in reference.iterrows():
        ref_rows[key_of(row)] = row
    problems = []
    for index, row in actual.iterrows():
        where = f"{label} row {index + 1} ({row['controller']}, " \
                f"{row['temperature_c']}/{row['humidity_pct']}/" \
                f"{row['occupancy_count']}/{row['tariff_level']})"
        ref = ref_rows.get(key_of(row))
        if ref is None:
            problems.append(f"{where}: no reference row for these inputs")
            continue
        if row["fan_level"] != ref["fan_level"]:
            problems.append(f"{where}: fan_level {row['fan_level']!r} "
                            f"!= reference {ref['fan_level']!r}")
        if row["energy_action"] != ref["energy_action"]:
            problems.append(f"{where}: energy_action {row['energy_action']!r}"
                            f" != reference {ref['energy_action']!r}")
        diff = abs(float(row["cooling_pct"]) - float(ref["cooling_pct"]))
        if diff > COOLING_TOLERANCE + 1e-9:
            problems.append(f"{where}: cooling_pct {row['cooling_pct']} "
                            f"differs from reference {ref['cooling_pct']} "
                            f"by {diff:.4f} (tolerance {COOLING_TOLERANCE})")
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--reference", required=True)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args(argv)

    try:
        reference = load(args.reference)
        loaded = [(Path(f).name, load(f)) for f in args.files]
    except (OSError, ValueError, pd.errors.ParserError) as error:
        print(f"ERROR: {error}")
        return 2

    problems = []
    total = 0
    for name, frame in loaded:
        total += len(frame)
        problems.extend(compare(reference, frame, name))

    print(f"Files compared: {len(loaded)}; rows compared: {total}; "
          f"cooling tolerance: +/-{COOLING_TOLERANCE}")
    if problems:
        print(f"DIFFERENCES FOUND ({len(problems)}):")
        for problem in problems:
            print(" -", problem)
        return 1
    print("PASS: every downloaded row matches the reference "
          "(fan level and energy action exactly, cooling within tolerance).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
