from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime
import pandas as pd
import os
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
