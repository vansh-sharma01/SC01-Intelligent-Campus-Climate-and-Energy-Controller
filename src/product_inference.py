"""SC01 Product V1 inference layer.

Connects the user interface to the project's existing controllers:

    User input -> validation -> existing controller -> output checks -> result

Nothing here re-implements controller logic. The three controllers are the
functions already used by the Step 3-7 experiments:

* ``baseline_controller``  (src/baseline_controller.py)
* ``fuzzy_controller``     (src/fuzzy_controller.py)
* ``fuzzy_controller`` with the saved GA parameters
  (results/step6/ga_best_params.json)

No controller is trained or re-optimised here. The GA parameters are only
read from the saved file; if that file is missing or invalid an error is
raised instead of silently substituting the ordinary fuzzy controller.

All results are simulated recommendations produced from synthetic-data
controllers. They are not HVAC commands and are not measured energy
savings or measured comfort outcomes.
"""

import json
import math
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

GA_PARAMS_PATH = ROOT / "results" / "step6" / "ga_best_params.json"

# Input schema. These ranges are the Step 1 contract (docs/STEP-1.md) and the
# domain of the generated scenarios (src/generate_scenarios.py).
TEMPERATURE_RANGE = (18.0, 45.0)   # degrees Celsius
HUMIDITY_RANGE = (20.0, 100.0)     # relative humidity, %
OCCUPANCY_RANGE = (0, 100)         # whole number of people in the room
TARIFFS = ("low", "medium", "high")
INPUT_FIELDS = ("temperature_c", "humidity_pct", "occupancy_count", "tariff_level")

# Output schema (as produced by the existing controllers).
FAN_LEVELS = ("off", "low", "medium", "high")
ENERGY_ACTIONS = ("normal", "save", "avoid_peak")  # "save" is never produced
COOLING_RANGE = (0.0, 100.0)

CONTROLLERS = {
    "baseline": "Baseline",
    "fuzzy": "Fuzzy",
    "ga_fuzzy": "GA-optimised Fuzzy",
}

GA_PARAM_KEYS = ("t1", "t2", "t3", "cool_low", "cool_medium", "cool_high")

NOTICE = (
    "Simulated recommendation from controllers built on synthetic data. "
    "Not an HVAC command; no real energy savings or indoor comfort have "
    "been measured."
)

OUTPUT_COLUMNS = (
    "controller",
    "temperature_c",
    "humidity_pct",
    "occupancy_count",
    "tariff_level",
    "cooling_pct",
    "fan_level",
    "energy_action",
    "notice",
)


class InputValidationError(ValueError):
    """Invalid user input. ``errors`` maps each bad field to its message."""

    def __init__(self, errors):
        self.errors = dict(errors)
        super().__init__("; ".join(self.errors.values()))


class ControllerLoadError(RuntimeError):
    """A controller, or its saved parameters, could not be loaded."""


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

def _to_number(raw):
    """Return a finite float, or raise ValueError with a short reason."""
    if isinstance(raw, bool):
        raise ValueError("enter a number.")
    if isinstance(raw, str):
        text = raw.strip()
        # float() would accept things like "1_0"; keep input plain.
        if "_" in text:
            raise ValueError("enter a number.")
        raw = text
    try:
        number = float(raw)
    except (TypeError, ValueError):
        raise ValueError("enter a number.") from None
    if not math.isfinite(number):
        raise ValueError("use a finite number (not NaN or infinity).")
    return number


def _is_blank(raw):
    return raw is None or (isinstance(raw, str) and raw.strip() == "")


