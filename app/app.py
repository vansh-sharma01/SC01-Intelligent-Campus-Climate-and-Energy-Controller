"""SC01 Product V1 - Intelligent Campus Climate and Energy Controller.

Run from the repository root:

    python -m streamlit run app/app.py

Flow: user input -> validation -> existing controller -> result display.
All recommendations come from the project's existing controllers through
src/product_inference.py. Nothing is trained or optimised when a button is
pressed, and no result is hard-coded.
"""

import ast
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import product_inference as pi  # noqa: E402
from check_product_consistency import direct_call  # noqa: E402

st.set_page_config(
    page_title="Campus Climate Controller - Product V1",
    page_icon="🌱",
    layout="wide",
)

LABELS = pi.CONTROLLERS  # internal name -> display name
COMPARE_ALL = "Compare all three controllers"
CHOICES = [*LABELS.values(), COMPARE_ALL]
ACTION_DISPLAY = {"normal": "Normal", "avoid_peak": "Avoid Peak", "save": "Save"}

SCOPE_NOTICE = (
    "**Simulation only.** This tool uses controllers built on synthetic "
    "scenarios. Recommendations are not HVAC commands, and no real "
    "electricity savings or indoor-comfort improvements have been measured."
)


def fan_text(value):
    return value.capitalize()


def action_text(value):
    return ACTION_DISPLAY.get(value, value)


@st.cache_resource
def saved_ga_params():
    """Read the saved GA parameters once. The GA is never re-run here."""
    return pi.load_ga_params()


@st.cache_data
def read_csv(relative_path):
    return pd.read_csv(ROOT / relative_path)


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------

st.title("Intelligent Campus Climate & Energy Controller")
st.caption("Product V1 · simulation-based decision-support demonstration")
st.warning(SCOPE_NOTICE)

with st.sidebar:
    st.header("About this demo")
    st.write(
        "**Purpose:** let a campus facility manager or building operator "
        "explore simulated cooling, fan and energy-action recommendations "
        "for a room, given its conditions and the electricity tariff."
    )
    st.write(
        "**Methods:** a fixed-rule baseline, a fuzzy-logic controller, and a "
        "genetic-algorithm (GA) optimised fuzzy controller."
    )
    st.caption(
        "Educational demonstration. Not connected to any building system or "
        "live sensor."
    )

tab_recommend, tab_eval, tab_campus, tab_about = st.tabs([
    "Recommendation",
    "Evaluation results (synthetic)",
    "Campus energy benchmark",
    "About & limitations",
])

# --------------------------------------------------------------------------
# Recommendation
# --------------------------------------------------------------------------

