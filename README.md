# Mountain hydroclimatic stress analysis

Code and processed data used to analyse the Hydroclimatic Stress Index (HCSI) reconstruction and its instrumental and CMIP6 comparisons.

## Reproduce the analysis

The calculations were tested with R 4.3.3. Package versions are listed in `R-packages.txt`. The attribution model uses Python; its package versions are fixed in `requirements.txt`.

```r
install.packages(c("ggplot2", "jsonlite", "zoo"))
```

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Rscript scripts/run_all.R
```

The scripts write summary tables to `results/` and figures to `figures/`.

The four edited manuscript figures are stored as vector PDFs in `figures/final/`. They are the publication versions and are not overwritten by the plotting scripts.

## Repository contents

- `data/input/proxy_components.csv`: standardized proxy components used to calculate the HCSI.
- `data/input/hcsi.csv`: final HCSI reconstruction and 95% uncertainty interval.
- `data/input/instrumental_pyrenees.csv`: annual Pyrenean precipitation, temperature and vapour-pressure deficit.
- `data/input/spei12.csv`: annual 12-month SPEI series used for the independent validation.
- `data/input/climate_drivers.csv`: annual natural and external drivers used in the attribution models.
- `data/processed/cmip6_trajectories.csv`: regional CMIP6 analogue trajectories shown in the manuscript analysis.
- `scripts/01_hcsi_decomposition.R`: fixed-weight supply and demand decomposition, instrumental comparison, uncertainty estimates and sensitivity tests.
- `scripts/02_extreme_events.R`: dry-warm and cool-wet years based on the ±1.5 standard-deviation threshold.
- `scripts/03_cmip6_baseline.R`: common-baseline sensitivity test for the reconstruction and CMIP6 analogue.
- `scripts/04_make_figures.R`: figures based on the calculated results.
- `scripts/05_attribution_models.py`: linear and gradient-boosting models for the factual and resampled-forcing experiments.
- `scripts/README_attribution.md`: inputs, model settings, counterfactual experiments and outputs for the attribution analysis.
- `scripts/run_all.R`: runs the R analyses and the Python attribution script.
- `figures/final/`: edited vector PDFs of the four manuscript figures.

## HCSI definition

The decomposition retains the weights used in the manuscript:

```text
supply = -0.291 × Z(precipitation)
demand = 0.419 × Z(Tmax)
       + 0.179 × Z(VPD JFMAM)
       + 0.111 × Z(VPD 5-year)
HCSI raw = supply + demand
```

The post-1980 analysis does not change these weights. Equal weights and weights estimated against pre-1980 SPEI are reported only as sensitivity tests.

## Attribution analysis

The attribution script was developed from `Script_ML_Python.py` by Ivan Alfaro. It uses 20-fold shuffled cross-validation to compare linear regression and gradient boosting. The counterfactual experiments replace post-1900 greenhouse-gas and aerosol values with samples from the pre-1901 values and refit the models.

This script produces the out-of-fold factual and counterfactual predictions used to evaluate the effects of greenhouse-gas and aerosol forcing.

## Data provenance

The files in `data/input/` are processed inputs from the manuscript analysis. The source publications and data products are cited in the manuscript.
