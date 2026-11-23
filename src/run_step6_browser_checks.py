"""Step 6 - scripted browser checks of the running application.

Testing tool only (needs `pip install playwright` and Google Chrome); it is NOT
an application dependency. Start the app first, then, from the repository root:

    python -m streamlit run app/app.py --server.headless true --server.port 8501
    python src/run_step6_browser_checks.py http://localhost:8501 docs/evidence/step6

The script drives real Google Chrome: it types each value, presses the real
button and records what the page actually displays. It covers the plan rows
L01, N01-N09, B01-B06 and I01-I18 of docs/STEP-6.md. Each row's expected value
below was written in the plan before this script was run. Downloaded CSV files
are saved under <evidence_dir>/downloads/ for src/compare_step6_predictions.py.

This is a scripted run, not a person clicking by hand (see plan group M).
"""

import csv
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

CHROME = "/usr/bin/google-chrome"
BASE = sys.argv[1]
OUT = Path(sys.argv[2])
DOWNLOADS = OUT / "downloads"
DOWNLOADS.mkdir(parents=True, exist_ok=True)

LABELS = {"temp": "Temperature (°C)", "hum": "Relative humidity (%)",
          "occ": "Occupancy (people in room)"}
NORMAL = {"temp": "25", "hum": "55", "occ": "50", "tariff": "Medium"}
BASELINE, FUZZY, GA, ALL = ("Baseline", "Fuzzy", "GA-optimised Fuzzy",
                            "Compare all three controllers")
BUTTONS = ("Generate Recommendation", "Compare Controllers")

log = []


def record(test_id, action, observed, expected, passed, **extra):
    entry = {"id": test_id, "action": action, "expected": expected,
             "observed": observed, "result": "PASS" if passed else "FAIL"}
    entry.update(extra)
    log.append(entry)
    print(f"{test_id:4s} {entry['result']}  {action}")
    return entry


# ----------------------------------------------------------------- helpers
def read_page(page):
    page.wait_for_timeout(1800)
    metrics = page.locator('[data-testid="stMetricValue"]').all_inner_texts()
    alerts = page.locator('[data-testid="stAlert"]').all_inner_texts()
    bullets = [b for b in page.locator('[data-testid="stMain"] li')
               .all_inner_texts()
               if b.split(":")[0] in ("Temperature", "Humidity", "Occupancy",
                                      "Tariff")]
    return {
        "metrics": metrics,
        "errors": [a for a in alerts if "invalid" in a or "could not" in a],
        "field_messages": bullets,
        "download_button_shown":
            page.get_by_role("button",
                             name="Download this result as CSV").count() > 0,
        "traceback_shown":
            page.locator('[data-testid="stException"]').count() > 0,
    }


def choose_controller(page, option):
    page.locator('div[data-baseweb="select"]').first.click()
    page.get_by_role("option", name=option, exact=True).click()
    page.wait_for_timeout(1200)


def set_tariff(page, tariff):
    page.locator('div[data-baseweb="select"]').nth(1).click()
    page.get_by_role("option", name=tariff, exact=True).click()


def submit(page, controller, inputs):
    """Fill the form (defaults overridden by `inputs`), press the button."""
    values = {**NORMAL, **inputs}
    for key in ("temp", "hum", "occ"):
        page.get_by_label(LABELS[key], exact=True).fill(values[key])
    set_tariff(page, values["tariff"])
    for name in BUTTONS:
        button = page.get_by_role("button", name=name)
        if button.count():
            button.click()
            return read_page(page)
    raise RuntimeError("submit button not found")


def groups_of_three(metrics):
    return [metrics[i:i + 3] for i in range(0, len(metrics), 3)]


def fmt(cooling):
    return f"{cooling:.2f} %"


