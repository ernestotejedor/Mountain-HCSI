"""Reproduce the historical calculation underlying the reported 15-fold value.

This calculation uses different evaluation windows in its numerator and
denominator. It is retained for provenance and must not be interpreted as a
same-window risk-ratio estimate.
"""

from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "input"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

THRESHOLD = 1.5
FIRST_YEAR = 1602
LAST_YEAR = 2022


def read_saved_predictions(filename):
    frame = pd.read_csv(DATA / filename)
    expected = LAST_YEAR - FIRST_YEAR + 1
    if len(frame) != expected:
        raise ValueError(f"{filename} has {len(frame)} rows; expected {expected}.")
    frame.insert(0, "Year", range(FIRST_YEAR, LAST_YEAR + 1))
    return frame


factual = read_saved_predictions("legacy_factual_predictions.csv")
counterfactual = read_saved_predictions("legacy_counterfactual_predictions.csv")

factual_recent = factual.loc[factual["Year"].between(1980, 2022), "gb_pred"]
counterfactual_long = counterfactual.loc[
    counterfactual["Year"].between(1900, 2022), "gb_pred"
]

factual_events = int((factual_recent > THRESHOLD).sum())
counterfactual_events = int((counterfactual_long > THRESHOLD).sum())
p_factual = factual_events / len(factual_recent)
p_counterfactual = counterfactual_events / len(counterfactual_long)
rr = p_factual / p_counterfactual

summary = {
    "status": "historical calculation; asymmetric evaluation windows",
    "threshold_rule": "HCSI > 1.5",
    "factual_window": "1980-2022",
    "factual_events": factual_events,
    "factual_years": len(factual_recent),
    "p_factual": p_factual,
    "counterfactual_window": "1900-2022",
    "counterfactual_events": counterfactual_events,
    "counterfactual_years": len(counterfactual_long),
    "p_counterfactual": p_counterfactual,
    "risk_ratio": rr,
    "rounded_risk_ratio": round(rr),
    "reported_confidence_interval_reproduced": False,
    "note": (
        "The point estimate 14.874 rounds to 15. The reported 95% interval "
        "8.2-22.4 is not reproduced by the available code or outputs."
    ),
}

with open(RESULTS / "legacy_risk_ratio.json", "w", encoding="utf-8") as handle:
    json.dump(summary, handle, indent=2)

print(json.dumps(summary, indent=2))
