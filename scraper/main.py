from typing import Coroutine, Dict, Generator, List, Optional, Tuple
from xml.etree.ElementTree import ElementTree
from bs4 import BeautifulSoup
from aiohttp import ClientSession
import asyncio, os
from datetime import datetime
from lxml import etree
import pandas as pd


class Scraper:
    def __init__(self, season: str, files_per_scrape: int) -> None:
        self.season = season
        self.files_per_scrape = files_per_scrape

        # all xpath which will be needed at following
        self.xpath_dict = {
            "box_scores": "//a[@class='link' and ./span[2][contains(text(), 'Box Score')]]",
            "first_q_tab": "//a[contains(text(), '1st Qtr')]",
            "overtime_tab": "//a[contains(@data-view, 'period5')]",
            "header": "//div[@class = 'head']/h1//text()",
            "q_element": "//table[@role='presentation']",
        }
        # dataframe columns for future data
        self.data_cols = ["Time", "Home", "H-event", "Score", "V-event", "Visitor"]

        self.main_page = "https://universitysport.prestosports.com/"
        self.box_scores_page = f"sports/mbkb/{self.season}/schedule"
        self.inv_path = os.path.join(os.getcwd(), "data", "inventory.csv")

        # defining inventory.csv path and creating it if not exists
        if not os.path.exists(self.inv_path):
            if not os.path.exists(os.path.dirname(self.inv_path)):
                os.mkdir(os.path.dirname(self.inv_path))

            df = pd.DataFrame(columns=["Home", "Visitor", "Date"])
            df.to_csv(self.inv_path)

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

        inventory_df = pd.read_csv(self.inv_path)
        adding_df = pd.DataFrame(data)
        df = pd.concat([inventory_df, adding_df], ignore_index=True)
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        df.to_csv(self.inv_path)

    def check_inventory(self, home_team: str, visitor_team: str, date: str) -> bool:
        """
        checking inventory sheet if it has data of specefic match or not

        home_team: name of home team
        visitor_team: name of visitor team
        date: date of match between these two teams
        """

        df = pd.read_csv(self.inv_path)
        # comparison line
        expression = df[
            (df["Home"] == home_team)
            & (df["Visitor"] == visitor_team)
            & (df["Date"] == date)
        ]

        # retrun true if there is no such data
        return len(expression) == 0

    def find_xpath(self, soup: Optional[BeautifulSoup], xpath :str) -> List[etree._Element]:
        """
        Finds specific element with xpath addressing

        soup: soup which we are searching in
        xpath: xpath pattern which we are searching for
        """

        tree = etree.fromstring(str(soup), parser=etree.HTMLParser())
        elements = tree.xpath(xpath)
        print(type(elements[0]))
        return elements

    async def check_content(self, soup: Optional[BeautifulSoup]) -> bool:
        """
        checking if match template has content or overtime

        soup: main match page BeautifulSoup
        """

        await asyncio.sleep(0)
        # empty content checking block
        has_content = False
        element = self.find_xpath(soup, self.xpath_dict["first_q_tab"])
        if len(element) != 0:
            has_content = True

        # overtime checking block
        has_overtime = False
        element = self.find_xpath(soup, self.xpath_dict["overtime_tab"])
        if len(element) != 0:
            has_overtime = True

        if has_content and not has_overtime:
            return True
        else:
            return False

    def header_sep(self, header: etree._Element, separator: str) -> Tuple[str, str]:
        """
        Takes a header with home & visitor teams name inside it,
        then tries to provide names from it using sseperator

        header: header with home and visitor name in it
        separator: string between two name
        """

        visitor_team = header.split(separator)[0].strip()
        home_team = header.split(separator)[1].strip()

        return home_team, visitor_team

    async def get_sheet_name(self, soup: Optional[BeautifulSoup]) -> Optional[Tuple[str, str, str, str]]:
        """
        providing final sheet name by template heading and date

        soup: main match page BeautifulSoup
        """

        await asyncio.sleep(0)
        header = self.find_xpath(soup, self.xpath_dict["header"])

        # some matches heading are separated in different ways
        if len(header) == 2:
            try:
                home_team, visitor_team = self.header_sep(header[0], " at ")
            except IndexError:
                try:
                    home_team, visitor_team = self.header_sep(header[0], " vs. ")
                except IndexError:
                    home_team, visitor_team = self.header_sep(header[0], " vs ")

            date_of_match = datetime.strptime(header[1], "%B %d, %Y").strftime("%m_%d_%Y")
            sheet_name = f"{home_team}_{visitor_team}_{date_of_match}.csv"

            return sheet_name, home_team, visitor_team, date_of_match

        # minor condition
        elif len(header) > 2:
            while " " in header:
                header.remove(" ")

            header = [info.strip() for info in header]
            try:
                header.remove("at")
            except:
                try:
                    header.remove("vs")
                except:
                    header.remove("vs.")

            visitor_team = header[0]
            home_team = header[1]
            date_of_match = datetime.strptime(header[2], "%B %d, %Y").strftime("%m_%d_%Y")

            sheet_name = f"{home_team}_{visitor_team}_{date_of_match}.csv"

            return sheet_name, home_team, visitor_team, date_of_match

        else:
            return None

    async def get_soup_(self, session: ClientSession, url: str) -> Optional[BeautifulSoup]:
        """
        The function makes a single request which may fail also

        session: requesting session
        url: link which we are taking its soup
        """

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

    async def get_soup(self, session: ClientSession, url: str) -> Optional[BeautifulSoup]:
        """
        Tries multiple times for for providing a link soup ;
        Handling timeouts due to connection possible failures

        session: requesting session
        url: link which we are taking its soup
        """

        for _ in range(3):
            if _ != 0:
                await asyncio.sleep(2)
                print("Retrying...")

            try:
                soup = await self.get_soup_(session, url)
                break
            except asyncio.exceptions.TimeoutError:
                print(f"TIMEOUT: {url}")

        if soup:
            return soup
        else:
            return None

    async def quarter_listing(self, input_dict: dict,
                              quarter: int,
                              session: ClientSession,
                              url: str, home_team: str,
                              visitor_team: str) -> None:
        """
        The function fills each quarter starter & reserve players list on input dictionary

        input_dict: the dictionary which would be filled
        quarter: considered quarter number
        session: requesting session
        url: main link of match without query
        home_team: home team name
        visitor_team: visitor team name
        """

        query = f"?view=period{quarter + 1}"
        url_ = url + query
        soup = await self.get_soup(session, url_)

        teams_dict = {visitor_team: "Visitor", home_team: "Home"}
        for team in teams_dict:
            players_xpath_pattern = f"//section[contains(@class, 'active')]//span[@class='team-name' and contains(text(), \"{team}\")]/../../..//*[self::span or self::a][@class='player-name']"
            raw_players = self.find_xpath(soup, players_xpath_pattern)
            raw_players = [element.text for element in raw_players]
            input_dict[quarter + 1][teams_dict[team]] = {
                "starters": raw_players[:5],
                "reserves": raw_players[5:],
            }

    async def general_listing(self, session: ClientSession,
                              url: str, home_team: str,
                              visitor_team: str) -> Dict[int, dict]:
        """
        makes tasks of all quarters starter & reserve players listing and does it asynchronously

        session: requesting session
        url: main link of match without query
        home_team: home team name
        visitor_team: visitor team name
        """

        players_dict = {key: {} for key in range(1, 5)}
        tasks = []
        for q in range(4):
            task = self.quarter_listing(players_dict, q,
                                        session, url,
                                        home_team, visitor_team)
            tasks.append(task)

        await asyncio.gather(*tasks)
        return players_dict

    def scrape_rows(self, soup: Optional[BeautifulSoup], players_dict: dict)\
        -> List[Dict[int, dict] | pd.DataFrame]: # returning dictionary inside list contains starter & reserve players
        """
        Main part of scraping which belongs to scraping rows on playbyplay tab of each match ;
        Each row is read and its data extracted into list of pandas DataFrame

        soup: soup of playbyplay tab of match
        players_dict: dictionary of starter & reserve players
        """

        quarters_element = self.find_xpath(soup, self.xpath_dict["q_element"])

        df_list = []
        for qn, element in enumerate(quarters_element):
            element = etree.tostring(element, encoding='unicode')
            q_soup = BeautifulSoup(element, "html.parser")

            rows = q_soup.find_all(class_="row")

            df = pd.DataFrame(columns=self.data_cols)
            df_list.append(players_dict[qn + 1])

            for row in rows:
                event_time = row.find(class_="time").text
                home_score = row.find(class_="h-score").text if row.find(class_="h-score") else 0
                visitor_score = row.find(class_="v-score").text if row.find(class_="v-score") else 0
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

                if "home" in homeORvisitor:
                    data["Home"] = [team_name]
                    data["H-event"] = [event_detail]
                else:
                    data["Visitor"] = [team_name]
                    data["V-event"] = [event_detail]

                df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)

            df_list.append(df)

        return df_list

    async def match_process(self, session:ClientSession, url:str) -> str:
        """
        All processes of one match

        session: requesting session
        url: main link of match
        """

        soup = await self.get_soup(session, url)
        tasks = [self.check_content(soup),
                 self.get_sheet_name(soup)]
        is_valid, sheet_tuple = await asyncio.gather(*tasks)

        if sheet_tuple:
            sheet_name, home_team, visitor_team, date_of_match = sheet_tuple
            path = os.path.join(os.getcwd(), "data_", sheet_name)
            if os.path.exists(path):
                print(f"{sheet_name} EXISTS")
                return "Exists"

            print(f"{sheet_name} STARTED")
        else:
            return "Error"

        if not is_valid:
            return "Error"

        players_dict = await self.general_listing(session, url, home_team, visitor_team)
        query = "?view=plays"
        rows_url = url + query
        rows_soup = await self.get_soup(session, rows_url)
        df_list = await asyncio.to_thread(self.scrape_rows, rows_soup, players_dict)

        if self.check_inventory(home_team, visitor_team, date_of_match):
            self.main_sheet(df_list, sheet_name)
            self.inventory_sheet(home_team, visitor_team, date_of_match)

        print(f"{sheet_name} DONE")
        return f"{sheet_name} DONE"
    
    def chunk_tasks(self, tasks:List[Coroutine], chunk_size:int) -> Generator[List[Coroutine], None, None]:
        """
        Chunks list of tasks into multiple lists

        tasks: list of all tasks
        chunk_size: how many tasks would be in each chunk (this means how many tasks will be done at same time)
        """

        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i + chunk_size]
            yield chunk

    async def main(self) -> None:
        """
        Running core
        """

        async with ClientSession() as session:
            boxes_soup = await self.get_soup(session, self.main_page + self.box_scores_page)
            urls = self.find_xpath(boxes_soup, self.xpath_dict["box_scores"])

            # all tasks list will be built at this loop
            tasks = []
            for url in urls[:1]:
                url = self.main_page + url.get("href")
                task = self.match_process(session, url)
                tasks.append(task)

            # running tasks inside each chunk
            errors = []
            for chunk in self.chunk_tasks(tasks, self.files_per_scrape):
                match_contents = await asyncio.gather(*chunk)
                errors += [content for content in match_contents if "Error" in content]

            print(f"Number of errors: {len(errors)}")

if __name__ == "__main__":
    scraper = Scraper("2023-24", 30)
    asyncio.run(scraper.main())
