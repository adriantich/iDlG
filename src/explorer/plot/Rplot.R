
library(arrow)
library(ggplot2)
library(dplyr)
library(tidyr)


data_mean <- read_parquet("/home/aantich/Nextcloud/2_PROJECTES/iDlG_paper/iDlG/scan_results/Chromosome_11_10000_2500_bypos_mean.parquet")
data_regions <- read_parquet("/home/aantich/Nextcloud/2_PROJECTES/iDlG_paper/iDlG/scan_results/Chromosome_11_10000_2500_bypos_suggested_regions.parquet")
# data_mean <- read_parquet("/home/aantich/Nextcloud/2_PROJECTES/iDlG_paper/iDlG/scan_results_1pc/Chromosome_11_10000_2500_bypos_mean.parquet")
# data_regions <- read_parquet("/home/aantich/Nextcloud/2_PROJECTES/iDlG_paper/iDlG/scan_results_1pc/Chromosome_11_10000_2500_bypos_suggested_regions.parquet")


data_mean$midpoint <- (data_mean$start + data_mean$end) / 2
data_mean$position <- c(1:nrow(data_mean))

data_mean_long <- data_mean %>%
  pivot_longer(cols = -c(start, end, midpoint, position), names_to = "sample", values_to = "mean_value")

# data_regions$midpoints <- 
#     (
#         data_mean$midpoint[2:nrow(data_mean)] + data_mean$midpoint[1:(nrow(data_mean)-1)]
#     ) / 2
# data_regions$xmin <- data_mean$midpoint[1:(nrow(data_mean)-1)]
# data_regions$xmax <- data_mean$midpoint[2:nrow(data_mean)]
data_regions$xmin <- data_mean$start[1:(nrow(data_mean)-1)]
data_regions$xmax <- data_mean$end[2:nrow(data_mean)]

ggplot() +
    # geom_bar(data = data_regions, aes(x = midpoints, y = 3, fill = scores), stat = "identity", alpha = 0.8) +
    geom_rect(data = data_regions, aes(xmin = xmin, xmax = xmax, ymin = 0, ymax = .5, fill = scores), alpha = 0.8) +
    scale_fill_continuous(low = "blue", high = "orange", name = "Score", limits = c(0, 1)) +
    geom_line(data = data_mean_long, 
        aes(x = midpoint, y = mean_value+.5, group = sample, color = mean_value), linewidth = 0.1) +
    scale_colour_gradientn(colours = c("navy", "steelblue", "yellow", "indianred", "red4"), values = scales::rescale(c(0, 1, 2)),  limits = c(0, 2),  name = "Value") +
    # scale_color_discrete(guide = "none") +
    labs(title = "Mean Window Value with Suggested Regions", x = "Midpoint", y = "Mean Window Value") +
    theme_minimal() +
    theme(axis.text = element_blank())
