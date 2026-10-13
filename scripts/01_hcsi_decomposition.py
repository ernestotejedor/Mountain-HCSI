from pathlib import Path
import json

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "input"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

WEIGHTS = {
    "PCP_z": -0.291,
    "Temp_MXDproxy_z": 0.419,
    "Speleothem_VPD_z": 0.179,
    "Lake_VPD_thickness_z": 0.111,
}


def linear_trend(year, values):
    frame = pd.DataFrame({"year": year, "value": values}).dropna()
    slope = np.polyfit(frame["year"], frame["value"], 1)[0]
    return slope * 10


def block_bootstrap(frame, columns, pre, post, block=11, draws=20_000, seed=420):
    rng = np.random.default_rng(seed)
    means = []
    for start, end in (pre, post):
        values = frame.loc[frame["Year"].between(start, end), columns].dropna().to_numpy()
        n = len(values)
        n_blocks = int(np.ceil(n / block))
        starts = rng.integers(0, n, size=(draws, n_blocks))
        indices = ((starts[:, :, None] + np.arange(block)) % n).reshape(draws, -1)[:, :n]
        means.append(values[indices].mean(axis=1))
    change = means[1] - means[0]
    return {
        column: dict(zip(("lower", "median", "upper"), np.quantile(change[:, i], [0.025, 0.5, 0.975])))
        for i, column in enumerate(columns)
    }


def nonnegative_fit(x, y):
    best = None
    for mask in range(1, 2 ** x.shape[1]):
        selected = [i for i in range(x.shape[1]) if mask & (1 << i)]
        coefficients = np.linalg.lstsq(x[:, selected], y, rcond=None)[0]
        if np.all(coefficients >= 0):
            full = np.zeros(x.shape[1])
            full[selected] = coefficients
            error = np.sum((y - x @ full) ** 2)
            if best is None or error < best[0]:
                best = (error, full)
    return best[1]


proxy = pd.read_csv(DATA / "proxy_components.csv")
hcsi = pd.read_csv(DATA / "hcsi.csv")
proxy = proxy.merge(hcsi, on="Year", how="left")

proxy["supply"] = WEIGHTS["PCP_z"] * proxy["PCP_z"]
proxy["tmax"] = WEIGHTS["Temp_MXDproxy_z"] * proxy["Temp_MXDproxy_z"]
proxy["vpd_jfmam"] = WEIGHTS["Speleothem_VPD_z"] * proxy["Speleothem_VPD_z"]
proxy["vpd_5yr"] = WEIGHTS["Lake_VPD_thickness_z"] * proxy["Lake_VPD_thickness_z"]
proxy["demand"] = proxy[["tmax", "vpd_jfmam", "vpd_5yr"]].sum(axis=1)
proxy["hcsi_raw"] = proxy["supply"] + proxy["demand"]
proxy["hcsi_equal"] = (
    -proxy["PCP_z"]
    + proxy["Temp_MXDproxy_z"]
    + proxy["Speleothem_VPD_z"]
    + proxy["Lake_VPD_thickness_z"]
) / 4


def summarize(frame, columns, pre, post=(1980, 2022)):
    rows = []
    for column in columns:
        early = frame.loc[frame["Year"].between(*pre), column].dropna()
        late = frame.loc[frame["Year"].between(*post), column].dropna()
        rows.append(
            {
                "component": column,
                "pre_start": pre[0],
                "pre_end": pre[1],
                "post_start": post[0],
                "post_end": post[1],
                "n_pre": len(early),
                "n_post": len(late),
                "mean_pre": early.mean(),
                "mean_post": late.mean(),
                "change": late.mean() - early.mean(),
                "post_1980_trend_per_decade": linear_trend(
                    frame.loc[frame["Year"].between(*post), "Year"],
                    frame.loc[frame["Year"].between(*post), column],
                ),
            }
        )
    return pd.DataFrame(rows)


proxy_summary = summarize(
    proxy,
    ["supply", "tmax", "vpd_jfmam", "vpd_5yr", "demand", "hcsi_raw", "Composite_A"],
    (1901, 1979),
)
changes = proxy_summary.set_index("component")["change"]
denominator = abs(changes["supply"]) + abs(changes["demand"])
proxy_summary["fraction_of_absolute_supply_demand_change"] = (
    proxy_summary["change"].abs() / denominator
)

instrumental = pd.read_csv(DATA / "instrumental_pyrenees.csv")
baseline = instrumental["Year"].between(1901, 1979)
for column in ["Precip_mm", "Temp_C", "VPD_kPa"]:
    instrumental[f"z_{column}"] = (
        instrumental[column] - instrumental.loc[baseline, column].mean()
    ) / instrumental.loc[baseline, column].std(ddof=1)
