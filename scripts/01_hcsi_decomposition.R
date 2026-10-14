#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(jsonlite))

args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grep("^--file=", args)])
root <- normalizePath(file.path(dirname(script_arg), ".."))
data_dir <- file.path(root, "data", "input")
results_dir <- file.path(root, "results")
dir.create(results_dir, showWarnings = FALSE, recursive = TRUE)

trend_decade <- function(year, value) {
  ok <- complete.cases(year, value)
  unname(coef(lm(value[ok] ~ year[ok]))[2]) * 10
}

summarise_periods <- function(x, columns, pre = c(1901, 1979), post = c(1980, 2022)) {
  do.call(rbind, lapply(columns, function(column) {
    early <- x[x$Year >= pre[1] & x$Year <= pre[2], column]
    late <- x[x$Year >= post[1] & x$Year <= post[2], column]
    data.frame(
      component = column, pre_start = pre[1], pre_end = pre[2],
      post_start = post[1], post_end = post[2],
      n_pre = sum(!is.na(early)), n_post = sum(!is.na(late)),
      mean_pre = mean(early, na.rm = TRUE), mean_post = mean(late, na.rm = TRUE),
      change = mean(late, na.rm = TRUE) - mean(early, na.rm = TRUE),
      post_1980_trend_per_decade = trend_decade(
        x$Year[x$Year >= post[1] & x$Year <= post[2]], late
      )
    )
  }))
}

circular_mean_draws <- function(values, block = 11L, draws = 20000L) {
  values <- as.matrix(values[complete.cases(values), , drop = FALSE])
  n <- nrow(values)
  n_blocks <- ceiling(n / block)
  out <- matrix(NA_real_, draws, ncol(values))
  for (i in seq_len(draws)) {
    starts <- sample.int(n, n_blocks, replace = TRUE)
    index <- unlist(lapply(starts, function(s) ((s - 1L + 0:(block - 1L)) %% n) + 1L))
    out[i, ] <- colMeans(values[index[seq_len(n)], , drop = FALSE])
  }
  out
}

block_change <- function(x, columns, pre, post, seed = 420L) {
  set.seed(seed)
  a <- circular_mean_draws(x[x$Year >= pre[1] & x$Year <= pre[2], columns, drop = FALSE])
  b <- circular_mean_draws(x[x$Year >= post[1] & x$Year <= post[2], columns, drop = FALSE])
  change <- b - a
  setNames(lapply(seq_along(columns), function(i) {
    q <- quantile(change[, i], c(0.025, 0.5, 0.975), na.rm = TRUE)
    list(lower = unname(q[1]), median = unname(q[2]), upper = unname(q[3]))
  }), columns)
}

nonnegative_fit <- function(x, y) {
  best_error <- Inf
  best <- rep(0, ncol(x))
  for (mask in seq_len(2^ncol(x) - 1L)) {
    selected <- which(as.logical(intToBits(mask)[seq_len(ncol(x))]))
    fit <- lm.fit(x[, selected, drop = FALSE], y)$coefficients
    if (all(is.finite(fit)) && all(fit >= 0)) {
      full <- rep(0, ncol(x)); full[selected] <- fit
      error <- sum((y - drop(x %*% full))^2)
      if (error < best_error) { best_error <- error; best <- full }
    }
  }
  best
}

proxy <- merge(
  read.csv(file.path(data_dir, "proxy_components.csv")),
  read.csv(file.path(data_dir, "hcsi.csv")), by = "Year", all.x = TRUE
)
proxy$supply <- -0.291 * proxy$PCP_z
proxy$tmax <- 0.419 * proxy$Temp_MXDproxy_z
proxy$vpd_jfmam <- 0.179 * proxy$Speleothem_VPD_z
proxy$vpd_5yr <- 0.111 * proxy$Lake_VPD_thickness_z
proxy$demand <- proxy$tmax + proxy$vpd_jfmam + proxy$vpd_5yr
proxy$hcsi_raw <- proxy$supply + proxy$demand
proxy$hcsi_equal <- (-proxy$PCP_z + proxy$Temp_MXDproxy_z +
  proxy$Speleothem_VPD_z + proxy$Lake_VPD_thickness_z) / 4

proxy_summary <- summarise_periods(proxy, c(
  "supply", "tmax", "vpd_jfmam", "vpd_5yr", "demand", "hcsi_raw", "Composite_A"
))
delta <- setNames(proxy_summary$change, proxy_summary$component)
denominator <- abs(delta["supply"]) + abs(delta["demand"])
proxy_summary$fraction_of_absolute_supply_demand_change <-
  abs(proxy_summary$change) / denominator

