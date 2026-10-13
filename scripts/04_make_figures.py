from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
FIGURES.mkdir(exist_ok=True)

proxy = pd.read_csv(RESULTS / "hcsi_annual_decomposition.csv")
instrumental = pd.read_csv(RESULTS / "instrumental_annual_decomposition.csv")
proxy_summary = pd.read_csv(RESULTS / "hcsi_decomposition_summary.csv").set_index("component")
instrumental_summary = pd.read_csv(RESULTS / "instrumental_decomposition_summary.csv").set_index("component")

blue = "#3973ac"
red = "#c94f44"

figure, axes = plt.subplots(2, 2, figsize=(9, 6.5), constrained_layout=True)

axes[0, 0].plot(proxy["Year"], proxy["supply"].rolling(11, center=True).mean(), color=blue, label="Supply")
axes[0, 0].plot(proxy["Year"], proxy["demand"].rolling(11, center=True).mean(), color=red, label="Demand")
axes[0, 0].set(xlim=(1901, 2022), ylabel="HCSI contribution", title="Proxy components")
axes[0, 0].legend(frameon=False)

proxy_change = proxy_summary.loc[["supply", "demand"], "change"]
axes[0, 1].bar(["Supply", "Demand"], proxy_change, color=[blue, red])
axes[0, 1].set(ylabel="Post-1980 minus pre-1980 mean", title="Proxy change")

axes[1, 0].plot(instrumental["Year"], instrumental["supply"].rolling(11, center=True).mean(), color=blue, label="Supply")
axes[1, 0].plot(instrumental["Year"], instrumental["demand"].rolling(11, center=True).mean(), color=red, label="Demand")
axes[1, 0].set(xlim=(1901, 2022), ylabel="Standardized component", title="Instrumental components")
axes[1, 0].legend(frameon=False)

instrumental_change = instrumental_summary.loc[["supply", "demand"], "change"]
axes[1, 1].bar(["Supply", "Demand"], instrumental_change, color=[blue, red])
axes[1, 1].set(ylabel="Post-1980 minus pre-1980 mean", title="Instrumental change")

for axis in axes.flat:
    axis.axhline(0, color="0.75", linewidth=0.8)
    axis.axvline(1980, color="0.5", linestyle="--", linewidth=0.8) if axis in (axes[0, 0], axes[1, 0]) else None
    axis.spines[["top", "right"]].set_visible(False)

figure.savefig(FIGURES / "supply_demand_decomposition.pdf")
figure.savefig(FIGURES / "supply_demand_decomposition.png", dpi=300)
plt.close(figure)

trajectories = pd.read_csv(ROOT / "data" / "processed" / "cmip6_trajectories.csv")
common = pd.read_csv(RESULTS / "hcsi_common_baseline_1850_2000.csv")
benchmark = common.loc[common["Year"].between(2000, 2022), "hcsi_common_baseline"].mean()

figure, axis = plt.subplots(figsize=(7.2, 4.4), constrained_layout=True)
for region, frame in trajectories.groupby("region", sort=False):
    axis.plot(frame["year"], frame["analogue_sd"], label=region)
axis.axhline(benchmark, color="black", linestyle="--", linewidth=1, label="Modern HCSI reference")
axis.set(xlabel="Year", ylabel="Standard deviations from 1850–2000", xlim=(2014, 2100))
axis.spines[["top", "right"]].set_visible(False)
axis.legend(frameon=False, ncol=2)
figure.savefig(FIGURES / "cmip6_common_baseline.pdf")
figure.savefig(FIGURES / "cmip6_common_baseline.png", dpi=300)
plt.close(figure)
