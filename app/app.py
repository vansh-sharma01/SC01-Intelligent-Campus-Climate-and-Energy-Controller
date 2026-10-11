import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from baseline_controller import baseline_controller
from fuzzy_controller import fuzzy_controller


st.set_page_config(
    page_title="Campus Climate Controller",
    page_icon="🌱",
    layout="wide"
)

st.title("Intelligent Campus Climate & Energy Controller")

st.write(
    "Compare the Step 3 rule-based baseline controller "
    "with the Step 4 fuzzy logic controller."
)

st.sidebar.header("Room Scenario")

temperature = st.sidebar.slider(
    "Temperature (°C)",
    18.0, 45.0, 24.0, 0.5
)

humidity = st.sidebar.slider(
    "Humidity (%)",
    20.0, 100.0, 50.0, 1.0
)

occupancy = st.sidebar.slider(
    "Occupancy",
    0, 100, 20, 1
)

tariff = st.sidebar.selectbox(
    "Tariff Level",
    ["low", "medium", "high"]
)

scenario = pd.Series({
    "scenario_id": "LIVE-DEMO",
    "temperature_c": temperature,
    "humidity_pct": humidity,
    "occupancy_count": occupancy,
    "tariff_level": tariff
})

baseline_cooling, baseline_fan, baseline_action = baseline_controller(
    temperature,
    humidity,
    occupancy,
    tariff
)

fuzzy = fuzzy_controller(scenario)

st.subheader("Controller Comparison")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Step 3 — Baseline Controller")
    st.metric("Cooling", f"{baseline_cooling:.1f}%")
    st.write("Fan Level:", baseline_fan)
    st.write("Energy Action:", baseline_action)

with col2:
    st.markdown("### Step 4 — Fuzzy Controller")
    st.metric("Cooling", f"{fuzzy['cooling_pct']:.1f}%")
    st.write("Fan Level:", fuzzy["fan_level"])
    st.write("Energy Action:", fuzzy["energy_action"])

st.subheader("Cooling Difference")

cooling_difference = float(fuzzy["cooling_pct"]) - float(baseline_cooling)

st.metric(
    "Fuzzy − Baseline",
    f"{cooling_difference:+.1f}%"
)

st.subheader("Scenario Inputs")

input_table = pd.DataFrame({
    "Parameter": ["Temperature", "Humidity", "Occupancy", "Tariff"],
    "Value": [
        f"{temperature:.1f} °C",
        f"{humidity:.0f}%",
        occupancy,
        tariff
    ]
})

st.table(input_table)

st.subheader("Controller Output")

output_table = pd.DataFrame({
    "Output": ["Cooling", "Fan Level", "Energy Action"],
    "Baseline": [
        f"{baseline_cooling:.1f}%",
        baseline_fan,
        baseline_action
    ],
    "Fuzzy": [
        f"{fuzzy['cooling_pct']:.1f}%",
        fuzzy["fan_level"],
        fuzzy["energy_action"]
    ]
})

st.table(output_table)

st.info(
    "The fuzzy controller uses overlapping membership functions "
    "and fuzzy rules to produce a continuous cooling recommendation."
)
