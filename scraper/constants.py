# neccassary lists to create tables
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
]

# needed for def possession calculation
neg_contrib = [
    "Turnover",
    "missed 3-pt. jump shot",
    "missed free throw",
    "missed jump shot",
    "missed layup",
]

# for final tables
final_columns = [
    "Player Name",
    "PtScored",
    "ptsconceded",
    "OffRtg",
    "DefRtg",
    "NetRtg",
    "total off possession",
    "total def possession",
    "global efficiency",
    "quarter2 last 5min efficiency",
    "quarter4 last 5min efficiency",
    "minutes",
    "home/visitor",
    "opponent",
    "date",
    "game_type",
]
