# Here we define functions which are needed for making time, events, effectiveness, lineup
# and final table drived from scraped data.

# load libraries
import numpy as np
import pandas as pd
import ast

pd.set_option("display.max_colwidth", None)
import ast, asyncio, difflib, os, re, sys
from typing import Coroutine, List, Tuple
from copy import deepcopy
from datetime import datetime

addition_path = os.path.join(os.getcwd(), "scraper")
sys.path.append(addition_path)
from constants import *


def format_names(ls: List[str]) -> List[str]:
    """
    gets player names ls and capitalize its names then swap first and lastname
    as needed to be with respect to scraped table.

    ls: list of players full name
    """

    formatted_players = []
    for player in ls:
        name_parts = player.split(" ")
        # first name consist of all words except last word considering last name has only one word
        first_name = " ".join(name_parts[:-1])
        # last word is last name
        last_name = name_parts[-1]

        # swaping names and converting their letters to uppercase
        formatted_name = last_name.upper() + "," + first_name.upper()
        # removing any dot character if exists
        formatted_name = formatted_name.replace(".", "")
        formatted_players.append(formatted_name)

    return formatted_players


def list_players(df: pd.DataFrame, quarter_index: int, HorV: str) -> Tuple[List[str], List[str]]:
    """
    extract starter lineup from scraped table and implement some functions on it.

    df: scraped table for a match
    quarter_index: row index of an specific quarter which we are extracting lineup from it
    HorV: either you are inspecting Home or Visitor team players
    """

    # reading dictionary of players name from string on quarter row
    p_dict = df.iloc[quarter_index][HorV]
    if isinstance(p_dict, str):
        p_dict = ast.literal_eval(p_dict)

    p_list = p_dict["starters"].copy()
    # adding reserve players to players list and removing 'Team' if on players list
    p_list.extend(p_dict["reserves"])
    if "Team" in p_list:
        p_list.remove("Team")

    sts = p_dict["starters"].copy()

    p_list = format_names(p_list)
    sts = format_names(sts)

    return p_list, sts


def hollinger_score_(events_row: pd.Series, minutes: float) -> float:
    """
    Calculates Player Efficiency Rating based on Hollinger Score

    events_row: row of event table related to specific player;
    minutes: time that player spend on field by minutes;
    """
    # Calculate Field Goals Made (FGM)
    fgm = (
        events_row['made layup'] +
        events_row['made jump shot'] +
        events_row['made 3-pt. jump shot']
    )

    # Calculate Field Goals Missed (FG_Missed)
    fg_missed = (
        events_row['missed layup'] +
        events_row['missed jump shot'] +
        events_row['missed 3-pt. jump shot']
    )

    hollinger_score = (
        fgm * 85.910 +
        events_row['Steal'] * 53.897 +
        events_row['made 3-pt. jump shot'] * 51.757 +
        events_row['made free throw'] * 46.845 +
        events_row['Block'] * 39.190 +
        events_row['offensive rebound'] * 39.190 +
        events_row['Assist'] * 34.677 +
        events_row['defensive rebound'] * 14.707 +
        events_row['Foul'] * 17.174 +
        events_row['missed free throw'] * 20.091 +
        fg_missed * 39.190 +
        events_row['Turnover'] * 53.897
    ) / minutes

    return float(hollinger_score.iloc[0])


def shots_acc_(events_row: pd.Series):
    """
    Calculates how accurate player shots was

    events_row: row of event table related to specific player;
    """

    # Calculate total shots made
    shots_made = (events_row['made layup'] +
                 events_row['made jump shot'] +
                 events_row['made 3-pt. jump shot'])

    # Calculate total shots attempted
    total_shots = (shots_made +
                  events_row['missed layup'] +
                  events_row['missed jump shot'] +
                  events_row['missed 3-pt. jump shot'])

    # Calculate shooting percentage
    if total_shots > 0:
        shooting_percentage = (shots_made / total_shots) * 100
    else:
        shooting_percentage = 0

    return round(shooting_percentage, 2)


def cal_eff(offense: int, defense: int, time: float) -> float:
    """
    calculates efficiency based on inputs.
    offense: number of offensive acts
    defense: number of defensive acts
    time: in-game time for a player that we are calculating his effectiveness
    """

    if time != 0:
        eff = ((offense - defense) * 60) / time
    else:
        eff = 0

    return float(eff)


def changed_cal_eff(pos_contrib: float, neg_contrib: float, time: float) -> float:
    """
    calculates efficiency based on inputs.
    pos_contrib: points scored added to events count which are positive
    neg_contrib: points conceded added to events count which are negitive
    time: df containing time for each players or lineups
    """

    if time != 0:
        eff = ((pos_contrib - neg_contrib) / time) * 100
    else:
        eff = 0

    return float(eff)


def cal_rtg(points: int, possession: int) -> float:
    """
    calculates rating based on inputs.

    points: may be PtsScored or PtsConceded
    offense: number of offensive acts
    defense: number of defensive acts
    time: in-game time for a player that we are calculating his effectiveness
    """
    try:
        rtg = (points / possession) * 100
    except ZeroDivisionError:
        rtg = 0
    
    return rtg


