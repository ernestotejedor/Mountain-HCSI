# Attribution analysis

The attribution analysis is implemented in `05_attribution_models.py`, developed from `Script_ML_Python.py` by Ivan Alfaro.

## Inputs

The response variable is the standardized HCSI reconstruction. The predictors are the North Atlantic Oscillation, Atlantic Multidecadal Oscillation, El Niño–Southern Oscillation, total solar irradiance, well-mixed greenhouse-gas forcing, volcanic forcing and anthropogenic aerosol forcing. Input series are read from `data/input/climate_drivers.csv` and `data/input/proxy_components.csv`.

Volcanic forcing is represented by the annual value plus lagged contributions from the following three years, weighted by 0.7, 0.5 and 0.3. Aerosol values after 2019 are held at the 2019 value.

## Models and cross-validation

The script compares linear regression with gradient-boosting regression. Model performance is evaluated using 20-fold shuffled cross-validation with a fixed random seed of 42. Predictions for each year are generated only when that year belongs to the held-out fold.

The gradient-boosting model uses 100 estimators, a learning rate of 0.1, maximum tree depth of 3, subsampling of 0.8 and a maximum-feature fraction of 0.8. Python package versions are specified in `requirements.txt`.

## Counterfactual experiments

Two counterfactual experiments are evaluated from 1901 onwards:

1. Greenhouse-gas and aerosol values are independently sampled from their values during 1602–1900.
2. Greenhouse-gas values are sampled from 1602–1900 while aerosol forcing retains its observed history.

The climate modes, solar forcing and volcanic forcing retain their historical values. Models are refitted for each factual and counterfactual predictor set using the same cross-validation structure.

## Outputs

`results/attribution_predictions.csv` contains the observed HCSI and out-of-fold predictions from the linear and gradient-boosting models for the factual and counterfactual experiments.

`results/attribution_model_metrics.json` contains the mean fold-level R², mean-squared error and mean absolute error for each model and experiment.

The script generates prediction series and cross-validation statistics. It does not calculate event probabilities, confidence intervals or risk ratios.
