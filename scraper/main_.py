from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from scraper_functions import *
import asyncio


class Scraper:
    def __init__(self, season:str) -> None:
        self.driver = self.build_driver(False)
        self.season = season

        self.xpath_dict = {
            "box_scores": "//a[@class='link' and ./span[2][contains(text(), 'Box Score')]]",
            "playbyplay": "//a[contains(text(),'Play by Play')]",
            "playbyplaytab": "//span[@class='label' and contains(text(), 'Periods:')]",
            "q_element": "//table[@role='presentation']",
        }

        self.box_scores_page = f"https://universitysport.prestosports.com/sports/mbkb/{self.season}/schedule"

    def build_driver(self, withUI:bool) -> Chrome:
        driver_options = webdriver.ChromeOptions()
        if withUI == False:
            UI_options = ["--headless",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "start-maximized",
                        "disable-infobars",
                        "--disable-extensions",]

            for opt in UI_options:
                driver_options.add_argument(opt)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                                       options=driver_options)

        return driver
    
    def get_links(self) -> list:
        self.driver.get(self.box_scores_page)
        box_scores = self.driver.find_elements(By.XPATH, self.xpath_dict["box_scores"])
        links = [self.box_scores_page + box.get_attribute("href") for box in box_scores]
        
        return links

    async def match_scraper(self, link:str, driver:Chrome):
        await asyncio.sleep(0)
        print(link)
        driver.get(link)

        quarters_player_dict = {key: {} for key in range(1, 5)}

        wait_till_located(
            driver, "XPATH",
            self.xpath_dict["box_scores"], 1
        )
        
        if not check_content(driver):
            return

        sheet_name, home_team, visitor_team, date_of_match = get_sheet_name(driver)

        # if os.path.exists(os.path.join(os.getcwd(), "data", sheet_name)):
        #     driver.back()
        #     return

        print(
            f"########################## {visitor_team} at {home_team} ##########################"
        )
        #
        # wait_till_located(driver, "XPATH",
        #                   self.xpath_dict["playbyplay"], 1)
        #
        # for q in range(4):
        #     driver.find_element(
        #         By.XPATH, f"//a[contains(text(),'{q + 1}') and contains(text(), 'Qtr')]"
        #     ).click()
        #
        #     wait_till_located(
        #         driver,
        #         "XPATH",
        #         f"//section[contains(@class, 'active')]//h1[contains(text(), 'Period{q + 1}')]",
        #         1,
        #     )
        #
        #     teams_dict = {visitor_team: "Visitor", home_team: "Home"}
        #     for team in teams_dict:
        #         players_xpath_pattern = f"//section[contains(@class, 'active')]//span[@class='team-name' and contains(text(), \"{team}\")]/../../..//*[self::span or self::a][@class='player-name']"
        #         raw_players = driver.find_elements(By.XPATH, players_xpath_pattern)
        #         raw_players = [element.text for element in raw_players]
        #         quarters_player_dict[q + 1][teams_dict[team]] = {
        #             "starters": raw_players[:5],
        #             "reserves": raw_players[5:],
        #         }
        #
        # driver.find_element(By.XPATH, self.xpath_dict["playbyplay"]).click()
        #
        # wait_till_located(
        #     driver, "XPATH",
        #     self.xpath_dict["playbyplaytab"], 1
        # )
        #
        # quarters_element = driver.find_elements(By.XPATH, self.xpath_dict["q_element"])
        # df_list = []
        # for qn, element in enumerate(quarters_element):
        #     print(f"\nQUARTER {qn + 1}\n")
        #     # event row element
        #     rows = element.find_elements(By.CLASS_NAME, "row")
        #
        #     df = pd.DataFrame(
        #         columns=["Time", "Home", "H-event", "Score", "V-event", "Visitor"]
        #     )
        #     df_list.append(quarters_player_dict[qn + 1])
        #
        #     for row in rows:
        #         driver.execute_script("arguments[0].scrollIntoView();", row)
        #
        #         try:
        #             event_time = row.find_element(By.CLASS_NAME, "time").text
        #         except StaleElementReferenceException:
        #             time.sleep(2)
        #             event_time = row.find_element(By.CLASS_NAME, "time").text
        #
        #         try:
        #             try:
        #                 home_score = int(row.find_element(By.CLASS_NAME, "h-score").text)
        #                 visitor_score = int(row.find_element(By.CLASS_NAME, "v-score").text)
        #             except StaleElementReferenceException:
        #                 time.sleep(2)
        #                 home_score = int(row.find_element(By.CLASS_NAME, "h-score").text)
        #                 visitor_score = int(row.find_element(By.CLASS_NAME, "v-score").text)
        #         except NoSuchElementException:
        #             home_score = 0
        #             visitor_score = 0
        #         try:
        #             event_detail = row.find_element(By.CLASS_NAME, "text").text.strip()
        #             team_name = row.find_element(By.TAG_NAME, "img").get_attribute("alt")
        #             homeORvisitor = str(
        #                 row.find_element(By.TAG_NAME, "img").get_attribute("class")
        #             ).split(" ")[1]
        #         except StaleElementReferenceException:
        #             time.sleep(2)
        #             event_detail = row.find_element(By.CLASS_NAME, "text").text.strip()
        #             team_name = row.find_element(By.TAG_NAME, "img").get_attribute("alt")
        #             homeORvisitor = str(
        #                 row.find_element(By.TAG_NAME, "img").get_attribute("class")
        #             ).split(" ")[1]
        #
        #         data = {
        #             "Time": [event_time],
        #             "Home": [None],
        #             "H-event": [None],
        #             "Score": [f"{home_score} - {visitor_score}"],
        #             "V-event": [None],
        #             "Visitor": [None],
        #         }
        #
        #         if homeORvisitor == "home":
        #             data["Home"] = [team_name]
        #             data["H-event"] = [event_detail]
        #         else:
        #             data["Visitor"] = [team_name]
        #             data["V-event"] = [event_detail]
        #
        #         df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)
        #         # print(data)
        #
        #     df_list.append(df)
        #
        # if check_inventory(home_team, visitor_team, date_of_match):
        #     main_sheet(df_list, sheet_name)
        #     inventory_sheet(home_team, visitor_team, date_of_match)
        #
        # _ = [driver.back() for i in range(6)]
    
    async def main(self):
        links = self.get_links()
        tasks = []
        for link in links:
            print("adding task")
            driver = self.build_driver(False)
            task = self.match_scraper(link, driver)
            tasks.append(task)
        
        print("starting all tasks")
        await asyncio.gather(*tasks)

scraper = Scraper("2023-24")
asyncio.run(scraper.main())