def validate_inputs(values):
    """Validate one room scenario and return cleaned values.

    ``values`` is a mapping with the keys in ``INPUT_FIELDS``. Every problem
    is collected so the user sees all of them at once. Invalid values are
    never replaced by defaults. Raises ``InputValidationError`` (a
    ``ValueError``) on any problem.
    """
    if not hasattr(values, "get"):
        raise InputValidationError({"input": "input must be a set of named fields."})

    errors = {}
    clean = {}

    lo, hi = TEMPERATURE_RANGE
    raw = values.get("temperature_c")
    if _is_blank(raw):
        errors["temperature_c"] = f"Temperature: enter a value ({lo:g}-{hi:g} °C)."
    else:
        try:
            number = _to_number(raw)
        except ValueError as problem:
            errors["temperature_c"] = f"Temperature: {problem}"
        else:
            if not lo <= number <= hi:
                errors["temperature_c"] = (
                    f"Temperature: {number:g} °C is outside the valid range "
                    f"{lo:g}-{hi:g} °C."
                )
            else:
                clean["temperature_c"] = number

    lo, hi = HUMIDITY_RANGE
    raw = values.get("humidity_pct")
    if _is_blank(raw):
        errors["humidity_pct"] = f"Humidity: enter a value ({lo:g}-{hi:g} %)."
    else:
        try:
            number = _to_number(raw)
        except ValueError as problem:
            errors["humidity_pct"] = f"Humidity: {problem}"
        else:
            if not lo <= number <= hi:
                errors["humidity_pct"] = (
                    f"Humidity: {number:g} % is outside the valid range "
                    f"{lo:g}-{hi:g} %."
                )
            else:
                clean["humidity_pct"] = number

    lo, hi = OCCUPANCY_RANGE
    raw = values.get("occupancy_count")
    if _is_blank(raw):
        errors["occupancy_count"] = f"Occupancy: enter a value ({lo}-{hi} people)."
    else:
        try:
            number = _to_number(raw)
        except ValueError as problem:
            errors["occupancy_count"] = f"Occupancy: {problem}"
        else:
            if number != int(number):
                errors["occupancy_count"] = (
                    "Occupancy: enter a whole number of people."
                )
            elif not lo <= number <= hi:
                errors["occupancy_count"] = (
                    f"Occupancy: {number:g} people is outside the valid range "
                    f"{lo}-{hi} people."
                )
            else:
                clean["occupancy_count"] = int(number)

    raw = values.get("tariff_level")
    allowed = ", ".join(TARIFFS)
    if _is_blank(raw):
        errors["tariff_level"] = f"Tariff: choose one of {allowed}."
    elif not isinstance(raw, str):
        errors["tariff_level"] = f"Tariff: choose one of {allowed}."
    else:
        tariff = raw.strip().lower()
        if tariff not in TARIFFS:
            errors["tariff_level"] = (
                f"Tariff: '{raw.strip()}' is not valid; choose one of {allowed}."
            )
        else:
            clean["tariff_level"] = tariff

    if errors:
        raise InputValidationError(errors)
    return clean


# --------------------------------------------------------------------------
# Loading the existing controllers and the saved GA parameters
# --------------------------------------------------------------------------

def _load_controller_functions():
    try:
        from baseline_controller import baseline_controller
        from fuzzy_controller import fuzzy_controller
    except Exception as error:  # missing file, bad import, missing package
        raise ControllerLoadError(
            f"The existing controller code could not be imported: {error}"
        ) from error
    return baseline_controller, fuzzy_controller


_GA_RESTORE_HINT = (
    "Restore results/step6/ga_best_params.json from the repository "
    "(do not re-run the GA here)."
)


