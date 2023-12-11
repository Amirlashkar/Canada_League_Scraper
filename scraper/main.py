from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
import os
import yaml
import time
from datetime import datetime
from functions import *

# loading config file
with open("scraper/config.yml", "rb") as f:
    cfg = yaml.load(f, yaml.Loader)
    cfg = cfg["main"]

season = "2023-24"
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get(f"https://universitysport.prestosports.com/sports/mbkb/{season}/schedule")

driver.maximize_window()

# getting elements of last column Box Scores link
box_scores = driver.find_elements(
    By.XPATH, "//a[@class='link' and ./span[2][contains(text(), 'Box Score')]]"
)

quarters_player_dict = {key: {} for key in range(1, 5)}
# iterating over every link to get needed Data
for i, box_score in enumerate(box_scores):
    wait_till_located(
        driver,
        "XPATH",
        "//a[@class='link' and ./span[2][contains(text(), 'Box Score')]]",
        1,
    )

    # getting elements of last column Box Scores link
    links = driver.find_elements(
        By.XPATH, "//a[@class='link' and ./span[2][contains(text(), 'Box Score')]]"
    )
    # clicking on link
    driver.execute_script("arguments[0].scrollIntoView();", links[i])
    time.sleep(1)
    links[i].click()

    # checking if match template has content
    try:
        driver.find_element(By.XPATH, "//a[contains(text(), '1st Qtr')]")
    except NoSuchElementException:
        driver.back()
        continue

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

    # this block ignores matches having overtimes
    try:
        driver.find_element(By.XPATH, "//a[contains(@data-view, 'period5')]")
        driver.back()
        continue
    except NoSuchElementException:
        pass

    if os.path.exists(os.path.join(os.getcwd(), "data", sheet_name)):
        driver.back()
        continue

    print(
        f"########################## {visitor_team} at {home_team} ##########################"
    )
    # waiting for link to load
    wait_till_located(driver, "XPATH", "//a[contains(text(),'Play by Play')]", 1)

    for q in range(4):
        driver.find_element(
            By.XPATH, f"//a[contains(text(),'{q + 1}') and contains(text(), 'Qtr')]"
        ).click()
        wait_till_located(
            driver,
            "XPATH",
            f"//section[contains(@class, 'active')]//h1[contains(text(), 'Period{q + 1}')]",
            1,
        )
        teams_dict = {visitor_team: "Visitor", home_team: "Home"}
        for team in teams_dict:
            players_xpath_pattern = f"//section[contains(@class, 'active')]//span[@class='team-name' and contains(text(), \"{team}\")]/../../..//*[self::span or self::a][@class='player-name']"
            raw_players = driver.find_elements(By.XPATH, players_xpath_pattern)
            raw_players = [element.text for element in raw_players]
            quarters_player_dict[q + 1][teams_dict[team]] = {
                "starters": raw_players[:5],
                "reserves": raw_players[5:],
            }

    # clicking on Play by Play Button
    driver.find_element(By.XPATH, "//a[contains(text(),'Play by Play')]").click()
    # wait to load Play by Play tab
    wait_till_located(
        driver, "XPATH", "//span[@class='label' and contains(text(), 'Periods:')]", 1
    )
    # getting quarters element
    quarters_element = driver.find_elements(By.XPATH, "//table[@role='presentation']")
    df_list = []
    for qn, element in enumerate(quarters_element):
        print(f"\nQUARTER {qn + 1}\n")
        # event row element
        rows = element.find_elements(By.CLASS_NAME, "row")

        df = pd.DataFrame(
            columns=["Time", "Home", "H-event", "Score", "V-event", "Visitor"]
        )
        df_list.append(quarters_player_dict[qn + 1])

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
                homeORvisitor = str(
                    row.find_element(By.TAG_NAME, "img").get_attribute("class")
                ).split(" ")[1]
            except StaleElementReferenceException:
                time.sleep(2)
                event_detail = row.find_element(By.CLASS_NAME, "text").text.strip()
                team_name = row.find_element(By.TAG_NAME, "img").get_attribute("alt")
                homeORvisitor = str(
                    row.find_element(By.TAG_NAME, "img").get_attribute("class")
                ).split(" ")[1]

            data = {
                "Time": [event_time],
                "Home": [None],
                "H-event": [None],
                "Score": [f"{home_score} - {visitor_score}"],
                "V-event": [None],
                "Visitor": [None],
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

    if check_inventory(home_team, visitor_team, date_of_match):
        main_sheet(df_list, sheet_name)
        inventory_sheet(home_team, visitor_team, date_of_match)

    for i in range(6):
        driver.back()
