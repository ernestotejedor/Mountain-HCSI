#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grep("^--file=", args)])
root <- normalizePath(file.path(dirname(script_arg), ".."))
hcsi <- read.csv(file.path(root, "data", "input", "hcsi.csv"))
events <- hcsi[abs(hcsi$Composite_A) >= 1.5, c("Year", "Composite_A")]
events$event <- ifelse(events$Composite_A >= 1.5, "dry-warm", "cool-wet")
write.csv(events, file.path(root, "results", "hcsi_extreme_years.csv"), row.names = FALSE)
events$period <- ifelse(events$Year >= 1980, "1980-2022", "1602-1979")
summary <- aggregate(Year ~ period + event, events, length)
names(summary)[3] <- "n_years"
write.csv(summary, file.path(root, "results", "hcsi_extreme_summary.csv"), row.names = FALSE)
