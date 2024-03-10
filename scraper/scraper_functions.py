import time, os
from datetime import datetime
import pandas as pd
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)


def check_content(driver:Chrome) -> bool:
    """
    checking if match template has content or overtime
    """

    # empty content checking block
    has_content = False
    try:
        driver.find_element(By.XPATH, "//a[contains(text(), '1st Qtr')]")
        has_content = True
    except NoSuchElementException:
        driver.back()
        
    # overtime checking block
    has_overtime = False
    try:
        driver.find_element(By.XPATH, "//a[contains(@data-view, 'period5')]")
        driver.back()
        has_overtime = True
    except NoSuchElementException:
        pass

    if has_content and not has_overtime:
        return True
    else:
        return False


def get_sheet_name(driver:Chrome) -> str:
    """
    providing final sheet name by template heading and date
    """

    head_info = driver.find_element(By.XPATH, "//div[@class = 'head']/h1").text.split(
        "\n"
    )

    # some matches heading are separated in different ways
    try:
        visitor_team = head_info[0].split(" at ")[0]
        home_team = head_info[0].split(" at ")[1]
    except IndexError:
        try:
            visitor_team = head_info[0].split(" vs. ")[0]
            home_team = head_info[0].split(" vs. ")[1]
        except IndexError:
            visitor_team = head_info[0].split(" vs ")[0]
            home_team = head_info[0].split(" vs ")[1]

    date_of_match = datetime.strptime(head_info[1], "%B %d, %Y").strftime("%m_%d_%Y")
    sheet_name = f"{home_team}_{visitor_team}_{date_of_match}.csv"

    return sheet_name, home_team, visitor_team, date_of_match


# defining inventory.csv path and creating it if not exists
inventory_path = os.path.join(os.getcwd(), "data", "inventory.csv")
if not os.path.exists(inventory_path):
    os.makedirs(os.path.dirname(inventory_path))
    df = pd.DataFrame(columns=["Home", "Visitor", "Date"])
    df.to_csv(inventory_path)


def check_exists(driver, by: str, target: str):
    """
    checking if some tag exists on template or not ;
    some tags may be still on loading stage.

    driver: webdriver object
    by: on what aspect this function should search for specific tag
    target: string of target in that specific 'by' aspect
    """
    try:
        # conditions for different aspects
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

    # return False if persued tag is not loaded or changed
    # not loaded tag
    except NoSuchElementException:
        return False
    # changed tag
    except StaleElementReferenceException:
        return False
    return True


def wait_till_located(driver, by: str, target: str, timestep: int):
    """
    walks through a while loop and uses 'check_exists' function constantly till target tag appeares or become loaded completely

    driver: webdriver object
    by: on what aspect this function should search for specific tag
    target: string of target in that specific 'by' aspect
    timestep: each iteration time will be added to timestep as a delay
    """

    # a loop till 'check_exists' function returns True
    while check_exists(driver, by, target) == False:
        print("Loading page...")
        time.sleep(timestep)


def main_sheet(df_list: list, sheet_name: str) -> None:
    """
    this function tells scraper how to assign each quarter df into one df and save it on data folder

    df_list: list of quarters df that are going to stick together
    sheet_name: name of sheet
    """
    q = 1
    ls = []
    for i, df in enumerate(df_list):
        if type(df) == pd.DataFrame:
            # adding some row for the sake of quarter change mentioning
            quarter_row = pd.DataFrame(
                [[f"Quarter {q}" for _ in range(6)]], columns=df.columns
            )
            # assining 'Home' and 'Visitor' columns of quarter row to team names
            quarter_row["Home"] = [df_list[i - 1]["Home"]]
            quarter_row["Visitor"] = [df_list[i - 1]["Visitor"]]
            # sticking made quarter row as first row of last df
            df = pd.concat([quarter_row, df], ignore_index=True)
            # appending df with quarter row to a list
            ls.append(df)
            q += 1

    # combining all quarter-row-containing-dfs together
    df = pd.concat(ls, ignore_index=True)

    # make data folder if not exists
    data_path = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_path):
        os.mkdir(data_path)

    df.to_csv(os.path.join(data_path, sheet_name))


def inventory_sheet(home_team: str, visitor_team: str, date: str):
    """
    adds new data info to inventory columns

    home_team: name of home team
    visitor_team: name of visitor team
    date: date of match between these two teams
    """
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


def check_inventory(home_team: str, visitor_team: str, date: str) -> bool:
    """
    checking inventory sheet if it has data of specefic match or not

    home_team: name of home team
    visitor_team: name of visitor team
    date: date of match between these two teams
    """
    df = pd.read_csv(inventory_path)
    # comparison line
    expression = df[
        (df["Home"] == home_team)
        & (df["Visitor"] == visitor_team)
        & (df["Date"] == date)
    ]

    # retrun true if there is no such data
    return len(expression) == 0