with tab_recommend:
    st.subheader("1. Choose a controller")
    choice = st.selectbox(
        "Controller",
        CHOICES,
        index=0,
        key="controller_choice",
        help="Pick one controller, or compare all three on identical inputs.",
    )
    comparing = choice == COMPARE_ALL
    button_label = "Compare Controllers" if comparing else "Generate Recommendation"

    st.subheader("2. Enter room conditions")
    with st.form("room_scenario"):
        col_t, col_h, col_o, col_p = st.columns(4)
        with col_t:
            st.text_input(
                "Temperature (°C)", value="25", key="temperature_c",
                help="Whole or decimal number.",
            )
            st.caption("Valid range: 18–45 °C")
        with col_h:
            st.text_input(
                "Relative humidity (%)", value="55", key="humidity_pct",
                help="Whole or decimal number.",
            )
            st.caption("Valid range: 20–100 %")
        with col_o:
            st.text_input(
                "Occupancy (people in room)", value="50", key="occupancy_count",
                help="Number of people, as a whole number.",
            )
            st.caption("Valid range: 0–100 people (whole number)")
        with col_p:
            st.selectbox(
                "Electricity tariff", list(pi.TARIFFS), index=1,
                key="tariff_level", format_func=str.capitalize,
            )
            st.caption("Low, Medium or High")
        submitted = st.form_submit_button(button_label, type="primary")

    if submitted:
        values = {name: st.session_state[name] for name in pi.INPUT_FIELDS}
        st.session_state.pop("results", None)
        st.session_state.pop("problem", None)
        try:
            if comparing:
                results = pi.recommend_all(values, ga_params=saved_ga_params())
            else:
                name = next(k for k, v in LABELS.items() if v == choice)
                params = saved_ga_params() if name == "ga_fuzzy" else None
                results = [pi.recommend(values, name, ga_params=params)]
        except pi.InputValidationError as error:
            st.session_state["problem"] = ("input", error.errors)
        except pi.ControllerLoadError as error:
            st.session_state["problem"] = ("load", str(error))
        except Exception as error:  # never show a raw traceback to the user
            st.session_state["problem"] = ("other", str(error))
        else:
            st.session_state["results"] = results

    problem = st.session_state.get("problem")
    results = st.session_state.get("results")

    if problem:
        kind, detail = problem
        if kind == "input":
            st.error(
                "No recommendation was produced because some inputs are "
                "invalid. Please correct them and try again:"
            )
            for message in detail.values():
                st.markdown(f"- {message}")
        elif kind == "load":
            st.error(f"A controller could not be loaded: {detail}")
            st.info(
                "Check that the repository files are complete (see the "
                "README) and run the app from the repository root."
            )
        else:
            st.error(f"The recommendation could not be completed: {detail}")

    if results:
        first = results[0]
        st.subheader("3. Results")
        st.caption(
            f"Inputs used: {first['temperature_c']:g} °C · "
            f"{first['humidity_pct']:g} % humidity · "
            f"{first['occupancy_count']} people · "
            f"{first['tariff_level'].capitalize()} tariff"
        )

        columns = st.columns(len(results))
        for column, result in zip(columns, results):
            with column, st.container(border=True):
                st.markdown(f"#### {LABELS[result['controller']]}")
                st.metric("Cooling recommendation", f"{result['cooling_pct']:.2f} %")
                st.metric("Fan level", fan_text(result["fan_level"]))
                st.metric("Energy action", action_text(result["energy_action"]))

        if len(results) > 1:
            table = pd.DataFrame({
                LABELS[r["controller"]]: {
                    "Cooling recommendation": f"{r['cooling_pct']:.2f} %",
                    "Fan level": fan_text(r["fan_level"]),
                    "Energy action": action_text(r["energy_action"]),
                }
                for r in results
            })
            st.markdown("**Side-by-side comparison (identical inputs)**")
            st.dataframe(table, width="stretch")

            chart = pd.DataFrame({
                "Controller": [LABELS[r["controller"]] for r in results],
                "Cooling (%)": [r["cooling_pct"] for r in results],
            }).set_index("Controller")
            st.markdown("**Cooling recommendation by controller**")
            st.bar_chart(chart, y="Cooling (%)")

            base = results[0]["cooling_pct"]
            st.markdown("**Cooling difference from Baseline (percentage points)**")
            st.dataframe(
                pd.DataFrame({
                    "Comparison": [f"{LABELS[r['controller']]} − Baseline"
                                   for r in results[1:]],
                    "Difference (percentage points)": [
                        round(r["cooling_pct"] - base, 2) for r in results[1:]
                    ],
                }),
                hide_index=True, width="stretch",
            )

        with st.expander("What do these outputs mean?", expanded=True):
            st.markdown(
                "- **Cooling recommendation (%)**: the controller's simulated "
                "cooling *demand* setting, from 0 to 100. It is not measured "
                "electricity use, not energy saved, and not a measured room "
                "temperature.\n"
                "- **Fan level**: Off, Low, Medium or High, chosen by the "
                "controller from the same conditions.\n"
                "- **Energy action**: a tariff-driven label. **Avoid Peak** is "
                "assigned for a High tariff, otherwise **Normal**. "
                "(**Save** exists in the schema but no controller produces "
                "it.) The label does not by itself show any energy saving."
            )
            for r in results:
                if r["occupancy_count"] == 0:
                    st.info(
                        "The room is unoccupied (0 people), so every "
                        "controller recommends 0 % cooling with the fan off."
                    )
                    break
            if len(results) == 1:
                r = results[0]
                st.markdown(
                    f"**{LABELS[r['controller']]}** gave "
                    f"{r['cooling_pct']:.2f} % cooling, fan "
                    f"{fan_text(r['fan_level']).lower()}, action "
                    f"{action_text(r['energy_action'])}."
                )

        # Interface-versus-direct consistency check, using the same inputs.
        with st.expander("Consistency check: interface vs direct controller call"):
            ga = saved_ga_params() if any(
                r["controller"] == "ga_fuzzy" for r in results) else None
            inputs = {k: first[k] for k in pi.INPUT_FIELDS}
            rows = []
            for r in results:
                d_cool, d_fan, d_act = direct_call(r["controller"], inputs, ga)
                same = (d_cool == r["cooling_pct"] and d_fan == r["fan_level"]
                        and d_act == r["energy_action"])
                rows.append({
                    "Controller": LABELS[r["controller"]],
                    "Interface result": f"{r['cooling_pct']:.2f} % / "
                                        f"{r['fan_level']} / {r['energy_action']}",
                    "Direct controller call": f"{d_cool:.2f} % / {d_fan} / {d_act}",
                    "Match": "✅ yes" if same else "❌ NO",
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True,
                         width="stretch")
            st.caption(
                "Both columns use the same existing controller code. This "
                "confirms the interface is wired correctly; it does not "
                "measure how good a controller is."
            )

        st.download_button(
            "Download this result as CSV",
            pi.results_to_csv(results).encode("utf-8"),
            file_name="sc01_product_v1_recommendation.csv",
            mime="text/csv",
            on_click="ignore",
        )
        st.caption(
            "The CSV holds the submitted inputs, controller, outputs and the "
            "limitation notice. Raw labels (e.g. `avoid_peak`) are kept."
        )

# --------------------------------------------------------------------------
# Evaluation results (historical, separate from the interactive result)
# --------------------------------------------------------------------------

with tab_eval:
    st.subheader("Existing evaluation: 10,000 synthetic scenarios")
    st.info(
        "These are **saved historical results** from the project's "
        "simulation experiment (10,000 generated scenarios, fixed random "
        "seed 42). They are not produced by your input above. Mean cooling "
        "is an average control-demand recommendation. It is **not** measured "
        "electricity consumption, actual energy savings, measured comfort, "
        "or real HVAC performance."
    )
    try:
        summary = read_csv("results/step7/evaluation_summary.csv")
        proxy = read_csv("results/step7/control_demand_proxy_summary.csv")
        comparison = read_csv("results/step7/three_controller_comparison.csv")
    except Exception as error:
        st.error(f"Saved evaluation files could not be read: {error}")
    else:
        st.markdown("**Mean cooling recommendation**")
        mean_table = proxy[["controller", "scenarios", "mean_cooling_command_pct"]].copy()
        mean_table["mean_cooling_command_pct"] = (
            mean_table["mean_cooling_command_pct"].map("{:.2f}".format)
        )
        st.dataframe(
            mean_table.rename(columns={
                "controller": "Controller", "scenarios": "Scenarios",
                "mean_cooling_command_pct": "Mean cooling recommendation (%)",
            }),
            hide_index=True, width="stretch",
        )
        st.bar_chart(
            proxy.set_index("controller")["mean_cooling_command_pct"]
            .rename("Mean cooling recommendation (%)")
        )

        names = {"baseline": "Baseline", "fuzzy": "Fuzzy", "ga_fuzzy": "GA-Fuzzy"}
        fan = summary[summary["metric"] == "fan_level_distribution"]
        fan_rows = {
            names[row.controller]: ast.literal_eval(row.value)
            for row in fan.itertuples()
        }
        fan_table = pd.DataFrame(fan_rows).reindex(
            ["off", "low", "medium", "high"]).fillna(0).astype(int)
        fan_table.index = [i.capitalize() for i in fan_table.index]
        st.markdown("**Fan-level distribution (number of scenarios)**")
        st.dataframe(fan_table, width="stretch")

        actions = pd.DataFrame({
            names[key]: comparison[f"{key}_energy_action"].value_counts()
            for key in names
        }).reindex(["normal", "avoid_peak", "save"]).fillna(0).astype(int)
        actions.index = [action_text(i) for i in actions.index]
        st.markdown("**Energy-action distribution (number of scenarios)**")
        st.dataframe(actions, width="stretch")
        st.caption(
            "The energy action depends only on the tariff, so it is "
            "identical for all three controllers. No scenario produced Save."
        )

        pairs = summary[summary["metric"].str.endswith("_differences")]
        diff = pairs.pivot(index="controller", columns="metric", values="value")
        diff = diff.rename(columns={
            "cooling_output_differences": "Cooling differs",
            "fan_level_differences": "Fan level differs",
            "energy_action_differences": "Energy action differs",
        })[["Cooling differs", "Fan level differs", "Energy action differs"]]
        diff.index = [
            i.replace("ga_fuzzy", "GA-Fuzzy").replace("baseline", "Baseline")
             .replace("fuzzy", "Fuzzy").replace("_vs_", " vs ")
            for i in diff.index
        ]
        st.markdown("**Scenarios where two controllers' outputs differ**")
        st.dataframe(diff.astype(int), width="stretch")

# --------------------------------------------------------------------------
# Campus benchmark (external context only)
# --------------------------------------------------------------------------

with tab_campus:
    st.subheader("Galgotias University campus energy benchmark")
    st.info(
        "**External context only.** This is institution-wide data. It was "
        "**not** an input to the controller experiment, and the controllers "
        "are **not** calibrated or validated against it. It says nothing "
        "about classroom-level or HVAC-specific consumption, and it does not "
        "show any energy saving from this project."
    )
    try:
        bench = read_csv("data/external/galgotias/campus_energy_benchmark.csv")
    except Exception as error:
        st.error(f"Benchmark file could not be read: {error}")
    else:
        shown = bench.rename(columns={
            "academic_year": "Academic year",
            "total_electricity_consumed_kwh": "Electricity consumed (kWh)",
            "renewable_capacity_kwp": "Renewable capacity (kWp)",
            "renewable_energy_generated_kwh": "Renewable generation (kWh)",
            "built_up_area_sq_ft": "Built-up area (sq ft)",
            "electricity_consumption_kwh_per_sq_ft": "Consumption (kWh per sq ft)",
            "renewable_generation_pct_of_electricity_consumption":
                "Renewable generation (% of consumption)",
        })
        st.dataframe(shown, hide_index=True, width="stretch")
        st.bar_chart(
            bench.set_index("academic_year")["total_electricity_consumed_kwh"]
            .rename("Electricity consumed (kWh)")
        )
        st.caption(
            "Source: Galgotias University, NIRF 2026 submission "
            "(https://www.galgotiasuniversity.edu.in/public/uploads/media/"
            "hPCbMYYPBCpGctNFiHjaDSfa0wPYd5Vbh3ihvSc6.pdf). Consumption per "
            "sq ft and renewable percentage are derived fields; see "
            "`data/external/galgotias/README.md`."
        )

# --------------------------------------------------------------------------
# About and limitations
# --------------------------------------------------------------------------

with tab_about:
    st.subheader("How this application works")
    st.markdown(
        "`User input` → `Input validation` → `Existing controller` → "
        "`Output processing` → `Result display`"
    )
    st.markdown(
        "- **Baseline**: fixed temperature, occupancy and humidity rules.\n"
        "- **Fuzzy**: fuzzy memberships and weighted rules produce the "
        "cooling recommendation.\n"
        "- **GA-optimised Fuzzy**: the same fuzzy controller using "
        "parameters saved from the project's genetic-algorithm experiment "
        "(`results/step6/ga_best_params.json`). They are loaded, not "
        "re-optimised."
    )

    st.markdown("**Inputs**")
    st.table(pd.DataFrame({
        "Input": ["Temperature", "Relative humidity", "Occupancy", "Electricity tariff"],
        "Unit": ["°C", "%", "people (whole number)", "category"],
        "Valid values": ["18–45", "20–100", "0–100", "Low, Medium, High"],
    }))
    st.markdown("**Outputs**")
    st.table(pd.DataFrame({
        "Output": ["Cooling recommendation", "Fan level", "Energy action"],
        "Values": ["0–100 %", "Off, Low, Medium, High",
                   "Normal, Avoid Peak (Save is defined but never produced)"],
    }))

    st.subheader("Limitations and responsible use")
    st.markdown(
        "- The controllers and evaluation use **synthetic simulation data**, "
        "not measurements from a real building.\n"
        "- Recommendations are **not actual HVAC commands** and the tool is "
        "not connected to any building equipment or live room sensor.\n"
        "- **No real electricity savings** have been established. Mean "
        "cooling recommendation is a control-demand figure, and the "
        "energy-action label is driven by the tariff alone.\n"
        "- **No physical indoor-comfort measurements** have been made. The "
        "GA objective is a documented synthetic heuristic, not a validated "
        "comfort model.\n"
        "- Passing validation means an input is inside the allowed range, "
        "not that it is typical of a real room.\n"
        "- Intended for **educational demonstration and decision-support "
        "exploration** only."
    )
