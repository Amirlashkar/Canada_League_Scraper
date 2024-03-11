# neccassary lists to create tables

# used for individual score
scoring_values = {
    'made layup': 2,
    'made free throw': 1,
    'made jump shot': 2,
    'made 3-pt. jump shot': 3
}

# for events counting tables either for players or lineups
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

# needed for off possession calculation
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

# needed for def possession calculation
neg_contrib = [
    "Turnover",
    "Steal",
    "Block",
]

eff_pos_contrib = [
    "Assist",
    "defensive rebound",
    "made 3-pt. jump shot",
    "made free throw",
    "made jump shot",
    "made layup",
    "offensive rebound",
]

eff_neg_contrib = [
    "Turnover",
    "Steal",
    "Block",
    "missed 3-pt. jump shot",
    "missed free throw",
    "missed jump shot",
    "missed layup",
]

# for final tables
final_columns = [
    "Player Name",
    "PtsScored",
    "realPtsScored",
    "PtsConceded",
    "total off possession",
    "total def possession",
    "global efficiency",
    "OffRtg",
    "DefRtg",
    "NetRtg",
    "quarter2 last 5min efficiency",
    "quarter4 last 5min efficiency",
    "minutes",
    "home/visitor",
    "opponent",
    "date",
]

# what we show to user from data
# ------------------------------
show_table = [
    "Player Name",
    "minutes",
    "PtsScored",
    "global efficiency",
    "OffRtg",
    "DefRtg",
    "NetRtg",
    "quarter2 last 5min efficiency",
    "quarter4 last 5min efficiency",
]

lineup_show_table = [
    "Lineup",
    "minutes",
    "PtsScored",
    "PtsConceded",
    "efficiency",
    "OffRtg",
    "DefRtg",
    "NetRtg",
]
# ------------------------------

# dropping columns of events
events_drop = [
    "enters the game",
    "goes to the bench",
]
