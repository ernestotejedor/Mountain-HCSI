from pathlib import Path
import runpy


SCRIPTS = Path(__file__).resolve().parent

for script in [
    "01_hcsi_decomposition.py",
    "02_extreme_events.py",
    "03_cmip6_baseline.py",
    "04_make_figures.py",
    "05_attribution_models.py",
    "06_legacy_risk_ratio.py",
]:
    print(f"Running {script}")
    runpy.run_path(SCRIPTS / script, run_name="__main__")
