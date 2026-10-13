"""Fit the factual and resampled-forcing attribution models.

Adapted from Script_ML_Python.py by Ivan Alfaro.
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "input"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

RANDOM_STATE = 42
PREDICTORS = ["NAO", "AMO_scale", "ENSO", "Solar", "GHG", "Volcanic_lag", "Aerosols"]


def cross_validated_predictions(frame, predictors, splits=20):
    x = frame[predictors]
    y = frame["target"]
    folds = KFold(n_splits=splits, shuffle=True, random_state=RANDOM_STATE)
    models = {
        "linear": LinearRegression(),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=RANDOM_STATE,
            subsample=0.8,
            max_features=0.8,
        ),
    }
    predictions = pd.DataFrame(index=frame.index)
    metrics = []

    for name, model in models.items():
        predicted = np.zeros(len(frame))
        fold_scores = []
        for fold, (train, test) in enumerate(folds.split(x), start=1):
            model.fit(x.iloc[train], y.iloc[train])
            values = model.predict(x.iloc[test])
            predicted[test] = values
            fold_scores.append(
                {
                    "fold": fold,
                    "r2": r2_score(y.iloc[test], values),
                    "mse": mean_squared_error(y.iloc[test], values),
                    "mae": mean_absolute_error(y.iloc[test], values),
                }
            )
        predictions[name] = predicted
        scores = pd.DataFrame(fold_scores)
        metrics.append(
            {
                "model": name,
                "mean_fold_r2": scores["r2"].mean(),
                "mean_fold_mse": scores["mse"].mean(),
                "mean_fold_mae": scores["mae"].mean(),
            }
        )

    return predictions, metrics


drivers = pd.read_csv(DATA / "climate_drivers.csv", sep=";")
proxy = pd.read_csv(DATA / "proxy_components.csv")
if not drivers["Year"].equals(proxy["Year"]):
    raise ValueError("Driver and proxy years must match in the same row order.")

drivers["Volcanic_lag"] = (
    drivers["Volcanic"]
    + 0.7 * drivers["Volcanic"].shift(-1)
    + 0.5 * drivers["Volcanic"].shift(-2)
    + 0.3 * drivers["Volcanic"].shift(-3)
).fillna(drivers["Volcanic"])

value_2019 = drivers.loc[drivers["Year"] == 2019, "Aerosols"].iloc[0]
drivers.loc[drivers.index[-3:], "Aerosols"] = value_2019
drivers["target"] = proxy["Composite_z_clipped"]

pre_1901 = drivers["Year"] <= 1900
rng = np.random.default_rng(RANDOM_STATE)
drivers["GHG_resampled"] = drivers["GHG"]
drivers["Aerosols_resampled"] = drivers["Aerosols"]
drivers.loc[~pre_1901, "GHG_resampled"] = rng.choice(
    drivers.loc[pre_1901, "GHG"], size=(~pre_1901).sum()
)
drivers.loc[~pre_1901, "Aerosols_resampled"] = rng.choice(
    drivers.loc[pre_1901, "Aerosols"], size=(~pre_1901).sum()
)

experiments = {
    "factual": PREDICTORS,
    "counterfactual_ghg_aerosols": [
        "NAO", "AMO_scale", "ENSO", "Solar", "GHG_resampled",
        "Volcanic_lag", "Aerosols_resampled",
    ],
    "counterfactual_ghg": [
        "NAO", "AMO_scale", "ENSO", "Solar", "GHG_resampled",
        "Volcanic_lag", "Aerosols",
    ],
}

output = drivers[["Year", "target"]].copy()
all_metrics = {}
for experiment, predictors in experiments.items():
    predictions, metrics = cross_validated_predictions(drivers, predictors)
    output[f"{experiment}_linear"] = predictions["linear"]
    output[f"{experiment}_gradient_boosting"] = predictions["gradient_boosting"]
    all_metrics[experiment] = metrics

output.to_csv(RESULTS / "attribution_predictions.csv", index=False)
with open(RESULTS / "attribution_model_metrics.json", "w", encoding="utf-8") as handle:
    json.dump(all_metrics, handle, indent=2)
