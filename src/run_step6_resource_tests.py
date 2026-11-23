"""Step 6 - missing-resource and recovery tests (plan rows R01-R08).

Testing tool only (needs Playwright and Google Chrome). From the repository
root:

    python src/run_step6_resource_tests.py --python /path/to/python \\
        --out docs/evidence/step6

Every phase makes its OWN temporary copy of the project, starts the real app
from that copy on port 8502, damages or removes a resource IN THE COPY ONLY,
drives the page in Chrome, and then deletes the copy. The real repository and
the application on port 8501 are never touched.

Phases (a fresh server process each, because the app caches loaded resources
for the lifetime of a server process):
  1  GA parameter file missing -> R01, R02, R03; file restored -> R04
  2  GA parameter file corrupt (invalid JSON) -> R05; restored -> R06
  3  Step 7 evaluation CSV missing -> R07
  4  Campus benchmark CSV missing -> R08
  extra observation: GA file removed AFTER it was loaded successfully
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

PORT = 8502
URL = f"http://localhost:{PORT}"
GA_REL = "results/step6/ga_best_params.json"
STEP7_REL = "results/step7/three_controller_comparison.csv"
BENCH_REL = "data/external/galgotias/campus_energy_benchmark.csv"
NORMAL = ["50.00 %", "Medium", "Normal"]

parser = argparse.ArgumentParser()
parser.add_argument("--python", required=True)
parser.add_argument("--repo", default=".")
parser.add_argument("--out", required=True)
parser.add_argument("--chrome", default="/usr/bin/google-chrome")
args = parser.parse_args()
REPO = Path(args.repo).resolve()
OUT = Path(args.out)
OUT.mkdir(parents=True, exist_ok=True)

log = []


def record(test_id, action, observed, expected, passed):
    log.append({"id": test_id, "action": action, "expected": expected,
                "observed": observed, "result": "PASS" if passed else "FAIL"})
    print(f"{test_id:6s} {'PASS' if passed else 'FAIL'}  {action}")


class Phase:
    """A temporary project copy plus a real Streamlit server running it."""

    def __init__(self, name):
        self.name = name
        self.tmp = Path(tempfile.mkdtemp(prefix=f"sc01_step6_{name}_"))
        self.copy = self.tmp / "project"
        shutil.copytree(REPO, self.copy, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", ".venv"))
        self.server = None

    def start(self):
        logfile = open(OUT / f"resource_server_{self.name}.log", "w")
        self.server = subprocess.Popen(
            [args.python, "-B", "-m", "streamlit", "run", "app/app.py",
             "--server.headless", "true", "--server.port", str(PORT),
             "--browser.gatherUsageStats", "false"],
            cwd=self.copy, stdout=logfile, stderr=subprocess.STDOUT)
        for _ in range(60):
            try:
                urllib.request.urlopen(f"{URL}/_stcore/health", timeout=2)
                return
            except Exception:
                time.sleep(1)
        raise RuntimeError("temporary app did not start")

    def stop(self):
        if self.server:
            self.server.terminate()
            self.server.wait(timeout=20)
        shutil.rmtree(self.tmp, ignore_errors=True)


def read_page(page):
    page.wait_for_timeout(1800)
    alerts = page.locator('[data-testid="stAlert"]').all_inner_texts()
    return {
        "metrics": page.locator('[data-testid="stMetricValue"]')
        .all_inner_texts(),
        # Streamlit keeps every tab's content in the page, so only keep real
        # error messages (not the info boxes of other tabs).
        "alerts": [a for a in alerts
                   if "could not" in a or "Check that" in a
                   or "No recommendation" in a],
        "traceback_shown":
            page.locator('[data-testid="stException"]').count() > 0,
    }


def choose(page, option):
    page.locator('div[data-baseweb="select"]').first.click()
    page.get_by_role("option", name=option, exact=True).click()
    page.wait_for_timeout(1200)


def submit(page, option):
    choose(page, option)
    for name in ("Generate Recommendation", "Compare Controllers"):
        button = page.get_by_role("button", name=name)
        if button.count():
            button.click()
            return read_page(page)


def open_app(browser, height=1500):
    page = browser.new_context(viewport={"width": 1400, "height": height}) \
        .new_page()
    page.goto(URL)
    page.wait_for_selector("text=Intelligent Campus Climate")
    page.wait_for_timeout(2000)
    return page


def clean_error(obs, needed, tmp_dir):
    text = " ".join(obs["alerts"])
    return (bool(obs["alerts"]) and not obs["metrics"]
            and not obs["traceback_shown"]
            and all(n in text for n in needed)
            and str(tmp_dir) not in text and "/home/" not in text
            and "/tmp/" not in text)


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=args.chrome,
                                args=["--no-sandbox"])

    # ---------------- phase 1: GA file missing, then restored ----------------
    ph = Phase("ga_missing")
    try:
        (ph.copy / GA_REL).unlink()
        ph.start()
        page = open_app(browser)
        obs = submit(page, "GA-optimised Fuzzy")
        page.screenshot(path=str(OUT / "R01-missing-ga-file.png"),
                        full_page=True)
        record("R01", "GA file missing; GA-optimised Fuzzy, NORMAL", obs,
               "clear error naming results/step6/ga_best_params.json and "
               "'Restore'; no result; no traceback; no absolute path",
               clean_error(obs, [GA_REL, "Restore"], ph.tmp))
        obs = submit(page, "Compare all three controllers")
        page.screenshot(path=str(OUT / "R02-missing-ga-compare.png"),
                        full_page=True)
        record("R02", "GA file missing; Compare all three", obs,
               "same clear error; no partial result",
               clean_error(obs, [GA_REL, "Restore"], ph.tmp))
        base = submit(page, "Baseline")
        fuzzy = submit(page, "Fuzzy")
        record("R03", "GA file missing; Baseline and Fuzzy",
               {"baseline": base, "fuzzy": fuzzy},
               "Baseline 50.00/Medium/Normal and Fuzzy 55.00/Medium/Normal",
               base["metrics"] == NORMAL and not base["traceback_shown"]
               and fuzzy["metrics"] == ["55.00 %", "Medium", "Normal"]
               and not fuzzy["traceback_shown"])
        # restore in the same temporary copy, WITHOUT restarting the server
        shutil.copy(REPO / GA_REL, ph.copy / GA_REL)
        obs = submit(page, "GA-optimised Fuzzy")
        page.screenshot(path=str(OUT / "R04-restored-ga-file.png"),
                        full_page=True)
        record("R04", "restore the GA file (no restart); GA-optimised Fuzzy",
               obs, "31.41 % / Medium / Normal; error gone",
               obs["metrics"] == ["31.41 %", "Medium", "Normal"]
               and not obs["alerts"] and not obs["traceback_shown"])
        # extra observation: remove the file again after a successful load
        (ph.copy / GA_REL).unlink()
        obs = submit(page, "GA-optimised Fuzzy")
        log.append({"id": "X01", "action": "EXTRA observation (not a plan "
                    "row): GA file removed again after it was loaded once",
                    "observed": obs,
                    "note": "the app caches the loaded GA parameters for the "
                    "life of the server process"})
        print("X01    observed (extra)", obs["metrics"], obs["alerts"])
    finally:
        ph.stop()

    # ---------------- phase 2: GA file corrupt, then restored ---------------
    ph = Phase("ga_corrupt")
    try:
        (ph.copy / GA_REL).write_text("{not json")
        ph.start()
        page = open_app(browser)
        obs = submit(page, "GA-optimised Fuzzy")
        page.screenshot(path=str(OUT / "R05-corrupt-ga-file.png"),
                        full_page=True)
        record("R05", "GA file contains invalid JSON; GA-optimised Fuzzy",
               obs, "clear error about the GA file; no result; no traceback",
               clean_error(obs, [GA_REL], ph.tmp))
        shutil.copy(REPO / GA_REL, ph.copy / GA_REL)
        obs = submit(page, "GA-optimised Fuzzy")
        record("R06", "restore valid GA file (no restart)", obs,
               "31.41 % / Medium / Normal",
               obs["metrics"] == ["31.41 %", "Medium", "Normal"]
               and not obs["alerts"])
    finally:
        ph.stop()

    # ---------------- phases 3 and 4: evaluation / benchmark CSVs -------------
    for phase_name, rel, tab, test_id, needle in (
            ("step7_missing", STEP7_REL, "Evaluation results (synthetic)",
             "R07", "could not be read"),
            ("benchmark_missing", BENCH_REL, "Campus energy benchmark",
             "R08", "could not be read")):
        ph = Phase(phase_name)
        try:
            (ph.copy / rel).unlink()
            ph.start()
            page = open_app(browser)
            page.get_by_role("tab", name=tab).click()
            tab_obs = read_page(page)
            page.screenshot(path=str(OUT / f"{test_id}-{phase_name}.png"),
                            full_page=True)
            page.get_by_role("tab", name="Recommendation").click()
            rec = submit(page, "Baseline")
            text = " ".join(tab_obs["alerts"])
            record(test_id, f"remove {rel}; open '{tab}', then "
                   "Recommendation", {"tab": tab_obs, "recommendation": rec},
                   "the tab shows an error message (no traceback); the "
                   "Recommendation tab still gives 50.00/Medium/Normal",
                   needle in text and not tab_obs["traceback_shown"]
                   and str(ph.tmp) not in text
                   and rec["metrics"] == NORMAL)
        finally:
            ph.stop()
    browser.close()

passed = sum(1 for e in log if e.get("result") == "PASS")
failed = [e["id"] for e in log if e.get("result") == "FAIL"]
summary = {"passed": passed, "failed": failed,
           "total_rows": sum(1 for e in log if "result" in e)}
(OUT / "resource_tests_log.json").write_text(
    json.dumps({"summary": summary, "rows": log}, indent=2,
               ensure_ascii=False))
print(json.dumps(summary))
sys.exit(1 if failed else 0)
