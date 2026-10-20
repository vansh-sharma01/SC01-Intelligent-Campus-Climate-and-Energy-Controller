
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from baseline_controller import baseline_controller
from fuzzy_controller import fuzzy_controller


st.set_page_config(
    page_title="Campus Climate Controller",
    page_icon="🌱",
    layout="wide",
)

st.title("Intelligent Campus Climate & Energy Controller")

st.write(
    "Explore and compare three simulated controllers: "
    "a rule-based baseline, fuzzy logic, and GA-tuned fuzzy logic."
)

st.caption(
    "This is a simulation using synthetic optimization data, "
    "not a physical HVAC controller or proof of measured energy savings."
)

# Load previously saved GA parameters. Do not retrain the GA here.
params_path = ROOT / "results" / "step6" / "ga_best_params.json"

with params_path.open("r", encoding="utf-8") as file:
    ga_results = json.load(file)

ga_params = ga_results["parameters"]

# Scenario inputs
st.sidebar.header("Room Scenario")

temperature = st.sidebar.slider(
    "Temperature (°C)", 18.0, 45.0, 24.0, 0.5
)
humidity = st.sidebar.slider(
    "Humidity (%)", 20.0, 100.0, 50.0, 1.0
)
occupancy = st.sidebar.slider(
    "Occupancy", 0, 100, 20, 1
)
tariff = st.sidebar.selectbox(
    "Tariff Level", ["low", "medium", "high"]
)

scenario = pd.Series({
    "scenario_id": "LIVE-DEMO",
    "temperature_c": temperature,
    "humidity_pct": humidity,
    "occupancy_count": occupancy,
    "tariff_level": tariff,
})

# Run all three controllers
baseline_cooling, baseline_fan, baseline_action = baseline_controller(
    temperature, humidity, occupancy, tariff
)

fuzzy = fuzzy_controller(scenario)
ga_fuzzy = fuzzy_controller(scenario, params=ga_params)

controllers = {
    "Baseline": {
        "Cooling (%)": float(baseline_cooling),
        "Fan Level": baseline_fan,
        "Energy Action": baseline_action,
    },
    "Fuzzy": {
        "Cooling (%)": float(fuzzy["cooling_pct"]),
        "Fan Level": fuzzy["fan_level"],
        "Energy Action": fuzzy["energy_action"],
    },
    "GA-tuned Fuzzy": {
        "Cooling (%)": float(ga_fuzzy["cooling_pct"]),
        "Fan Level": ga_fuzzy["fan_level"],
        "Energy Action": ga_fuzzy["energy_action"],
    },
}

# Main comparison
st.subheader("Three-Controller Comparison")

columns = st.columns(3)

for column, (name, values) in zip(columns, controllers.items()):
    with column:
        st.markdown(f"### {name}")
        st.metric("Cooling", f"{values['Cooling (%)']:.2f}%")
        st.write("**Fan level:**", values["Fan Level"])
        st.write("**Energy action:**", values["Energy Action"])

# Output table
st.subheader("Output Comparison")

output_table = pd.DataFrame(controllers)
output_table.insert(
    0, "Output", ["Cooling (%)", "Fan Level", "Energy Action"]
)
output_table["Output"] = output_table["Output"].astype(str)

st.dataframe(
    output_table,
    hide_index=True,
    use_container_width=True,
)

# New: explanation of controller recommendations
st.subheader("Recommendation Explanation")

if occupancy == 0:
    st.info(
        "The room is unoccupied. All three controllers are evaluated for "
        "this scenario; check the comparison above for their actual outputs."
    )
else:
    st.write(
        f"**Baseline:** At {temperature:.1f} °C, the baseline uses fixed "
        "temperature thresholds to select cooling. Humidity can also "
        "increase its fan level."
    )

    st.write(
        f"**Fuzzy:** This controller combines temperature, occupancy, "
        "and humidity through fuzzy membership rules. Its output for this "
        f"scenario is {fuzzy['cooling_pct']:.2f}% cooling with a "
        f"{fuzzy['fan_level']} fan."
    )

    st.write(
        "**GA-tuned Fuzzy:** This uses the fuzzy controller with parameters "
        "saved from the genetic-algorithm optimization experiment. Its "
        f"output is {ga_fuzzy['cooling_pct']:.2f}% cooling with a "
        f"{ga_fuzzy['fan_level']} fan."
    )

if tariff == "high":
    st.write(
        "**Tariff note:** The high tariff selects the `avoid_peak` "
        "energy action."
    )
else:
    st.write(
        f"**Tariff note:** The {tariff} tariff selects the `normal` "
        "energy action."
    )

# New: visual cooling comparison
st.subheader("Cooling Output Chart")

cooling_chart = pd.DataFrame({
    "Controller": list(controllers.keys()),
    "Cooling (%)": [
        values["Cooling (%)"] for values in controllers.values()
    ],
}).set_index("Controller")

st.bar_chart(cooling_chart, y="Cooling (%)")

# Existing: cooling differences
st.subheader("Cooling Differences")

difference_table = pd.DataFrame({
    "Comparison": [
        "Fuzzy − Baseline",
        "GA-tuned Fuzzy − Baseline",
    ],
    "Cooling Difference (percentage points)": [
        float(fuzzy["cooling_pct"]) - float(baseline_cooling),
        float(ga_fuzzy["cooling_pct"]) - float(baseline_cooling),
    ],
})

st.dataframe(
    difference_table,
    hide_index=True,
    use_container_width=True,
)

# Scenario input summary
st.subheader("Scenario Inputs")

input_table = pd.DataFrame({
    "Parameter": [
        "Temperature",
        "Humidity",
        "Occupancy",
        "Tariff",
    ],
    "Value": [
        f"{temperature:.1f} °C",
        f"{humidity:.0f}%",
        occupancy,
        tariff,
    ],
})

st.dataframe(
    input_table,
    hide_index=True,
    use_container_width=True,
)