def load_ga_params(path=None):
    """Read the saved GA-optimised fuzzy parameters.

    Raises ``ControllerLoadError`` if the file is missing or unusable. It
    never falls back to the ordinary fuzzy parameters.
    """
    path = Path(path) if path is not None else GA_PARAMS_PATH
    if not path.is_file():
        try:
            shown = path.relative_to(ROOT)
        except ValueError:
            shown = path
        raise ControllerLoadError(
            f"Saved GA parameters not found: {shown.as_posix()}. Restore "
            "results/step6/ga_best_params.json (do not re-run the GA here)."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        saved = data["parameters"]
        params = {key: float(saved[key]) for key in GA_PARAM_KEYS}
    except (ValueError, KeyError, TypeError) as error:
        raise ControllerLoadError(
            f"Saved GA parameters in {path.name} are unreadable or incomplete "
            f"({type(error).__name__}). {_GA_RESTORE_HINT}"
        ) from error

    if not all(math.isfinite(value) for value in params.values()):
        raise ControllerLoadError(
            f"{path.name} contains non-finite parameters. {_GA_RESTORE_HINT}"
        )
    t_lo, t_hi = TEMPERATURE_RANGE
    if not t_lo < params["t1"] < params["t2"] < params["t3"] < t_hi:
        raise ControllerLoadError(
            f"{path.name}: temperature parameters must satisfy "
            f"{t_lo:g} < t1 < t2 < t3 < {t_hi:g}. {_GA_RESTORE_HINT}"
        )
    return params


# --------------------------------------------------------------------------
# Recommendation
# --------------------------------------------------------------------------

def _run_controller(controller, clean, ga_params):
    baseline_controller, fuzzy_controller = _load_controller_functions()

    if controller == "baseline":
        cooling, fan, action = baseline_controller(
            clean["temperature_c"],
            clean["humidity_pct"],
            clean["occupancy_count"],
            clean["tariff_level"],
        )
    elif controller in ("fuzzy", "ga_fuzzy"):
        params = None
        if controller == "ga_fuzzy":
            params = ga_params if ga_params is not None else load_ga_params()
        # fuzzy_controller reads these four fields from a row-like mapping.
        import pandas as pd

        out = fuzzy_controller(pd.Series(clean), params=params)
        cooling, fan, action = (
            out["cooling_pct"], out["fan_level"], out["energy_action"]
        )
    else:
        raise ValueError(
            f"Unknown controller '{controller}'. Choose one of: "
            + ", ".join(CONTROLLERS)
        )

    cooling = float(cooling)
    if not math.isfinite(cooling) or not COOLING_RANGE[0] <= cooling <= COOLING_RANGE[1]:
        raise RuntimeError(
            f"{CONTROLLERS[controller]} returned an invalid cooling value: {cooling!r}"
        )
    if fan not in FAN_LEVELS:
        raise RuntimeError(
            f"{CONTROLLERS[controller]} returned an unknown fan level: {fan!r}"
        )
    if action not in ENERGY_ACTIONS:
        raise RuntimeError(
            f"{CONTROLLERS[controller]} returned an unknown energy action: {action!r}"
        )

    return {
        "controller": controller,
        "temperature_c": clean["temperature_c"],
        "humidity_pct": clean["humidity_pct"],
        "occupancy_count": clean["occupancy_count"],
        "tariff_level": clean["tariff_level"],
        "cooling_pct": cooling,
        "fan_level": str(fan),
        "energy_action": str(action),
        "notice": NOTICE,
    }


def recommend(values, controller="fuzzy", ga_params=None):
    """Validate ``values`` and return one controller's recommendation."""
    if controller not in CONTROLLERS:
        raise ValueError(
            f"Unknown controller '{controller}'. Choose one of: "
            + ", ".join(CONTROLLERS)
        )
    clean = validate_inputs(values)
    return _run_controller(controller, clean, ga_params)


def recommend_all(values, ga_params=None):
    """Validate once and return recommendations from all three controllers."""
    clean = validate_inputs(values)
    if ga_params is None:
        ga_params = load_ga_params()
    return [_run_controller(name, clean, ga_params) for name in CONTROLLERS]


def results_to_csv(results):
    """Return CSV text of recommendation results (submitted inputs, selected
    controller, outputs and the limitation notice)."""
    import pandas as pd

    frame = pd.DataFrame(list(results), columns=list(OUTPUT_COLUMNS))
    return frame.to_csv(index=False)