def convert_min(minutes: float) -> str:
    """
    Converts float minutes to an string represented like 11Hrs, 11Min, 11s

    minutes: float shape of time in minute
    """

    hours = int(minutes / 60)
    mins = int(minutes % 60)
    seconds = int((minutes - int(minutes)) * 60)
    show_str = f"{str(hours).zfill(2)}:{str(mins).zfill(2)}:{str(seconds).zfill(2)}"

    return show_str


def data_showoff(data: np.ndarray) -> List[float | str | int]:
    """
    takes a sequence of data and converts its floats in shape of
    two digits after floating-point.

    data: sequence of data with or without other types of variables
    than float
    """

    _data = []
    for elem in data:
        ls = []
        for e in elem:
            try:
                e = float(e)
                if abs(e - int(e)) == 0:
                    e = int(e)

            except:
                pass

            if isinstance(e, float):
                ls.append("{:.2f}".format(e))
            else:
                ls.append(e)

        _data.append(ls)

    return _data


def provide_data(home: str, visitor: str, date: str) -> pd.DataFrame:
    """
    returns scraped table by specific home and visitor team on a particular date of match

    home: home team name
    visitor: visitor team name
    date: date of match
    """

    data_path = os.path.join(os.getcwd(), "data")
    filename = f"{home}_{visitor}_{date}.csv"
    file_path = os.path.join(data_path, filename)
    raw_data = pd.read_csv(file_path)

    return raw_data


def initial_edit(df: pd.DataFrame, HorV: str) -> pd.DataFrame:
    """
    this makes 4 other column within raw table which are mentioning 
    player infered and exact event occured for both side.

    df: raw table
    HorV: team side
    """

    # look up pattern to find player name
    pattern = r"([A-Z]+\W*[A-Z]+,[A-Z]+\W*[A-Z]+)"

    # players list of both sides that is needed in following
    side_plist, _ = list_players(df, 0, HorV)
    op_plist, _ = list_players(df, 0, "Home" if HorV[0] == "V" else "Visitor")

    # filling nan values on two column to not face error on main_loop
    df[f"H-event"] = df[f"H-event"].fillna("No Event")
    df[f"V-event"] = df[f"V-event"].fillna("No Event")
    for index, row in df.iterrows():
        for side in ["H", "V"]:
            compare_list = side_plist.copy() if HorV[0] == side else op_plist.copy()
            player = re.search(pattern, row[f"{side}-event"])
            if player:
                player = player[0].strip()
                if player not in compare_list:
                    # some names are entered invalid or incomplete, then will search for most similar at players list
                    # found similar is going to be exchanged with player cell on dataframe
                    found = difflib.get_close_matches(
                        player, compare_list, n=1, cutoff=0.0
                    )[0]
                    if found:
                        df.loc[index, f"{side}_player"] = found
                    else:
                        print(f"{player} not found !!!")
                else:
                    df.loc[index, f"{side}_player"] = player
            else:
                df.loc[index, f"{side}_player"] = "No Player"

            for event in event_list:
                if event in row[f"{side}-event"]:
                    df.loc[index, f"{side}_exactevent"] = event
                    break
                else:
                    df.loc[index, f"{side}_exactevent"] = "No Event"

    return df


async def create_eff_df(cusMin_df: pd.DataFrame, eff_columns: List[Tuple], custom_minute: float=1) -> pd.DataFrame:
    """
    creating effectiveness table from event dataframe separated by custom chunks of time ;

    cusMin_df: dataframe with custom time chunk size 
    eff_columns: list of dynamic strings representing effectiveness dataframe columns each as tuple
    custom_minute: size of time chunks
    """

    await asyncio.sleep(0)

    # creating effectiveness dataframe like a MultiIndex dataframe by usage of eff_columns
    eff_df = pd.DataFrame({key: [] for key in [("player", "player")] + eff_columns})
    eff_df.columns = pd.MultiIndex.from_tuples([("player", "player")] + eff_columns)

    for _, row in cusMin_df.iterrows():
        data = {("player", "player"): [row["player", "player", "player"]]}
        for col in eff_columns:
            alter = []
            for event in pos_contrib:
                alter.append(col + (event,))

            offense = row[alter].sum()

            for event in neg_contrib:
                alter.append(col + (event,))

            defense = row[alter].sum()

            eff = cal_eff(offense, defense, custom_minute * 60)
            data[col] = [eff]

        new_df = pd.DataFrame(data)
        eff_df = pd.concat([eff_df, new_df], ignore_index=True, axis=0)

    return eff_df


