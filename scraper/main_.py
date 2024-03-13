from bs4 import BeautifulSoup
from aiohttp import ClientSession
import asyncio, aiohttp
from lxml import etree
import pandas as pd


class Scraper:
    def __init__(self, season:str) -> None:
        self.season = season

        self.xpath_dict = {
            "box_scores": "//a[@class='link' and ./span[2][contains(text(), 'Box Score')]]",
            "playbyplay": "//a[contains(text(),'Play by Play')]",
            "playbyplaytab": "//span[@class='label' and contains(text(), 'Periods:')]",
            "q_element": "//table[@role='presentation']",
        }

        self.main_page = "https://universitysport.prestosports.com/"
        self.box_scores_page = f"sports/mbkb/{self.season}/schedule"

    def main_sheet(self, df_list: list, sheet_name: str) -> None:
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

    def inventory_sheet(self, home_team: str, visitor_team: str, date: str):
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

    def check_inventory(self, home_team: str, visitor_team: str, date: str) -> bool:
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

    def find_xpath(self, soup:BeautifulSoup, xpath:str):
        tree = etree.fromstring(str(soup), parser=etree.HTMLParser())
        elements = tree.xpath(xpath)
        return elements

    async def check_content(self, soup:BeautifulSoup) -> bool:
        """
        checking if match template has content or overtime
        """

        await asyncio.sleep(0)
        # empty content checking block
        has_content = False
        element = self.find_xpath(soup, "//a[contains(text(), '1st Qtr')]")
        if len(element) != 0:
            has_content = True
            
        # overtime checking block
        has_overtime = False
        element = self.find_xpath(soup, "//a[contains(@data-view, 'period5')]")
        if len(element) != 0:
            has_overtime = True

        if has_content and not has_overtime:
            return True
        else:
            return False

    async def get_sheet_name(self, soup:BeautifulSoup) -> str:
        """
        providing final sheet name by template heading and date
        """

        await asyncio.sleep(0)
        xpath = "//div[@class = 'head']/h1"
        head_element = self.find_xpath(soup, xpath)[0].text_content().split("\n")

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

    async def get_soup(self, session:ClientSession, url:str) -> BeautifulSoup|None:
        # async with ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                try:
                    response = await response.text()
                    return BeautifulSoup(response, 'html.parser')
                except UnicodeDecodeError:
                    print(f"Error fetching {url}: {response.status}")
                    return None
            else:
                print(f"Error fetching {url}: {response.status}")
                return None

    async def quarter_listing(self, quarters_player_dict:dict,
                              quarter:int,
                              session:ClientSession,
                              url:str, home_team:str,
                              visitor_team:str):

        query = f"?view=period{quarter + 1}"
        url_ = url + query
        soup = self.get_soup(session, url_)

        teams_dict = {visitor_team: "Visitor", home_team: "Home"}
        for team in teams_dict:
            players_xpath_pattern = f"//section[contains(@class, 'active')]//span[@class='team-name' and contains(text(), \"{team}\")]/../../..//*[self::span or self::a][@class='player-name']"
            raw_players = self.find_xpath(soup, players_xpath_pattern)
            raw_players = [element.text_content() for element in raw_players]
            quarters_player_dict[quarter + 1][teams_dict[team]] = {
                "starters": raw_players[:5],
                "reserves": raw_players[5:],
            }

    async def general_listing(self, session:ClientSession, url:str, home_team, visitor_team):
        quarters_player_dict = {key: {} for key in range(1, 5)}
        tasks = []
        for q in range(4):
            task = self.quarter_listing(quarters_player_dict, q, session, url, home_team, visitor_team)
            tasks.append(task)

        await asyncio.gather(*tasks)
        return quarters_player_dict

    def scrape_rows(self, soup:BeautifulSoup, quarters_player_dict:dict):
        quarters_element = self.find_xpath(soup, self.xpath_dict["q_element"])

        df_list = []
        for qn, element in enumerate(quarters_element):
            element = etree.tostring(element, encoding='unicode')
            q_soup = BeautifulSoup(element, "html.parser")
            print(f"\nQUARTER {qn + 1}\n")

            # event row element
            rows = q_soup.find_all(class_="row")

            df = pd.DataFrame(columns=["Time", "Home", "H-event", "Score", "V-event", "Visitor"])
            df_list.append(quarters_player_dict[qn + 1])

            for row in rows:
                event_time = row.find(class_="time").text
                home_score = row.find(class_="h-score").text
                visitor_score = row.find(class_="v-score").text
                event_detail = row.find(class_="text").text.strip()
                team_name = row.find("img").get("alt")
                homeORvisitor = str(row.find("img").get("class")).split(" ")[1]

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

        return df_list

    async def match_process(self, session:ClientSession, url:str):
        soup = self.get_soup(session, url)
        tasks = [self.check_content(soup), self.get_sheet_name(soup)]
        is_valid, sheet_tuple = await asyncio.gather(*tasks)

        if not is_valid:
            return None

        sheet_name, home_team, visitor_team = sheet_tuple

        quarters_player_dict = await self.general_listing(session, url, home_team, visitor_team)
        query = "?view=plays"
        rows_url = url + query
        rows_soup = self.get_soup(session, rows_url)
        df_list = await asyncio.to_thread(self.scrape_rows, rows_soup, quarters_player_dict)

        if self.check_inventory(home_team, visitor_team, date_of_match):
            self.main_sheet(df_list, sheet_name)
            self.inventory_sheet(home_team, visitor_team, date_of_match)

    async def main(self):
        async with ClientSession() as session:
            boxes_soup = await self.get_soup(session, self.main_page + self.box_scores_page)
            urls = self.find_xpath(boxes_soup, self.xpath_dict["box_scores"])

            tasks = []
            for url in urls:
                url = self.main_page + url.get("href")
                task = self.match_process(session, url)
                tasks.append(task)

            match_contents = await asyncio.gather(*tasks)
            print(match_contents)

scraper = Scraper("2023-24")
asyncio.run(scraper.main())
