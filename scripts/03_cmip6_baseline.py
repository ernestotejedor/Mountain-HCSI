from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
BASELINE = (1850, 2000)
MODERN = (2000, 2022)


def first_crossing(frame, threshold, sustained=1):
    values = frame["analogue_sd"].to_numpy()
    years = frame["year"].to_numpy()
    for index in range(len(frame) - sustained + 1):
        if np.all(values[index : index + sustained] >= threshold):
            return int(years[index])
    return np.nan


hcsi = pd.read_csv(ROOT / "data" / "input" / "hcsi.csv")
baseline = hcsi.loc[hcsi["Year"].between(*BASELINE), "Composite_A"]
hcsi["hcsi_common_baseline"] = (
    hcsi["Composite_A"] - baseline.mean()
) / baseline.std(ddof=1)
benchmark = hcsi.loc[hcsi["Year"].between(*MODERN), "hcsi_common_baseline"].mean()

trajectories = pd.read_csv(ROOT / "data" / "processed" / "cmip6_trajectories.csv")
rows = []
for region, frame in trajectories.groupby("region", sort=False):
    frame = frame.sort_values("year")
    rows.append(
        {
            "region": region,
            "modern_hcsi_benchmark_sd": benchmark,
            "first_crossing": first_crossing(frame, benchmark),
            "sustained_5yr_crossing": first_crossing(frame, benchmark, 5),
        }
    )

hcsi.to_csv(RESULTS / "hcsi_common_baseline_1850_2000.csv", index=False)
pd.DataFrame(rows).to_csv(RESULTS / "cmip6_common_baseline_summary.csv", index=False)
