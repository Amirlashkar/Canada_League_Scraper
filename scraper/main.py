from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import requests
import yaml
import time
import sys
from functions import main_sheet, inventory_sheet, check_inventory

# loading config file
with open("scraper/config.yml", "rb") as f:
    cfg = yaml.load(f, yaml.Loader)
    cfg = cfg["main"]

followup_team = "Carleton"

driver = webdriver.Chrome(executable_path=cfg["chrome_driver_path"])
driver.get(f"https://universitysport.prestosports.com/sports/mbkb/2022-23/schedule?team={followup_team}")

# function to check if an element exists
def check_exists(by:str, target:str):
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
def wait_till_located(by:str, target:str, timestamp:int):
    while check_exists(by, target) == False:
        print("Loading page...")
        time.sleep(timestamp)

driver.maximize_window()

# name of opponent teams
op_teams = driver.find_elements(By.XPATH, "//a[contains(@class, 'team-name')]")
op_teams_ = [str(element.text) for element in op_teams]

# # getting elements of last column Box Scores link
# links = driver.find_elements(By.XPATH, "//span[contains(text(), 'Box Score')]/..")

rss_feed = requests.get(f"https://universitysport.prestosports.com/sports/mbkb/2022-23/schedule?print=rss&team={followup_team}").content
rss_feed = BeautifulSoup(rss_feed, features="xml")
dates = rss_feed.find_all("dc:date")

# iterating over every link to get needed Data
for i, op_team in enumerate(op_teams_):
    date_of_match = dates[i].text.split("T")[0]

    wait_till_located("XPATH", "//a[@class='link' and ./span[2][contains(text(), 'Box Score')]]", 1)

    sheet_name = followup_team + "|" + op_team + "|" + date_of_match
    # getting elements of last column Box Scores link
    links = driver.find_elements(By.XPATH, "//a[@class='link' and ./span[2][contains(text(), 'Box Score')]]")
    # clicking on link
    print(f"########################## {op_team} ##########################")
    driver.execute_script("arguments[0].scrollIntoView();", links[i])
    time.sleep(1)
    links[i].click()
    # waiting for link to load
    wait_till_located("XPATH", "//a[contains(text(),'Play by Play')]", 1)
    # clicking on Play by Play Button
    driver.find_element(By.XPATH, "//a[contains(text(),'Play by Play')]").click()
    # wait to load Play by Play tab
    wait_till_located("XPATH", "//span[@class='label' and contains(text(), 'Periods:')]", 1)
    # getting quarters element
    quarters_element = driver.find_elements(By.XPATH, "//table[@role='presentation']")
    df_list = []
    for qn, element in enumerate(quarters_element):

        print(f"\nQUARTER {qn + 1}\n")
        # event row element
        rows = element.find_elements(By.CLASS_NAME, "row")
        
        df = pd.DataFrame(columns=["Time", "Home", "H-event", "Score", "V-event", "Visitor"])
        for row in rows:

            driver.execute_script("arguments[0].scrollIntoView();", row)

            try:
                event_time = row.find_element(By.CLASS_NAME, "time").text
            except StaleElementReferenceException:
                time.sleep(2)
                event_time = row.find_element(By.CLASS_NAME, "time").text

            try:
                try:
                    home_score = int(row.find_element(By.CLASS_NAME, "h-score").text)
                    visitor_score = int(row.find_element(By.CLASS_NAME, "v-score").text)
                except StaleElementReferenceException:
                    time.sleep(2)
                    home_score = int(row.find_element(By.CLASS_NAME, "h-score").text)
                    visitor_score = int(row.find_element(By.CLASS_NAME, "v-score").text)
            except NoSuchElementException:
                home_score = 0
                visitor_score = 0
            try:
                event_detail = row.find_element(By.CLASS_NAME, "text").text.strip()
                team_name = row.find_element(By.TAG_NAME, "img").get_attribute("alt")
                homeORvisitor = str(row.find_element(By.TAG_NAME, "img").get_attribute("class")).split(" ")[1]
            except StaleElementReferenceException:
                time.sleep(2)
                event_detail = row.find_element(By.CLASS_NAME, "text").text.strip()
                team_name = row.find_element(By.TAG_NAME, "img").get_attribute("alt")
                homeORvisitor = str(row.find_element(By.TAG_NAME, "img").get_attribute("class")).split(" ")[1]
            # print(event_time, home_score, visitor_score, event_detail, team_name, homeORaway)

            data = {
                "Time": [event_time],
                "Home": [None],
                "H-event": [None],
                "Score": [f"{home_score} - {visitor_score}"],
                "V-event": [None],
                "Visitor": [None]
            }

            if homeORvisitor == "home":
                data["Home"] = [team_name]
                data["H-event"] = [event_detail]
            else:
                data["Visitor"] = [team_name]
                data["V-event"] = [event_detail]

            df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)
            print(data)

        df_list.append(df)

    if check_inventory(followup_team, op_team, date_of_match):
        main_sheet(df_list, sheet_name)
        inventory_sheet(followup_team, op_team, date_of_match)
        
    driver.back() ; driver.back()