def main_loop(df: pd.DataFrame, HorV: str, custom_minute: float=1) -> Tuple:
    """
    This is the main part which creates time and events tables drived from raw table

    df: raw table
    HorV: followed team side
    custom_minute: custom size of time chunks
    """

    if df.shape[0] == 4:
        raise IndexError("Dataframe is empty")

    # ------------------------------------------------------------------------------------------------------------------------------------------------------------
    # dependencies
    op_HorV = "Home" if HorV == "Visitor" else "Visitor"
    players_list, _ = list_players(df, 0, HorV)
    pts_expression = 0 if HorV[0] == "H" else 1
    ptc_expression = 0 if HorV[0] == "V" else 1

    # converting time column strings to datetime to be comparable
    df["Time"] = pd.to_datetime(df["Time"], format="%M:%S", errors="coerce")
    under5min_df = df.loc[df["Time"] < datetime.strptime("05:00", "%M:%S")]

    quarter_indices5min = list(reversed(under5min_df["Time"].nlargest(4).index))
    quarter_indices = list(df[df["Score"].str.contains("Quarter")].index)
    quarter_indices.append(len(df) - 1)

    quarter_dict = {
        "player": players_list,
        "seconds1": [],
        "pts1": [],
        "ptc1": [],
        "seconds2": [],
        "pts2": [],
        "ptc2": [],
        "seconds3": [],
        "pts3": [],
        "ptc3": [],
        "seconds4": [],
        "pts4": [],
        "ptc4": [],
    }

    v = list(quarter_dict.keys())
    v.remove("player")
    reorder_ls = ["lineup"] + v
    lineup_quarter_dict = {key: [] for key in reorder_ls}

    # Last 5 minutes statistics of quarters 2 and 4
    quarter_dict5min = {
        "player": players_list,
        "time2": [],
        "score2": [],
        "time4": [],
        "score4": [],
    }

    quarter = 1
    in_lineup = []

    not_changed_list = ["not_changed" for n in range(len(players_list))]
    event_num_dict = {k: [] for k in ["Player Name"] + event_list + ["off_poss", "def_poss"]}
    event_num_dict5min = {
        k: []
        for k in ["player"]
        + [e + "2" for e in event_list]
        + [e + "4" for e in event_list]
    }
    time_dict = {
        "player": players_list,
        "seconds": list(np.zeros(len(players_list))),
        "pts": list(np.zeros(len(players_list))),
        "ptc": list(np.zeros(len(players_list))),
        "timecache": not_changed_list.copy(),
        "ptscache": not_changed_list.copy(),
        "ptccache": not_changed_list.copy(),
        "seconds5min": list(np.zeros(len(players_list))),
        "points_conceded5min": list(np.zeros(len(players_list))),
        "timecache5min": not_changed_list.copy(),
        "scorecache5min": not_changed_list.copy(),
    }

    # each custom minutes
    each_ls = list(reversed([int(m) for m in range(1, int((10 / custom_minute) + 1))]))
    cusMin_columns = []
    eff_columns = []  # will be used for efficiency later on
    for qu in range(1, 5):
        for each in list(reversed(each_ls)):
            eff_columns.append((f"quarter{qu}", f"{custom_minute}minute{each}"))
            for event in event_list:
                cusMin_columns.append(
                    (f"quarter{qu}", f"{custom_minute}minute{each}", event)
                )

    cusMin_columns = [("player", "player", "player")] + cusMin_columns
    init_data = {}
    for c in cusMin_columns:
        if "player" in c:
            init_data[c] = players_list
        else:
            init_data[c] = list(np.zeros(len(players_list)))

    cusMin_columns = pd.MultiIndex.from_tuples(cusMin_columns)
    cusMin_df = pd.DataFrame(init_data, columns=cusMin_columns)
    minutes_ls = list(np.array(each_ls) * custom_minute) + [0]

    lineup_time_dict = {k: [] for k in list(time_dict.keys())}
    lineup_time_dict["lineup"] = lineup_time_dict.pop("player")
    lineup_event_dict = {k: [] for k in ["Lineup"] + event_list + ["off_poss", "def_poss"]}

    for ind, row in df.iterrows():
        # 5min checking needs these constants
        cur_time = deepcopy(row["Time"])
        threshold_time = datetime.strptime("05:00", "%M:%S")
        # ------------------------------------------------------------------------------------------------------------------------------------------------------------
        # calculating in-game time of each player
        # -------------------------------------------
        # each quarter end calculations
        if ind in quarter_indices:
            if ind != len(df) - 1:
                _, starters = list_players(df, ind, HorV)

            if ind != 0:
                for player in in_lineup:
                    player_ind = time_dict["player"].index(player)
                    cached_time = time_dict["timecache"][player_ind]
                    ptscache = time_dict["ptscache"][player_ind]
                    ptccache = time_dict["ptccache"][player_ind]
                    if cached_time == "not_changed":
                        enter_time = datetime.strptime("10:00", "%M:%S")
                        enter_score_index = quarter_indices[quarter - 1] + 1
                        enter_pts = int(
                            df.iloc[enter_score_index]["Score"].split("-")[
                                pts_expression
                            ]
                        )
                        enter_ptc = int(
                            df.iloc[enter_score_index]["Score"].split("-")[
                                ptc_expression
                            ]
                        )
                    else:
                        enter_time = cached_time
                        enter_pts = ptscache
                        enter_ptc = ptccache

                    seconds = enter_time - datetime.strptime("00:00", "%M:%S")
                    seconds = seconds.total_seconds()

                    time_dict["seconds"][player_ind] += seconds

                # ---------------------
                # lineup quarter calculations
                lineup_cached_pts = lineup_time_dict["ptscache"][-1]
                lineup_cached_ptc = lineup_time_dict["ptccache"][-1]
                if lineup_time_dict["timecache"][-1] == "not_changed":
                    lineup_time_dict["seconds"][-1] += 600
                    enter_score_index = quarter_indices[quarter - 1] + 1
                    enter_pts = int(
                        df.iloc[enter_score_index]["Score"].split("-")[pts_expression]
                    )
                    enter_ptc = int(
                        df.iloc[enter_score_index]["Score"].split("-")[ptc_expression]
                    )
                else:
                    cached_time = lineup_time_dict["timecache"][-1]
                    enter_time = cached_time
                    seconds = enter_time - datetime.strptime("00:00", "%M:%S")
                    seconds = seconds.total_seconds()
                    lineup_time_dict["seconds"][-1] += seconds
                    enter_pts = int(lineup_cached_pts.split("-")[pts_expression])
                    enter_ptc = int(lineup_cached_ptc.split("-")[ptc_expression])

                lineup_time_dict["seconds"][-1] += seconds
                # ---------------------

                quarter_dict["player"] = time_dict["player"]
                quarter_dict[f"seconds{quarter}"] = time_dict["seconds"]
                quarter_dict[f"pts{quarter}"] = time_dict["pts"]
                quarter_dict[f"ptc{quarter}"] = time_dict["ptc"]
                if quarter in (2, 4):
                    quarter_dict5min["player"] = time_dict["player"]
                    quarter_dict5min[f"time{quarter}"] = time_dict["seconds5min"]
                    quarter_dict5min[f"score{quarter}"] = time_dict[
                        "points_conceded5min"
                    ]

                for key in list(lineup_quarter_dict.keys()):
                    if key != "lineup":
                        if int(key[-1]) == quarter:
                            if "seconds" in key:
                                lineup_quarter_dict[f"seconds{quarter}"].extend(
                                    lineup_time_dict["seconds"]
                                )
                            elif "pts" in key:
                                lineup_quarter_dict[f"pts{quarter}"].extend(
                                    lineup_time_dict["pts"]
                                )
                            else:
                                lineup_quarter_dict[f"ptc{quarter}"].extend(
                                    lineup_time_dict["ptc"]
                                )
                        else:
                            length = len(lineup_time_dict["lineup"])
                            zero_list = list(np.zeros(length))
                            lineup_quarter_dict[key].extend(zero_list)
                    else:
                        lineup_quarter_dict[key].extend(lineup_time_dict["lineup"])

                quarter += 1
                time_dict["timecache"] = not_changed_list.copy()
                time_dict["ptscache"] = not_changed_list.copy()
                time_dict["ptccache"] = not_changed_list.copy()
                time_dict["timecache5min"] = not_changed_list.copy()
                time_dict["scorecache5min"] = not_changed_list.copy()
                time_dict["seconds"] = list(np.zeros(len(players_list)))
                time_dict["pts"] = list(np.zeros(len(players_list)))
                time_dict["ptc"] = list(np.zeros(len(players_list)))
                time_dict["seconds5min"] = list(np.zeros(len(players_list)))
                time_dict["points_conceded5min"] = list(np.zeros(len(players_list)))

                lineup_time_dict = {key: [] for key in lineup_time_dict}

            in_lineup = starters.copy()
            lineup_time_dict["lineup"].append(sorted(in_lineup.copy()))
            for key in lineup_time_dict:
                if key != "lineup":
                    if "cache" in key:
                        lineup_time_dict[key].append("not_changed")
                    else:
                        lineup_time_dict[key].append(0)

            for key in lineup_event_dict:
                if key == "lineup":
                    lineup_event_dict[key].append(sorted(in_lineup))
                else:
                    lineup_event_dict[key].append(0)
            continue

        # counting off possession of opponent team which equals to def posession of selected team
        if row[f"{op_HorV[0]}_player"] not in ("No Player", np.nan, "nan") and row[f"{op_HorV[0]}_exactevent"] not in ("No Event", np.nan, "nan") and not pd.isna(row[f"{op_HorV[0]}_player"]) and not pd.isna(row[f"{op_HorV[0]}_exactevent"]):
            exactevent = row[f"{op_HorV[0]}_exactevent"]

            ## possession counting for players
            if exactevent in pos_contrib:
                for p in in_lineup:
                    if p not in event_num_dict["Player Name"]:
                        event_num_dict["Player Name"].append(p)
                        for key in event_num_dict:
                            if key != "Player Name":
                                event_num_dict[key].append(0)

                    p_ind = event_num_dict["Player Name"].index(p)
                    event_num_dict["def_poss"][p_ind] += 1

                last_lineup = lineup_event_dict["Lineup"][-1]
                new_lineup = sorted(in_lineup.copy())

                if new_lineup != last_lineup and len(new_lineup) == 5:
                    for key in lineup_event_dict:
                        if key == "Lineup":
                            lineup_event_dict[key].append(new_lineup)
                        else:
                            lineup_event_dict[key].append(0)

                lineup_event_dict["def_poss"][-1] += 1

        # -------------------------------------------
        # iterating rows calculation
        if (
            row[f"{HorV[0]}_player"] not in ("No Player", np.nan, "nan")
            and row[f"{HorV[0]}_exactevent"] not in ("No Event", np.nan, "nan")
            and not pd.isna(row[f"{HorV[0]}_player"])
            and not pd.isna(row[f"{HorV[0]}_exactevent"])
        ):
            player_index = time_dict["player"].index(row[f"{HorV[0]}_player"])
            cached_time = time_dict["timecache"][player_index]
            ptscache = time_dict["ptscache"][player_index]
            ptccache = time_dict["ptccache"][player_index]
            if "goes to the bench" in row[f"{HorV[0]}_exactevent"]:
                in_lineup.remove(row[f"{HorV[0]}_player"])

                if cached_time == "not_changed":
                    enter_time = datetime.strptime("10:00", "%M:%S")
                    enter_score_index = quarter_indices[quarter - 1] + 1
                    enter_pts = int(
                        df.iloc[enter_score_index]["Score"].split("-")[pts_expression]
                    )
                    enter_ptc = int(
                        df.iloc[enter_score_index]["Score"].split("-")[ptc_expression]
                    )
                else:
                    enter_time = cached_time
                    enter_pts = ptscache
                    enter_ptc = ptccache

                seconds = enter_time - row["Time"]
                seconds = seconds.total_seconds()

                time_dict["seconds"][player_index] += seconds

                ## if player goes to bench in last 5min of quarters 2 an 4
                ## (considering not to exceed to to much memory and calculate them when needed)
                if cur_time < threshold_time and quarter in (2, 4):
                    cached_time5min = time_dict["timecache5min"][player_index]
                    cached_score5min = time_dict["scorecache5min"][player_index]
                    if cached_time5min == "not_changed":
                        enter_time5min = threshold_time
                        enter_score_index5min = quarter_indices5min[quarter - 1] + 1
                        enter_score5min = int(
                            df.iloc[enter_score_index5min]["Score"].split("-")[
                                ptc_expression
                            ]
                        )
                    else:
                        if cached_time5min > threshold_time:
                            enter_time5min = threshold_time
                            enter_score_index5min = quarter_indices5min[quarter - 1] + 1
                            enter_score5min = int(
                                df.iloc[enter_score_index5min]["Score"].split("-")[
                                    ptc_expression
                                ]
                            )
                        else:
                            enter_time5min = cached_time5min
                            enter_score5min = cached_score5min

                    seconds5min = enter_time5min - row["Time"]
                    seconds5min = seconds5min.total_seconds()
                    points5min = int(row["Score"].split("-")[0]) - enter_score5min
                    time_dict["seconds5min"][player_index] += seconds5min
                    time_dict["points_conceded5min"][player_index] += points5min

            elif "enters the game" in row[f"{HorV[0]}_exactevent"]:
                in_lineup.append(row[f"{HorV[0]}_player"])
                time_dict["timecache"][player_index] = row["Time"]
                time_dict["ptscache"][player_index] = int(
                    row["Score"].split("-")[pts_expression]
                )
                time_dict["ptccache"][player_index] = int(
                    row["Score"].split("-")[ptc_expression]
                )

                ## time and score cache for under 5 min assessment would be catched if the the time is below 05:00
                ## else i would not change it and it would be the initial list that i made before main loop for it
                if cur_time < threshold_time:
                    time_dict["timecache5min"][player_index] = row["Time"]
                    time_dict["scorecache5min"][player_index] = int(
                        row["Score"].split("-")[pts_expression]
                    )

            # ---------------------
            # lineup iterating rows calculation
            last_lineup = lineup_time_dict["lineup"][-1]
            if sorted(in_lineup) != sorted(last_lineup) and len(in_lineup) == 5:
                cached_time = lineup_time_dict["timecache"][-1]
                if cached_time == "not_changed":
                    enter_time = datetime.strptime("10:00", "%M:%S")
                    enter_score_index = quarter_indices[quarter - 1] + 1
                    enter_pts = int(
                        df.iloc[enter_score_index]["Score"].split("-")[pts_expression]
                    )
                    enter_ptc = int(
                        df.iloc[enter_score_index]["Score"].split("-")[ptc_expression]
                    )
                else:
                    enter_time = cached_time
                    enter_pts = int(
                        lineup_time_dict["ptscache"][-1].split("-")[pts_expression]
                    )
                    enter_ptc = int(
                        lineup_time_dict["ptccache"][-1].split("-")[ptc_expression]
                    )

                seconds = enter_time - row["Time"]
                seconds = seconds.total_seconds()

                pts_curr_score = int(row["Score"].split("-")[pts_expression])
                ptc_curr_score = int(row["Score"].split("-")[ptc_expression])
                pts = pts_curr_score - enter_pts
                ptc = ptc_curr_score - enter_ptc

                lineup_time_dict["seconds"][-1] += seconds

                lineup_time_dict["lineup"].append(sorted(in_lineup.copy()))
                lineup_time_dict["seconds"].append(0)
                lineup_time_dict["pts"].append(0)
                lineup_time_dict["ptc"].append(0)
                lineup_time_dict["timecache"].append(row["Time"])
                lineup_time_dict["ptscache"].append(row["Score"])
                lineup_time_dict["ptccache"].append(row["Score"])
            # ---------------------
            # -------------------------------------------
            # ------------------------------------------------------------------------------------------------------------------------------------------------------------
            ## filling event_num_dict for meaesuring how many times each event occured
            exactevent = row[f"{HorV[0]}_exactevent"]
            if row[f"{HorV[0]}_player"] not in event_num_dict["Player Name"]:
                event_num_dict["Player Name"].append(row[f"{HorV[0]}_player"])
                for key in event_num_dict:
                    if key != "Player Name":
                        event_num_dict[key].append(0)

            player_index = event_num_dict["Player Name"].index(row[f"{HorV[0]}_player"])
            event_num_dict[exactevent][player_index] += 1

            ## possession counting
            if exactevent in pos_contrib:
                for p in in_lineup:
                    if p not in event_num_dict["Player Name"]:
                        event_num_dict["Player Name"].append(p)
                        for key in event_num_dict:
                            if key != "Player Name":
                                event_num_dict[key].append(0)

                    p_ind = event_num_dict["Player Name"].index(p)
                    event_num_dict["off_poss"][p_ind] += 1

            if cur_time < threshold_time and quarter in (2, 4):
                if row[f"{HorV[0]}_player"] not in event_num_dict5min["player"]:
                    event_num_dict5min["player"].append(row[f"{HorV[0]}_player"])
                    for key in event_num_dict5min:
                        if key != "player":
                            event_num_dict5min[key].append(0)

                player_index = event_num_dict5min["player"].index(
                    row[f"{HorV[0]}_player"]
                )
                event_num_dict5min[row[f"{HorV[0]}_exactevent"] + str(quarter)][
                    player_index
                ] += 1

            # each custom minutes
            minute_integer = row["Time"].minute + row["Time"].second / 60
            if minute_integer >= 10:
                which_minute = 1
            else:
                for minute_index, minute in enumerate(minutes_ls):
                    if minute <= minute_integer:
                        which_minute = minute_index
                        break

            cusMin_df.loc[
                cusMin_df["player", "player", "player"] == row[f"{HorV[0]}_player"],
                (
                    f"quarter{quarter}",
                    f"{custom_minute}minute{which_minute}",
                    row[f"{HorV[0]}_exactevent"],
                ),
            ] += 1

            # ---------------------
            # lineup event calculations
            if len(lineup_event_dict["Lineup"]) == 0:
                lineup_event_dict["Lineup"].append(sorted(in_lineup))
                for key in lineup_event_dict:
                    if key != "Lineup":
                        lineup_event_dict[key].append(0)

            last_lineup = lineup_event_dict["Lineup"][-1]
            new_lineup = sorted(in_lineup.copy())

            if exactevent in pos_contrib:
                if new_lineup != last_lineup and len(new_lineup) == 5:
                    for key in lineup_event_dict:
                        if key == "Lineup":
                            lineup_event_dict[key].append(new_lineup)
                        else:
                            lineup_event_dict[key].append(0)

                lineup_event_dict[exactevent][-1] += 1
                lineup_event_dict["off_poss"][-1] += 1
            # ---------------------
            
        
        # ---------------------
        # PtsScored and PtsConceded addition per row if Score column changed somehow
        if ind not in quarter_indices:
            pts = int(row["Score"].split("-")[pts_expression])
            ptc = int(row["Score"].split("-")[ptc_expression])

            try:
                prepts = int(df.iloc[ind - 1]["Score"].split("-")[pts_expression])
                preptc = int(df.iloc[ind - 1]["Score"].split("-")[ptc_expression])
            except:
                prepts = pts
                preptc = ptc

            if pts != prepts or ptc != preptc:
                pts_cnt = pts - prepts
                ptc_cnt = ptc - preptc
                for player in in_lineup:
                    player_ind = time_dict["player"].index(player)
                    time_dict["pts"][player_ind] += pts_cnt
                    time_dict["ptc"][player_ind] += ptc_cnt

                last_lineup = lineup_time_dict["lineup"][-1]
                if sorted(in_lineup) != sorted(last_lineup) and len(in_lineup) == 5:
                    lineup_time_dict["lineup"].append(sorted(in_lineup.copy()))
                    lineup_time_dict["seconds"].append(0)
                    lineup_time_dict["pts"].append(0)
                    lineup_time_dict["ptc"].append(0)
                    lineup_time_dict["timecache"].append(row["Time"])
                    lineup_time_dict["ptscache"].append(row["Score"])
                    lineup_time_dict["ptccache"].append(row["Score"])
                
                lineup_time_dict["pts"][-1] += pts_cnt
                lineup_time_dict["ptc"][-1] += ptc_cnt
        # ---------------------
    # ------------------------------------------------------------------------------------------------------------------------------------------------------------

    time_score_df = pd.DataFrame(quarter_dict)
    time_score_df5min = pd.DataFrame(quarter_dict5min)
    lineup_time_score_df = pd.DataFrame(lineup_quarter_dict)
    events_df = pd.DataFrame(event_num_dict)
    events_df5min = pd.DataFrame(event_num_dict5min)
    lineup_event_df = pd.DataFrame(lineup_event_dict)

    time_columns = []
    time_columns_5min = []
    for i in range(1, 5):
        for sub in ["seconds", "pts", "ptc"]:
            time_columns.append((f"quarter{i}", sub))
            if sub != "pts":
                time_columns_5min.append((f"quarter{i}", sub))

    event_columns = []
    for i in [2, 4]:
        for sub in event_list:
            event_columns.append((f"quarter{i}", sub))

    time_score_df.columns = pd.MultiIndex.from_tuples(
        [("player", "player")] + time_columns
    )
    time_score_df5min.columns = pd.MultiIndex.from_tuples(
        [("player", "player")]
        + [(k, v) for k, v in time_columns_5min if k[-1] not in ("1", "3")]
    )
    lineup_time_score_df.columns = pd.MultiIndex.from_tuples(
        [("lineup", "lineup")] + time_columns
    )
    events_df5min.columns = pd.MultiIndex.from_tuples(
        [("player", "player")] + event_columns
    )

    time_sum_ls = [(f"quarter{i}", "seconds") for i in range(1, 5)]
    pts_sum_ls = [(f"quarter{i}", "pts") for i in range(1, 5)]
    ptc_sum_ls = [(f"quarter{i}", "ptc") for i in range(1, 5)]
    time_score_df[("total", "seconds")] = time_score_df[time_sum_ls].sum(axis=1)
    time_score_df[("total", "pts")] = time_score_df[pts_sum_ls].sum(axis=1)
    time_score_df[("total", "ptc")] = time_score_df[ptc_sum_ls].sum(axis=1)
    lineup_time_score_df[("total", "seconds")] = lineup_time_score_df[time_sum_ls].sum(
        axis=1
    )
    lineup_time_score_df[("total", "pts")] = lineup_time_score_df[pts_sum_ls].sum(
        axis=1
    )
    lineup_time_score_df[("total", "ptc")] = lineup_time_score_df[ptc_sum_ls].sum(
        axis=1
    )

    lineup_event_df["Lineup"] = lineup_event_df["Lineup"].loc[lineup_event_df["Lineup"] != 0].apply(tuple)
    lineup_event_df = lineup_event_df.groupby("Lineup").sum().reset_index()
    lineup_time_score_df[("lineup", "lineup")] = lineup_time_score_df[
        ("lineup", "lineup")
    ].apply(tuple)
    lineup_time_score_df = (
        lineup_time_score_df.groupby(("lineup", "lineup")).sum().reset_index()
    )

    return (
        cusMin_df,
        events_df,
        lineup_event_df,
        time_score_df,
        lineup_time_score_df,
        events_df5min,
        time_score_df5min,
        eff_columns,
    )


