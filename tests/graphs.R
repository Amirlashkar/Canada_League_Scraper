library(hrbrthemes)
library(GGally)
library(viridis)
library(ggplot2)
library(dplyr)
library(tidyr)

# Data set is provided by R natively
colnames(eff_df) = c("player","Quarter1_1","Quarter1_2", "Quarter2_1", "Quarter2_2", "Quarter3_1", "Quarter3_2","Quarter4_1", "Quarter4_2")
data <- eff_df[-1,]

# Plot
# Plot
# Load necessary libraries
library(GGally)
library(ggplot2)
library(dplyr)

# Read the data
df <- read.csv('/path/to/your/file.csv')

# Remove the first row which is a duplicate header
df_cleaned <- eff_df[-1,]

# Convert the quarter columns to numeric
df_cleaned[2:ncol(df_cleaned)] <- sapply(df_cleaned[2:ncol(df_cleaned)], as.numeric)

# Create a parallel coordinates plot
ggparcoord(df_cleaned,
           columns = 2:ncol(df_cleaned),
           groupColumn = 1,
           order = "allClass",
           showPoints = TRUE,
           title = "Parallel Coordinate Plot for the Players Data",
           alphaLines = 0.3) +
  scale_color_viridis(discrete = TRUE) +
  theme_ipsum() +
  theme(plot.title = element_text(size = 10))

# Load necessary libraries
library(ggplot2)
library(dplyr)
library(tidyr)

# Read the data


# Remove the first row which is a duplicate header

# Convert the quarter columns to numeric
df_cleaned[2:ncol(df_cleaned)] <- sapply(df_cleaned[2:ncol(df_cleaned)], as.numeric)

# Reshape the data for plotting
# Reshape the data for plotting
df_long <- df_cleaned %>%
  gather(key = "quarter", value = "value", -player)

# Create a time series plot
ggplot(df_long, aes(x = quarter, y = value, group = player, color = player)) +
  geom_line() +
  geom_point() +
  theme_minimal() +
  labs(title = "Time Series Plot for All Players",
       x = "Quarter",
       y = "Value") +
  theme(legend.position="bottom")



remove_column = which(event_num_df5min[2,]== "enters the game")
remove_column2 = which(event_num_df5min[2,]== "goes to the bench")

cleaned_event5minutes = event_num_df5min[,-c(remove_column,remove_column2)]
quarter_2 = which(cleaned_event5minutes[1,]=="quarter2")

quarter2_event5m  = cleaned_event5minutes[-1,c(1,quarter_2)]
colnames(quarter2_event5m) = quarter2_event5m[1,]
quarter2_event5m = quarter2_event5m[-1,]

df_cleaned = quarter2_event5m
df_cleaned[2:ncol(df_cleaned)] <- sapply(df_cleaned[2:ncol(df_cleaned)], as.numeric)

# Create a parallel coordinates plot
ggparcoord(df_cleaned,
           columns = 2:ncol(df_cleaned),
           groupColumn = 1,
           order = "allClass",
           showPoints = TRUE,
           title = "Parallel Coordinate Plot for the Players Data",
           alphaLines = 0.3) +
  scale_color_viridis(discrete = TRUE) +
  theme_ipsum() +
  theme(plot.title = element_text(size = 10))+
  geom_line(size = 2)
