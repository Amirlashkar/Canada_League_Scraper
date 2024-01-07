from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime
import time
import pandas as pd
import os, ast, re
from copy import deepcopy
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)

inventory_path = os.path.join(os.getcwd(), "data", "inventory.csv")
if not os.path.exists(inventory_path):
    df = pd.DataFrame(columns=["Home", "Visitor", "Date"])
    df.to_csv(inventory_path)


# scraper-specific functions
# function to check if an element exists
def check_exists(driver, by: str, target: str):
    try:
        if by == "XPATH":
            driver.find_element(By.XPATH, target)
        elif by == "ID":
            driver.find_element(By.ID, target)
        elif by == "CLASS_NAME":
            driver.find_element(By.CLASS_NAME, target)
        elif by == "LINK_TEXT":
            driver.find_element(By.LINK_TEXT, target)
        elif by == "TAG_NAME":
            driver.find_element(By.TAG_NAME, target)
    except NoSuchElementException:
        return False
    except StaleElementReferenceException:
        return False
    return True


# this function causes driver to wait in a loop till an element exists
def wait_till_located(driver, by: str, target: str, timestamp: int):
    while check_exists(driver, by, target) == False:
        print("Loading page...")
        time.sleep(timestamp)


# data management functions
def main_sheet(df_list: list, sheet_name: str) -> None:
    q = 1
    ls = []
    for i, df in enumerate(df_list):
        if type(df) == pd.DataFrame:
            quarter_row = pd.DataFrame(
                [[f"Quarter {q}" for _ in range(6)]], columns=df.columns
            )
            quarter_row["Home"] = [df_list[i - 1]["Home"]]
            quarter_row["Visitor"] = [df_list[i - 1]["Visitor"]]
            df = pd.concat([quarter_row, df], ignore_index=True)
            ls.append(df)
            q += 1

    df = pd.concat(ls, ignore_index=True)
    data_path = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    df.to_csv(os.path.join(data_path, sheet_name))


def inventory_sheet(home_team, visitor_team, date):
    data = {
        "Home": [home_team],
        "Visitor": [visitor_team],
        "Date": [date],
    }
    inventory_df = pd.read_csv(inventory_path)
    adding_df = pd.DataFrame(data)
    df = pd.concat([inventory_df, adding_df], ignore_index=True)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df.to_csv(inventory_path)


def check_inventory(home_team, visitor_team, date) -> bool:
    df = pd.read_csv(inventory_path)
    expression = df[
        (df["Home"] == home_team)
        & (df["Visitor"] == visitor_team)
        & (df["Date"] == date)
    ]

    # retrun true if there is no such data
    return len(expression) == 0


def finder(follow_up_team, start_date, end_date):
    inventory_df = pd.read_csv(inventory_path)
    inventory_df["Date"] = pd.to_datetime(inventory_df["Date"])
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    filtered_df = inventory_df.loc[
        (
            inventory_df["Home"] == follow_up_team
            or inventory_df["Visitor"] == follow_up_team
        )
        and inventory_df["Date"] > start_date_obj
        and inventory_df["Date"] <= end_date_obj
    ]

    if filtered_df.empty:
        return "empty"
    else:
        return filtered_df


def zipper(user_path, zip_name, result_df):
    saving_path = os.path.join(user_path, zip_name)
    with ZipFile(saving_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
        for index, row in result_df.iterrows():
            filename = (
                row["Home"]
                + "_"
                + row["Visitor"]
                + "_"
                + row["Date"].strftime("%Y-%m-%d")
                + ".csv"
            )
            file_path = os.path.join(os.getcwd(), "data", filename)
            zf.write(file_path, arcname=filename)
    return saving_path


def make_swap_uppernames(ls):
    formatted_players = []
    for player in ls:
        name_parts = player.split(" ")
        first_name = " ".join(name_parts[:-1])
        last_name = name_parts[-1]
        formatted_name = last_name.upper() + "," + first_name.upper()
        formatted_name = formatted_name.replace(".", "")
        formatted_players.append(formatted_name)

    return formatted_players


def players_list_and_starters(df:pd.DataFrame, quarter_index:int, HorV:str):
    p_dict = ast.literal_eval(df.iloc[quarter_index][HorV])
    p_list = p_dict["starters"].copy()
    p_list.extend(p_dict["reserves"])
    p_list.remove("Team")
    
    sts = p_dict["starters"].copy()

    p_list = make_swap_uppernames(p_list)
    sts = make_swap_uppernames(sts)

    return p_list, sts


def final_table_maker(data, HorV):

    player_event_df = data.copy()
    
    event_list = ['made layup','missed layup','Assist','Turnover','defensive rebound','enters the game'
                  ,'goes to the bench','missed 3-pt. jump shot','Foul','Steal','made free throw',
                  'missed free throw','made jump shot','made 3-pt. jump shot','missed jump shot','offensive rebound']
    
    pattern = "([A-Z]+\W*[A-Z]+,[A-Z]+\W*[A-Z]+)"
    player_event_df["H-event"] = player_event_df["H-event"].fillna("No Event")
    player_event_df["V-event"] = player_event_df["V-event"].fillna("No Event")
    for index, row in player_event_df.iterrows():
        for side in ["H", "V"]:
            player = re.search(pattern, row[f"{side}-event"])
            if player:
                player = player[0].strip()
                player_event_df.loc[index, f"{side}_player"] = player
            
            for event in event_list:
                if event in row[f"{side}-event"]:
                    player_event_df.loc[index, f"{side}_exactevent"] = event

    player_event_df[f"{HorV[0]}_player"] = player_event_df[f"{HorV[0]}_player"].fillna("No Player")
    player_event_df[f"{HorV[0]}_player"] = player_event_df[f"{HorV[0]}_player"].fillna("No Player")
    player_event_df[f"{HorV[0]}_exactevent"] = player_event_df[f"{HorV[0]}_exactevent"].fillna("No Event")
    player_event_df[f"{HorV[0]}_exactevent"] = player_event_df[f"{HorV[0]}_exactevent"].fillna("No Event")

    pass
