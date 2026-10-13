from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
hcsi = pd.read_csv(ROOT / "data" / "input" / "hcsi.csv")

events = hcsi.loc[hcsi["Composite_A"].abs() >= 1.5, ["Year", "Composite_A"]].copy()
events["event"] = events["Composite_A"].map(
    lambda value: "dry-warm" if value >= 1.5 else "cool-wet"
)
events.to_csv(ROOT / "results" / "hcsi_extreme_years.csv", index=False)

summary = (
    events.assign(period=events["Year"].map(lambda year: "1980-2022" if year >= 1980 else "1602-1979"))
    .groupby(["period", "event"])
    .size()
    .rename("n_years")
    .reset_index()
)
summary.to_csv(ROOT / "results" / "hcsi_extreme_summary.csv", index=False)