instrumental["supply"] = -instrumental["z_Precip_mm"]
instrumental["demand"] = (
    instrumental["z_Temp_C"] + instrumental["z_VPD_kPa"]
) / 2
instrumental["stress_equal"] = (
    instrumental["supply"] + instrumental["demand"]
) / 2
instrumental_summary = summarize(
    instrumental, ["supply", "demand", "stress_equal"], (1901, 1979)
)
instrumental_changes = instrumental_summary.set_index("component")["change"]
instrumental_denominator = abs(instrumental_changes["supply"]) + abs(
    instrumental_changes["demand"]
)
instrumental_summary["fraction_of_absolute_supply_demand_change"] = (
    instrumental_summary["change"].abs() / instrumental_denominator
)

spei = pd.read_csv(DATA / "spei12.csv", sep=";").rename(columns={"SPEI12": "SPEI"})
validation = instrumental.merge(spei, on="Year")
validation["realized_stress"] = -validation["SPEI"]
train = validation["Year"] <= 1979
test = validation["Year"].between(1980, 2022)
x = validation[["supply", "demand"]].to_numpy()
y = validation["realized_stress"].to_numpy()
coefficients = nonnegative_fit(x[train], y[train])
prediction = x @ coefficients
validation_results = {
    "training_period": [int(validation.loc[train, "Year"].min()), 1979],
    "test_period": [1980, 2022],
    "coefficient_supply": float(coefficients[0]),
    "coefficient_demand": float(coefficients[1]),
    "training_correlation": float(np.corrcoef(prediction[train], y[train])[0, 1]),
    "test_correlation": float(np.corrcoef(prediction[test], y[test])[0, 1]),
    "test_rmse": float(np.sqrt(np.mean((prediction[test] - y[test]) ** 2))),
}

proxy_x = np.column_stack(
    [
        -proxy["PCP_z"],
        proxy["Temp_MXDproxy_z"],
        proxy["Speleothem_VPD_z"],
        proxy["Lake_VPD_thickness_z"],
    ]
)
proxy_spei = proxy.merge(spei, on="Year")
proxy_x = np.column_stack(
    [
        -proxy_spei["PCP_z"],
        proxy_spei["Temp_MXDproxy_z"],
        proxy_spei["Speleothem_VPD_z"],
        proxy_spei["Lake_VPD_thickness_z"],
    ]
)
early = proxy_spei["Year"] <= 1979
late = proxy_spei["Year"].between(1980, 2022)
process_weights = nonnegative_fit(proxy_x[early], -proxy_spei.loc[early, "SPEI"].to_numpy())
process_index = proxy_x @ process_weights

sensitivity = []
for method, frame, values, early_mask, late_mask in [
    ("published fixed weights", proxy, proxy["hcsi_raw"], proxy["Year"].between(1901, 1979), proxy["Year"].between(1980, 2022)),
    ("equal weights", proxy, proxy["hcsi_equal"], proxy["Year"].between(1901, 1979), proxy["Year"].between(1980, 2022)),
    ("pre-1980 SPEI fit", proxy_spei, pd.Series(process_index, index=proxy_spei.index), early, late),
]:
    sensitivity.append(
        {
            "method": method,
            "mean_pre": values[early_mask].mean(),
            "mean_post": values[late_mask].mean(),
            "change": values[late_mask].mean() - values[early_mask].mean(),
            "post_1980_trend_per_decade": linear_trend(frame.loc[late_mask, "Year"], values[late_mask]),
        }
    )

proxy.to_csv(RESULTS / "hcsi_annual_decomposition.csv", index=False)
proxy_summary.to_csv(RESULTS / "hcsi_decomposition_summary.csv", index=False)
instrumental.to_csv(RESULTS / "instrumental_annual_decomposition.csv", index=False)
instrumental_summary.to_csv(RESULTS / "instrumental_decomposition_summary.csv", index=False)
pd.DataFrame(sensitivity).to_csv(RESULTS / "sensitivity_summary.csv", index=False)

uncertainty = {
    "proxy_change_1901_1979_to_1980_2022": block_bootstrap(
        proxy, ["supply", "demand", "hcsi_raw"], (1901, 1979), (1980, 2022)
    ),
    "instrumental_change_1901_1979_to_1980_2022": block_bootstrap(
        instrumental, ["supply", "demand", "stress_equal"], (1901, 1979), (1980, 2022)
    ),
    "spei_validation": validation_results,
    "pre_1980_spei_proxy_weights": process_weights.tolist(),
}
with open(RESULTS / "uncertainty_and_validation.json", "w", encoding="utf-8") as handle:
    json.dump(uncertainty, handle, indent=2)
