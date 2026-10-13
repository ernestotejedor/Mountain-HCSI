#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grep("^--file=", args)])
scripts <- dirname(normalizePath(script_arg))

for (script in c(
  "01_hcsi_decomposition.R",
  "02_extreme_events.R",
  "03_cmip6_baseline.R",
  "04_make_figures.R"
)) {
  message("Running ", script)
  status <- system2("Rscript", file.path(scripts, script))
  if (status != 0) stop(script, " failed")
}

message("Running 05_attribution_models.py (Ivan Alfaro's Python workflow)")
status <- system2("python3", file.path(scripts, "05_attribution_models.py"))
if (status != 0) stop("05_attribution_models.py failed")