def download_csv(page, filename):
    with page.expect_download() as info:
        page.get_by_role("button", name="Download this result as CSV").click()
    download = info.value
    dest = DOWNLOADS / filename
    download.save_as(str(dest))
    with open(dest, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with open(dest, encoding="utf-8") as handle:
        header = handle.readline().strip()
    return dest, download.suggested_filename, header, rows


def shot(page, name):
    page.screenshot(path=str(OUT / name), full_page=True)


# ----------------------------------------------------------------- run
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME,
                                args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1400, "height": 1000},
                                  accept_downloads=True)
    page = context.new_page()
    page.goto(BASE)
    page.wait_for_selector("text=Intelligent Campus Climate")
    page.wait_for_timeout(2000)

    # ---- L01 -----------------------------------------------------------
    tabs = [t.strip() for t in page.get_by_role("tab").all_inner_texts()]
    warning = page.locator('[data-testid="stAlert"]').first.inner_text()
    obs = {"title_visible": page.get_by_text(
               "Intelligent Campus Climate & Energy Controller").count() > 0,
           "simulation_warning": warning, "tabs": tabs,
           "traceback_shown":
               page.locator('[data-testid="stException"]').count() > 0,
           "browser": browser.version}
    record("L01", "open the app in Chrome", obs,
           "title, 'Simulation only' warning, four tabs, no traceback",
           obs["title_visible"] and "Simulation only" in warning
           and tabs == ["Recommendation", "Evaluation results (synthetic)",
                        "Campus energy benchmark", "About & limitations"]
           and not obs["traceback_shown"])
    page.screenshot(path=str(OUT / "L01-home.png"))
    page.set_viewport_size({"width": 1400, "height": 2700})
    page.wait_for_timeout(800)

    def single(test_id, controller, inputs, expected_metrics, shot_name=None):
        choose_controller(page, controller)
        obs = submit(page, controller, inputs)
        ok = (obs["metrics"] == expected_metrics and not obs["errors"]
              and not obs["traceback_shown"])
        record(test_id, f"{controller}: {inputs or 'defaults'}", obs,
               expected_metrics, ok)
        if shot_name:
            shot(page, shot_name)
        return obs

    # ---- N01-N03 ----------------------------------------------------------
    single("N01", BASELINE, {}, ["50.00 %", "Medium", "Normal"],
           "N01-normal-baseline.png")
    single("N02", FUZZY, {}, ["55.00 %", "Medium", "Normal"],
           "N02-normal-fuzzy.png")
    single("N03", GA, {}, ["31.41 %", "Medium", "Normal"],
           "N03-normal-ga.png")

    # ---- compare helper ---------------------------------------------------
    def compare_case(test_id, inputs, csv_name, expected_fn, shot_name=None):
        choose_controller(page, ALL)
        obs = submit(page, ALL, inputs)
        groups = groups_of_three(obs["metrics"])
        ok = (len(groups) == 3 and not obs["errors"]
              and not obs["traceback_shown"] and expected_fn(groups))
        if shot_name:
            shot(page, shot_name)
        saved = download_csv(page, csv_name)
        return obs, groups, ok, saved

    # ---- N04 + N05 --------------------------------------------------------
    obs, groups, ok, (dest, suggested, header, rows) = compare_case(
        "N04", {}, "N05_NORMAL_compare.csv",
        lambda g: g == [["50.00 %", "Medium", "Normal"],
                        ["55.00 %", "Medium", "Normal"],
                        ["31.41 %", "Medium", "Normal"]],
        "N04-normal-compare.png")
    record("N04", "NORMAL, Compare all three", obs,
           "three results equal to N01-N03", ok)
    expected_header = ("controller,temperature_c,humidity_pct,occupancy_count,"
                       "tariff_level,cooling_pct,fan_level,energy_action,"
                       "notice")
    screen_cooling = [g[0] for g in groups]
    file_cooling = [fmt(float(r["cooling_pct"])) for r in rows]
    csv_obs = {"suggested_filename": suggested, "header": header,
               "controllers": [r["controller"] for r in rows],
               "cooling_in_file": file_cooling,
               "cooling_on_screen": screen_cooling,
               "notice_present": all(r["notice"].startswith("Simulated")
                                     for r in rows),
               "saved_as": dest.name}
    record("N05", "press 'Download this result as CSV' after N04", csv_obs,
           "sc01_product_v1_recommendation.csv; documented header; 3 rows "
           "equal to the screen; notice present",
           suggested == "sc01_product_v1_recommendation.csv"
           and header == expected_header
           and csv_obs["controllers"] == ["baseline", "fuzzy", "ga_fuzzy"]
           and file_cooling == screen_cooling and csv_obs["notice_present"])

    # ---- N06 --------------------------------------------------------------
    def n06(g):
        ga_cool = float(g[2][0].split()[0])
        return (g[0] == ["90.00 %", "High", "Avoid Peak"]
                and g[1] == ["90.00 %", "High", "Avoid Peak"]
                and 31.41 <= ga_cool <= 72.09
                and g[2][1:] == ["High", "Avoid Peak"])
    obs, groups, ok, saved = compare_case(
        "N06", {"temp": "38", "hum": "85", "occ": "80", "tariff": "High"},
        "N06_HOT-HUMID_compare.csv", n06, "N06-hot-humid-compare.png")
    record("N06", "HOT-HUMID 38/85/80/high, Compare all three + CSV", obs,
           "Baseline 90/High/Avoid Peak; Fuzzy 90/High/Avoid Peak; GA 31.41-72.09/"
           "High/Avoid Peak", ok)

    # ---- N07 --------------------------------------------------------------
    obs, groups, ok, saved = compare_case(
        "N07", {"temp": "30", "hum": "50", "occ": "0", "tariff": "Low"},
        "N07_EMPTY_compare.csv",
        lambda g: g == [["0.00 %", "Off", "Normal"]] * 3,
        "N07-empty-room-compare.png")
    record("N07", "EMPTY 30/50/0/low, Compare all three + CSV", obs,
           "all three 0.00 % / Off / Normal", ok)

    # ---- N08 --------------------------------------------------------------
    def n08(g):
        return (g[0] == ["10.00 %", "Low", "Normal"]
                and abs(float(g[1][0].split()[0]) - 28.33) <= 0.01
                and g[1][1:] == ["Low", "Normal"]
                and abs(float(g[2][0].split()[0]) - 15.99) <= 0.01
                and g[2][1:] == ["Low", "Normal"])
    obs, groups, ok, saved = compare_case(
        "N08", {"temp": "21", "hum": "45", "occ": "15", "tariff": "Low"},
        "N08_COOL_compare.csv", n08, "N08-cool-room-compare.png")
    record("N08", "COOL 21/45/15/low, Compare all three + CSV", obs,
           "Baseline 10/Low/Normal; Fuzzy ~28.33/Low/Normal; GA ~15.99/Low/"
           "Normal (+/-0.01)", ok)

    # ---- N09 --------------------------------------------------------------
    choose_controller(page, BASELINE)
    tariff_obs = {}
    for tariff, action in (("Low", "Normal"), ("Medium", "Normal"),
                           ("High", "Avoid Peak")):
        tariff_obs[tariff] = submit(page, BASELINE, {"tariff": tariff})["metrics"]
    record("N09", "Baseline, NORMAL with tariff Low / Medium / High",
           tariff_obs, "energy action Normal, Normal, Avoid Peak; cooling and "
           "fan unchanged",
           tariff_obs == {"Low": ["50.00 %", "Medium", "Normal"],
                          "Medium": ["50.00 %", "Medium", "Normal"],
                          "High": ["50.00 %", "Medium", "Avoid Peak"]})

    # ---- B01-B06 (Compare all three, CSV downloaded) -------------------------
    boundaries = [
        ("B01", {"temp": "18"}, [["10.00 %", "Low", "Normal"],
                                 ["55.00 %", "Medium", "Normal"],
                                 ["31.41 %", "Medium", "Normal"]]),
        ("B02", {"temp": "45"}, [["90.00 %", "Medium", "Normal"],
                                 ["90.00 %", "High", "Normal"],
                                 ["72.09 %", "High", "Normal"]]),
        ("B03", {"hum": "20"}, [["50.00 %", "Medium", "Normal"],
                                ["55.00 %", "Medium", "Normal"],
                                ["31.41 %", "Medium", "Normal"]]),
        ("B04", {"hum": "100"}, [["50.00 %", "High", "Normal"],
                                 ["72.50 %", "High", "Normal"],
                                 ["31.41 %", "High", "Normal"]]),
        ("B05", {"occ": "0"}, [["0.00 %", "Off", "Normal"]] * 3),
        ("B06", {"occ": "100"}, [["50.00 %", "Medium", "Normal"],
                                 ["90.00 %", "High", "Normal"],
                                 ["31.41 %", "Medium", "Normal"]]),
    ]
    for test_id, inputs, expected in boundaries:
        obs, groups, ok, saved = compare_case(
            test_id, inputs, f"{test_id}_compare.csv",
            lambda g, e=expected: g == e,
            "B02-boundary-temperature-45.png" if test_id == "B02" else
            "B05-boundary-occupancy-0.png" if test_id == "B05" else None)
        record(test_id, f"boundary {inputs}, Compare all three + CSV", obs,
               expected, ok)

    # ---- invalid inputs (Baseline) ---------------------------------------------
    choose_controller(page, BASELINE)

    def invalid(test_id, inputs, keywords, shot_name=None):
        obs = submit(page, BASELINE, inputs)
        messages = " | ".join(obs["field_messages"])
        ok = (bool(obs["errors"]) and not obs["metrics"]
              and not obs["download_button_shown"]
              and not obs["traceback_shown"]
              and all(k in messages for k in keywords))
        record(test_id, f"Baseline with {inputs}", obs,
               f"error mentioning {keywords}; no result, no CSV, no traceback",
               ok)
        if shot_name:
            shot(page, shot_name)
        return obs

    invalid("I01", {"temp": "46"}, ["Temperature", "18-45"],
            "I01-invalid-temperature-46.png")
    invalid("I02", {"temp": "17"}, ["Temperature", "18-45"])
    invalid("I03", {"temp": "45.01"}, ["Temperature", "18-45"])
    invalid("I04", {"temp": "17.99"}, ["Temperature", "18-45"])
    invalid("I05", {"hum": "101"}, ["Humidity", "20-100"])
    invalid("I06", {"hum": "19"}, ["Humidity", "20-100"])
    invalid("I07", {"occ": "-1"}, ["Occupancy", "0-100"])
    invalid("I08", {"occ": "101"}, ["Occupancy", "0-100"])
    invalid("I09", {"occ": "20.5"}, ["Occupancy", "whole number"])
    invalid("I10", {"temp": "abc"}, ["Temperature", "enter a number"],
            "I10-invalid-temperature-text.png")
    invalid("I11", {"occ": "many"}, ["Occupancy", "enter a number"])
    invalid("I12", {"hum": ""}, ["Humidity", "enter a value"],
            "I12-invalid-humidity-blank.png")
    invalid("I13", {"temp": ""}, ["Temperature", "enter a value"])
    invalid("I14", {"temp": "nan"}, ["Temperature", "finite"])
    invalid("I15", {"occ": "inf"}, ["Occupancy", "finite"])
    obs = invalid("I16", {"temp": "abc", "hum": "200", "occ": "-5"},
                  ["Temperature", "Humidity", "Occupancy"],
                  "I16-invalid-three-fields.png")
    log[-1]["field_message_count"] = len(obs["field_messages"])
    if len(obs["field_messages"]) != 3:
        log[-1]["result"] = "FAIL"

    # I17 / I18: stale result removed, then recovery
    valid = submit(page, BASELINE, {})
    stale = submit(page, BASELINE, {"temp": "46"})
    ok17 = (len(valid["metrics"]) == 3 and valid["download_button_shown"]
            and not stale["metrics"] and not stale["download_button_shown"]
            and bool(stale["errors"]))
    record("I17", "valid result, then invalid submit (temperature 46)",
           {"before": valid["metrics"],
            "after_metrics": stale["metrics"],
            "after_download_button": stale["download_button_shown"],
            "after_errors": stale["errors"]},
           "old result and CSV button removed; only the error shown", ok17)
    shot(page, "I17-stale-result-cleared.png")
    recovery = submit(page, BASELINE, {})
    record("I18", "correct the value and submit again", recovery,
           "error gone; 50.00 % / Medium / Normal",
           recovery["metrics"] == ["50.00 %", "Medium", "Normal"]
           and not recovery["errors"])

    # ---- other tabs (not planned rows; recorded as extra observations) ------
    extras = []
    for tab in ("Evaluation results (synthetic)", "Campus energy benchmark",
                "About & limitations"):
        page.get_by_role("tab", name=tab).click()
        page.wait_for_timeout(1500)
        extras.append({"tab": tab, "traceback_shown":
                       page.locator('[data-testid="stException"]')
                       .count() > 0})
    log.append({"id": "extra", "action": "open the other three tabs",
                "observed": extras})
    browser.close()

passed = sum(1 for e in log if e.get("result") == "PASS")
failed = [e["id"] for e in log if e.get("result") == "FAIL"]
summary = {"passed": passed, "failed": failed,
           "total_rows": sum(1 for e in log if "result" in e)}
(OUT / "browser_checks_log.json").write_text(
    json.dumps({"summary": summary, "rows": log}, indent=2,
               ensure_ascii=False))
print(json.dumps(summary))
sys.exit(1 if failed else 0)
