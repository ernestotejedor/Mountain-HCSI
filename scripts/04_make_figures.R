#!/usr/bin/env Rscript

suppressPackageStartupMessages({library(ggplot2); library(zoo)})
args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grep("^--file=", args)])
root <- normalizePath(file.path(dirname(script_arg), ".."))
results <- file.path(root, "results"); figures <- file.path(root, "figures")
dir.create(figures, showWarnings = FALSE)

proxy <- read.csv(file.path(results, "hcsi_annual_decomposition.csv"))
instrumental <- read.csv(file.path(results, "instrumental_annual_decomposition.csv"))
proxy_long <- rbind(
  data.frame(Year = proxy$Year, component = "Supply", value = rollmean(proxy$supply, 11, fill = NA, align = "center")),
  data.frame(Year = proxy$Year, component = "Demand", value = rollmean(proxy$demand, 11, fill = NA, align = "center"))
)
instrumental_long <- rbind(
  data.frame(Year = instrumental$Year, component = "Supply", value = rollmean(instrumental$supply, 11, fill = NA, align = "center")),
  data.frame(Year = instrumental$Year, component = "Demand", value = rollmean(instrumental$demand, 11, fill = NA, align = "center"))
)
colours <- c(Supply = "#3973ac", Demand = "#c94f44")
p1 <- ggplot(proxy_long, aes(Year, value, colour = component)) + geom_hline(yintercept = 0, colour = "grey75") +
  geom_vline(xintercept = 1980, linetype = 2, colour = "grey50") + geom_line() +
  coord_cartesian(xlim = c(1901, 2022)) + scale_colour_manual(values = colours) +
  labs(x = NULL, y = "HCSI contribution", colour = NULL) + theme_classic()
p2 <- ggplot(instrumental_long, aes(Year, value, colour = component)) + geom_hline(yintercept = 0, colour = "grey75") +
  geom_vline(xintercept = 1980, linetype = 2, colour = "grey50") + geom_line() +
  coord_cartesian(xlim = c(1901, 2022)) + scale_colour_manual(values = colours) +
  labs(x = "Year", y = "Standardized component", colour = NULL) + theme_classic()
pdf(file.path(figures, "supply_demand_decomposition.pdf"), width = 7, height = 6)
print(p1); print(p2); dev.off()
png(file.path(figures, "supply_demand_decomposition.png"), width = 2100, height = 1800, res = 300)
print(p1); print(p2); dev.off()

trajectories <- read.csv(file.path(root, "data", "processed", "cmip6_trajectories.csv"))
common <- read.csv(file.path(results, "hcsi_common_baseline_1850_2000.csv"))
benchmark <- mean(common$hcsi_common_baseline[common$Year >= 2000 & common$Year <= 2022])
p3 <- ggplot(trajectories, aes(year, analogue_sd, colour = region)) + geom_line() +
  geom_hline(yintercept = benchmark, linetype = 2) + coord_cartesian(xlim = c(2014, 2100)) +
  labs(x = "Year", y = "Standard deviations from 1850-2000", colour = NULL) + theme_classic()
ggsave(file.path(figures, "cmip6_common_baseline.pdf"), p3, width = 7.2, height = 4.4)
ggsave(file.path(figures, "cmip6_common_baseline.png"), p3, width = 7.2, height = 4.4, dpi = 300)