async def create_pfinal_df(
    df: pd.DataFrame,
    HorV: str,
    date: str,
    events_df: pd.DataFrame,
    time_score_df: pd.DataFrame,
    events_df5min: pd.DataFrame,
    time_score_df5min: pd.DataFrame,
) -> pd.DataFrame:
    """
    The function creates table of players related statistics

    df: main row-by-row match dataframe
    HorV: side of playing team in match
    date: date of the match
    event_df: players related events table of the match
    time_score_df: players related dataframe with content of playtimes and scores
    events_df5min: players related events table of the match in last 5 minutes of each quarter
    time_score_df5min: players related dataframe with content of playtimes and scores in last 5 minutes of each quarter
    """

    await asyncio.sleep(0)
    globals()["neg_contrib2"] = []
    globals()["neg_contrib4"] = []
    globals()["pos_contrib2"] = []
    globals()["pos_contrib4"] = []
    globals()["quarter2_5min_eff"] = 0
    globals()["quarter4_5min_eff"] = 0

    for q in [2, 4]:
        for n in neg_contrib:
            globals()[f"neg_contrib{q}"].append((f"quarter{q}", n))
        for p in pos_contrib:
            globals()[f"pos_contrib{q}"].append((f"quarter{q}", p))

    player_final_table = pd.DataFrame(columns=final_columns)
    for _, row in events_df.iterrows():
        showing_pts = 0
        for event, score in list(scoring_values.items()):
            showing_pts += float(row[event] * score)

        points_scored = int(
            time_score_df.loc[time_score_df[("player", "player")] == row["Player Name"]][
                ("total", "pts")
            ].to_list()[0]
        )

        points_conceded = int(
            time_score_df.loc[time_score_df[("player", "player")] == row["Player Name"]][
                ("total", "ptc")
            ].to_list()[0]
        )

        seconds = time_score_df.loc[
            time_score_df[("player", "player")] == row["Player Name"]
        ][("total", "seconds")]
        time = seconds.iloc[0]
        global_off_possession = int(row["off_poss"])
        global_def_possession = int(row["def_poss"])

        eff_pos_contrib_ = points_scored + row[eff_pos_contrib].sum(axis=0)
        eff_neg_contrib_ = points_conceded + row[eff_neg_contrib].sum(axis=0)
        global_efficiency = changed_cal_eff(eff_pos_contrib_, eff_neg_contrib_, time)

        if row["Player Name"] in events_df5min["player", "player"].tolist():
            time_row5min = time_score_df5min.loc[
                time_score_df5min["player", "player"] == row["Player Name"]
            ]
            event_row5min = events_df5min.loc[
                events_df5min["player", "player"] == row["Player Name"]
            ]
            for q in [2, 4]:
                time = time_row5min[f"quarter{q}", "seconds"].iloc[0]
                offense = float(
                    event_row5min[globals()[f"pos_contrib{q}"]].sum(axis=1).iloc[0]
                )
                defense = float(
                    event_row5min[globals()[f"neg_contrib{q}"]].sum(axis=1).iloc[0]
                )
                globals()[f"quarter{q}_5min_eff"] = cal_eff(offense, defense, time)

                if time == 0:
                    globals()[f"quarter{q}_5min_eff"] = "N/A"
        else:
            globals()["quarter2_5min_eff"] = "N/A"
            globals()["quarter4_5min_eff"] = "N/A"

        minutes = seconds / 60

        hollinger_score = hollinger_score_(row, minutes)
        shots_acc = shots_acc_(row)

        minutes = "{:.2f}".format(minutes.to_list()[0])
        opponent_df = df.loc[pd.isna(df[HorV]) == True]
        opponent = (
            opponent_df.iloc[1]["Home"]
            if HorV == "Visitor"
            else opponent_df.iloc[1]["Visitor"]
        )

        try:
            off_rtg = cal_rtg(points_scored, global_off_possession)
            def_rtg = cal_rtg(points_conceded, global_def_possession)
        except ZeroDivisionError:
            off_rtg = 0
            def_rtg = 0

        net_rtg = off_rtg - def_rtg
        off_rtg = "{:.3f}".format(off_rtg)
        def_rtg = "{:.3f}".format(def_rtg)
        net_rtg = "{:.3f}".format(net_rtg)

        new_row = {
            "Player Name": [row["Player Name"]],
            "PtsScored": [showing_pts],
            "realPtsScored": [points_scored],
            "OffRtg": [off_rtg],
            "DefRtg": [def_rtg],
            "NetRtg": [net_rtg],
            "PtsConceded": [points_conceded],
            "total off possession": [global_off_possession],
            "total def possession": [global_def_possession],
            # "global efficiency": [global_efficiency],
            "PER": [hollinger_score],
            "Shots Accuracy": [shots_acc],
            "quarter2 last 5min efficiency": [quarter2_5min_eff],
            "quarter4 last 5min efficiency": [quarter4_5min_eff],
            "minutes": minutes,
            "home/visitor": HorV,
            "date": date,
            "opponent": opponent,
        }

        new_df = pd.DataFrame(new_row)
        player_final_table = pd.concat(
            [player_final_table,
            new_df.astype(player_final_table.dtypes)], # astype method is used to ignore concat future warning
            ignore_index=True, axis=0
        )

    player_final_table = player_final_table.reindex(columns=final_columns)

    return player_final_table


