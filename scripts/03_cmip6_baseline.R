#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grep("^--file=", args)])
root <- normalizePath(file.path(dirname(script_arg), ".."))

first_crossing <- function(x, threshold, sustained = 1L) {
  for (i in seq_len(nrow(x) - sustained + 1L)) {
    if (all(x$analogue_sd[i:(i + sustained - 1L)] >= threshold)) return(x$year[i])
  }
  NA_integer_
}

hcsi <- read.csv(file.path(root, "data", "input", "hcsi.csv"))
baseline <- hcsi$Composite_A[hcsi$Year >= 1850 & hcsi$Year <= 2000]
hcsi$hcsi_common_baseline <- (hcsi$Composite_A - mean(baseline)) / sd(baseline)
benchmark <- mean(hcsi$hcsi_common_baseline[hcsi$Year >= 2000 & hcsi$Year <= 2022])

trajectories <- read.csv(file.path(root, "data", "processed", "cmip6_trajectories.csv"))
regions <- unique(trajectories$region)
summary <- do.call(rbind, lapply(regions, function(region) {
  x <- trajectories[trajectories$region == region, ]; x <- x[order(x$year), ]
  data.frame(region = region, modern_hcsi_benchmark_sd = benchmark,
             first_crossing = first_crossing(x, benchmark),
             sustained_5yr_crossing = first_crossing(x, benchmark, 5L))
}))
write.csv(hcsi, file.path(root, "results", "hcsi_common_baseline_1850_2000.csv"), row.names = FALSE)
write.csv(summary, file.path(root, "results", "cmip6_common_baseline_summary.csv"), row.names = FALSE)
