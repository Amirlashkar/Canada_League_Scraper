# scoring values for different types of shots
scoring_values = {
    'made layup': 2,
    'made free throw': 1,
    'made jump shot': 2,
    'made 3-pt. jump shot': 3
}

# list of all possible events in the game
event_list = [
    "made layup",
    "missed layup",
    "Assist",
    "Turnover",
    "defensive rebound",
    "enters the game",
    "goes to the bench",
    "missed 3-pt. jump shot",
    "Foul",
    "Steal",
    "Block",
    "made free throw",
    "missed free throw",
    "made jump shot",
    "made 3-pt. jump shot",
    "missed jump shot",
    "offensive rebound",
]

# events that contribute to offensive possessions
pos_contrib = [
    "Assist",
    "defensive rebound",
    "made 3-pt. jump shot",
    "made free throw",
    "made jump shot",
    "made layup",
    "offensive rebound",
    "missed 3-pt. jump shot",
    "missed free throw",
    "missed jump shot",
    "missed layup",
]

# events that contribute to defensive possessions
neg_contrib = [
    "Turnover",
    "Steal",
    "Block",
]

# columns for the final statistics table
final_columns = [
    "Player Name",
    "PtsScored",           # Points scored by the player
    "realPtsScored",       # Actual points scored when player was on court
    "PtsConceded",         # Points conceded when player was on court
    "total off possession", # Total offensive possessions
    "total def possession", # Total defensive possessions
    "OffRtg",             # Offensive Rating
    "DefRtg",             # Defensive Rating
    "NetRtg",             # Net Rating (OffRtg - DefRtg)
    "minutes",            # Minutes played
    "home/visitor",       # Whether player was on home or visiting team
    "opponent",           # Opposing team
    "date",              # Date of the game
    "hollinger_score",   # Hollinger Game Score
    "shooting_percentage" # Overall shooting percentage
]

# columns to show in the main display table
show_table = [
    "Player Name",
    "minutes",
    "PtsScored",
    "hollinger_score",
    "shooting_percentage",
    "OffRtg",
    "DefRtg",
    "NetRtg"
]

# columns to show for lineup statistics
lineup_show_table = [
    "Lineup",
    "minutes",
    "PtsScored",
    "PtsConceded",
    "OffRtg",
    "DefRtg",
    "NetRtg",
]

# events to exclude from event calculations
events_drop = [
    "enters the game",
    "goes to the bench",
]