async def create_lfinal_df(
    df: pd.DataFrame,
    HorV: str,
    date:str,
    lineup_time_score_df: pd.DataFrame,
    lineup_event_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    The function creates table of players related statistics

    df: main row-by-row match dataframe
    HorV: side of playing team in match
    date: date of the match
    event_df: lineups related events table of the match
    time_score_df: lineups related dataframe with content of playtimes and scores
    """

    await asyncio.sleep(0)
    lineup_final_columns = final_columns.copy()
    if "Player Name" in lineup_final_columns:
        lineup_final_columns.remove("Player Name")

    lineup_final_columns = ["Lineup"].extend(lineup_final_columns)
    lineup_final_table = pd.DataFrame(columns=lineup_final_columns)
    for index, row in lineup_event_df.iterrows():
        points_scored = int(
            lineup_time_score_df.loc[
                lineup_time_score_df["lineup", "lineup"] == tuple(row["Lineup"])
            ][("total", "pts")].to_list()[0]
        )
        points_conceded = int(
            lineup_time_score_df.loc[
                lineup_time_score_df[("lineup", "lineup")] == tuple(row["Lineup"])
            ][("total", "ptc")].to_list()[0]
        )

        seconds = lineup_time_score_df.loc[
            lineup_time_score_df[("lineup", "lineup")] == row["Lineup"]
        ][("total", "seconds")]
        time = seconds.iloc[0]
        global_off_possession = int(row["off_poss"])
        global_def_possession = int(row["def_poss"])

        eff_pos_contrib_ = points_scored + row[eff_pos_contrib].sum(axis=0)
        eff_neg_contrib_ = points_conceded + row[eff_neg_contrib].sum(axis=0)
        global_efficiency = changed_cal_eff(eff_pos_contrib_, eff_neg_contrib_, time)

        off_rtg = cal_rtg(points_scored, global_off_possession)
        def_rtg = cal_rtg(points_conceded, global_def_possession)

        net_rtg = off_rtg - def_rtg
        off_rtg = "{:.3f}".format(off_rtg)
        def_rtg = "{:.3f}".format(def_rtg)
        net_rtg = "{:.3f}".format(net_rtg)

        minutes = lineup_time_score_df["total", "seconds"].iloc[index] / 60
        minutes = "{:.2f}".format(minutes)

        opponent_df = df.loc[pd.isna(df[HorV]) == True]
        opponent = (
            opponent_df.iloc[1]["Home"]
            if HorV == "Visitor"
            else opponent_df.iloc[1]["Visitor"]
        )

        new_row = {
            "Lineup": [row["Lineup"]],
            "PtsScored": [points_scored],
            "OffRtg": off_rtg,
            "DefRtg": def_rtg,
            "NetRtg": net_rtg,
            "PtsConceded": [points_conceded],
            "total off possession": [global_off_possession],
            "total def possession": global_def_possession,
            "efficiency": [global_efficiency],
            "minutes": minutes,
            "home/visitor": HorV,
            "date":date,
            "opponent": opponent,
        }

        new_df = pd.DataFrame(new_row)
        lineup_final_table = pd.concat(
            [lineup_final_table, new_df], ignore_index=True, axis=0
        )

    lineup_final_table = lineup_final_table.reindex(columns=lineup_final_columns)

    return lineup_final_table
