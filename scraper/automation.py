from typing import Coroutine, Dict, Generator, List, Optional, Tuple
import aiohttp
from bs4 import BeautifulSoup
from aiohttp import ClientSession
import asyncio, os
from datetime import datetime
from lxml import etree
import pandas as pd
from tables_function import *
from report_maker import Reporter


class Scraper:
    def __init__(self, season: str, files_per_scrape: int) -> None:
        self.season = season
        self.files_per_scrape = files_per_scrape
        self.custom_min = 1

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
        self.data_path = os.path.join(os.getcwd(), "data")
        self.tables_path = os.path.join(os.getcwd(), "tables")
        self.inv_path = os.path.join(self.tables_path, "inventory.csv")

        # defining inventory.csv path and creating it if not exists
        if not os.path.exists(self.inv_path):
            if not os.path.exists(os.path.dirname(self.inv_path)):
                os.mkdir(os.path.dirname(self.inv_path))

            df = pd.DataFrame(columns=["Home", "Visitor", "Date"])
            df.to_csv(self.inv_path)

        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)

    def main_sheet(self, df_list: List[dict | pd.DataFrame], sheet_name: str) -> pd.DataFrame | str:
        """
        this function tells scraper how to assign each quarter df into one df and save it on data folder

        df_list: list of quarters df that are going to stick together
        sheet_name: name of sheet
        """

        q = 1
        ls = []
        for i, df in enumerate(df_list):
            if isinstance(df, pd.DataFrame):
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
        try:
            df = pd.concat(ls, ignore_index=True)
        except ValueError: # in case ls has no dataframe inside
            return "Error: Empty dataframe"

        df.to_csv(os.path.join(self.data_path, sheet_name))
        return df

    def fill_inv(self, home_team: str, visitor_team: str, date: str):
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

    def is_in_inv(self, home_team: str, visitor_team: str, date: str) -> bool:
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

        # retrun true if there is such data
        return len(expression) != 0

    def check_tables_dir(self, home: str, visitor: str, date: str, HorV:str) -> None:
        match_dir = os.path.join(self.tables_path, home, visitor, date, HorV)
        if not os.path.exists(match_dir):
            os.makedirs(match_dir)

    def find_xpath(self, soup: Optional[BeautifulSoup], xpath :str) -> List[etree._Element]:
        """
        Finds specific element with xpath addressing

        soup: soup which we are searching in
        xpath: xpath pattern which we are searching for
        """

        tree = etree.fromstring(str(soup), parser=etree.HTMLParser())
        elements = tree.xpath(xpath)
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
            except aiohttp.client_exceptions.ClientConnectorError:
                print(f"Connection Error: {url}")
            except aiohttp.client_exceptions.ClientOSError:
                print(f"Client OS Error: {url}")

        try:
            return soup
        except:
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

    async def raw2table(self, raw_df: pd.DataFrame, home_team: str, visitor_team: str, date_of_match: str) -> int:
        """
        All tables are created here from every data file

        raw_df: raw scraped dataframe out of play page
        home_team: name of home team
        visitor_team: name of visitor team
        date_of_match: match date
        """

        await asyncio.sleep(0)
        schematic_name = f"{home_team}_{visitor_team}_{date_of_match}"
        invalids = 0
        for HorV in ("Home", "Visitor"):
            match_dir = os.path.join(self.tables_path, home_team, visitor_team, date_of_match, HorV)
            self.check_tables_dir(home_team, visitor_team, date_of_match, HorV)
            raw_df = initial_edit(raw_df, HorV)

            try:
                (
                    cusMin_df,
                    events_df,
                    lineup_event_df,
                    time_score_df,
                    lineup_time_score_df,
                    events_df5min,
                    time_score_df5min,
                    eff_columns,
                ) = await asyncio.to_thread(main_loop, raw_df, HorV, self.custom_min)
                print(schematic_name, "--->", HorV, "main loop done")

            except ValueError:
                # sometimes player name wasn't nither on starters nor players entered the game but he exits suddenly :|
                invalids += 1
                print(schematic_name, "--->", HorV, "Invalid substitution data!")
                continue

            except IndexError:
                invalids += 1
                print(schematic_name, "--->", HorV, "Empty Dataframe!")
                continue

            eff_task = create_eff_df(cusMin_df, eff_columns, self.custom_min)
            pfinal_task = create_pfinal_df(
                raw_df,
                HorV,
                date_of_match,
                events_df,
                time_score_df,
                events_df5min,
                time_score_df5min,
            )

            lfinal_task = create_lfinal_df(
                raw_df, HorV, date_of_match, lineup_time_score_df, lineup_event_df
            )

            tasks = [eff_task, pfinal_task, lfinal_task]
            eff_df, pfinal_table, lfinal_table = await asyncio.gather(*tasks)

            cusMin_df.to_csv(os.path.join(match_dir, "CustomMinuteEvents.csv"))
            events_df.to_csv(os.path.join(match_dir, "PAllEvents.csv"))
            lineup_event_df.to_csv(os.path.join(match_dir, "LAllEvents.csv"))
            time_score_df.to_csv(os.path.join(match_dir, "PTimeScore.csv"))
            lineup_time_score_df.to_csv(os.path.join(match_dir, "LTimeScore.csv"))
            events_df5min.to_csv(os.path.join(match_dir, "5MinEvents.csv"))
            time_score_df5min.to_csv(os.path.join(match_dir, "5MinTimeScore.csv"))
            eff_df.to_csv(os.path.join(match_dir, "Effectiveness.csv"))
            pfinal_table.to_csv(os.path.join(match_dir, "PFinalTable.csv"))
            lfinal_table.to_csv(os.path.join(match_dir, "LFinalTable.csv"))

        return invalids

    async def match_process(self, session:ClientSession, url:str) -> Tuple[str, int] | str:
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
            if self.is_in_inv(home_team, visitor_team, date_of_match):
                print(f"{sheet_name} EXISTS")
                return "Exists"

            print(f"{sheet_name} STARTED")
        else:
            return "Error: sheet tuple can't be provided"

        if not is_valid:
            return "Error: No content | overtime exists"

        players_dict = await self.general_listing(session, url, home_team, visitor_team)
        query = "?view=plays"
        rows_url = url + query
        rows_soup = await self.get_soup(session, rows_url)
        df_list = await asyncio.to_thread(self.scrape_rows, rows_soup, players_dict)

        df = self.main_sheet(df_list, sheet_name)
        if isinstance(df, str):
            return df

        invalids = await self.raw2table(df, home_team, visitor_team, date_of_match)
        self.fill_inv(home_team, visitor_team, date_of_match)
        print(f"{sheet_name} DONE")
        return sheet_name, invalids

    def chunk_tasks(self, tasks:List[Coroutine], chunk_size:int) -> Generator[List[Coroutine], None, None]:
        """
        Chunks list of tasks into multiple lists

        tasks: list of all tasks
        chunk_size: how many tasks would be in each chunk (this means how many tasks will be done at same time)
        """

        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i + chunk_size]
            yield chunk

    async def main(self) -> List[str]:
        """
        Running core
        Returns list of added sheets for reporter to update just their reports
        """

        async with ClientSession() as session:
            boxes_soup = await self.get_soup(session, self.main_page + self.box_scores_page)
            urls = self.find_xpath(boxes_soup, self.xpath_dict["box_scores"])

            # all tasks list will be built at this loop
            tasks = []
            for url in urls:
                url = self.main_page + url.get("href")
                task = self.match_process(session, url)
                tasks.append(task)

            # running tasks inside each chunk
            errors = []
            invalids = 0
            added_sheets = []
            for chunk in self.chunk_tasks(tasks, self.files_per_scrape):
                match_contents = await asyncio.gather(*chunk)
                for content in match_contents:
                    if isinstance(content, str) and "Error" in content:
                        errors.append(content)
                    elif isinstance(content, tuple):
                        inval = content[1]
                        invalids += inval

                        if inval != 2:
                            added_sheets.append(content[0])

            print(f"Errors on scraper: {len(errors)}\nInvalid data: {invalids}")
            return added_sheets

if __name__ == "__main__":
    scraper = Scraper("2023-24", 25)
    reporter = Reporter(25)
    added_sheets = asyncio.run(scraper.main())
    print("----------------------------------REPORTING-STARTED----------------------------------")
    asyncio.run(reporter.main(added_sheets))