instrumental <- read.csv(file.path(data_dir, "instrumental_pyrenees.csv"))
baseline <- instrumental$Year >= 1901 & instrumental$Year <= 1979
for (column in c("Precip_mm", "Temp_C", "VPD_kPa")) {
  instrumental[[paste0("z_", column)]] <-
    (instrumental[[column]] - mean(instrumental[[column]][baseline], na.rm = TRUE)) /
    sd(instrumental[[column]][baseline], na.rm = TRUE)
}
instrumental$supply <- -instrumental$z_Precip_mm
instrumental$demand <- (instrumental$z_Temp_C + instrumental$z_VPD_kPa) / 2
instrumental$stress_equal <- (instrumental$supply + instrumental$demand) / 2
instrumental_summary <- summarise_periods(
  instrumental, c("supply", "demand", "stress_equal")
)
delta_i <- setNames(instrumental_summary$change, instrumental_summary$component)
denominator_i <- abs(delta_i["supply"]) + abs(delta_i["demand"])
instrumental_summary$fraction_of_absolute_supply_demand_change <-
  abs(instrumental_summary$change) / denominator_i

spei <- read.csv(
  file.path(data_dir, "spei12.csv"), sep = ";", fileEncoding = "UTF-8-BOM"
)
names(spei)[names(spei) == "SPEI12"] <- "SPEI"
validation <- merge(instrumental, spei, by = "Year")
validation$realized_stress <- -validation$SPEI
train <- validation$Year <= 1979
test <- validation$Year >= 1980 & validation$Year <= 2022
x <- as.matrix(validation[, c("supply", "demand")])
y <- validation$realized_stress
coefficients <- nonnegative_fit(x[train, , drop = FALSE], y[train])
prediction <- drop(x %*% coefficients)

proxy_spei <- merge(proxy, spei, by = "Year")
proxy_x <- cbind(
  -proxy_spei$PCP_z, proxy_spei$Temp_MXDproxy_z,
  proxy_spei$Speleothem_VPD_z, proxy_spei$Lake_VPD_thickness_z
)
early <- proxy_spei$Year <= 1979
late <- proxy_spei$Year >= 1980 & proxy_spei$Year <= 2022
process_weights <- nonnegative_fit(proxy_x[early, , drop = FALSE], -proxy_spei$SPEI[early])
process_index <- drop(proxy_x %*% process_weights)

sensitivity <- rbind(
  data.frame(method = "published fixed weights", values = I(list(proxy$hcsi_raw)),
             early = I(list(proxy$Year >= 1901 & proxy$Year <= 1979)), late = I(list(proxy$Year >= 1980))),
  data.frame(method = "equal weights", values = I(list(proxy$hcsi_equal)),
             early = I(list(proxy$Year >= 1901 & proxy$Year <= 1979)), late = I(list(proxy$Year >= 1980))),
  data.frame(method = "pre-1980 SPEI fit", values = I(list(process_index)),
             early = I(list(early)), late = I(list(late)))
)
sensitivity_out <- do.call(rbind, lapply(seq_len(nrow(sensitivity)), function(i) {
  values <- sensitivity$values[[i]]; a <- sensitivity$early[[i]]; b <- sensitivity$late[[i]]
  years <- if (i < 3) proxy$Year else proxy_spei$Year
  data.frame(method = sensitivity$method[i], mean_pre = mean(values[a], na.rm = TRUE),
             mean_post = mean(values[b], na.rm = TRUE),
             change = mean(values[b], na.rm = TRUE) - mean(values[a], na.rm = TRUE),
             post_1980_trend_per_decade = trend_decade(years[b], values[b]))
}))

write.csv(proxy, file.path(results_dir, "hcsi_annual_decomposition.csv"), row.names = FALSE)
write.csv(proxy_summary, file.path(results_dir, "hcsi_decomposition_summary.csv"), row.names = FALSE)
write.csv(instrumental, file.path(results_dir, "instrumental_annual_decomposition.csv"), row.names = FALSE)
write.csv(instrumental_summary, file.path(results_dir, "instrumental_decomposition_summary.csv"), row.names = FALSE)
write.csv(sensitivity_out, file.path(results_dir, "sensitivity_summary.csv"), row.names = FALSE)

uncertainty <- list(
  proxy_change_1901_1979_to_1980_2022 = block_change(
    proxy, c("supply", "demand", "hcsi_raw"), c(1901, 1979), c(1980, 2022)
  ),
  instrumental_change_1901_1979_to_1980_2022 = block_change(
    instrumental, c("supply", "demand", "stress_equal"), c(1901, 1979), c(1980, 2022)
  ),
  spei_validation = list(
    training_period = c(min(validation$Year[train]), 1979), test_period = c(1980, 2022),
    coefficient_supply = coefficients[1], coefficient_demand = coefficients[2],
    training_correlation = cor(prediction[train], y[train]),
    test_correlation = cor(prediction[test], y[test]),
    test_rmse = sqrt(mean((prediction[test] - y[test])^2))
  ),
  pre_1980_spei_proxy_weights = process_weights
)
write_json(uncertainty, file.path(results_dir, "uncertainty_and_validation.json"),
           pretty = TRUE, auto_unbox = TRUE)
