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
import time
from datetime import datetime
from scraper_functions import *

driver_options = webdriver.ChromeOptions()
driver_options.add_argument("--headless")
driver_options.add_argument("--no-sandbox")  # This make Chromium reachable
driver_options.add_argument("--disable-dev-shm-usage")  # Overcomes limited resource problems
driver_options.add_argument('start-maximized')
driver_options.add_argument('disable-infobars')
driver_options.add_argument("--disable-extensions")

season = "2023-24"
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=driver_options)
driver.get(f"https://universitysport.prestosports.com/sports/mbkb/{season}/schedule")

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

    if not check_content(driver):
        continue

    sheet_name, home_team, visitor_team = get_sheet_name(driver)

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
