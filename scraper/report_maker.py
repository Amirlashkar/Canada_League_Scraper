from typing import Dict, Generator, List, Optional, Coroutine
import pandas as pd
import numpy as np
import os, difflib, ast
from tables_function import cal_eff, cal_rtg
import asyncio


class Reporter:
    def __init__(self, menORwomen: str, report_per_iter: int) -> None:
        self.report_per_iter = report_per_iter

        # defining static pathes
        self.data_path = os.path.join(os.getcwd(), "data", menORwomen)
        self.tables_path = os.path.join(self.data_path, "tables")
        self.reports_path = os.path.join(self.data_path, "reports")

        self.teams_dict = {}

        # reports dir will be created if not exists
        if not os.path.exists(self.reports_path):
            os.makedirs(self.reports_path)

    def find_valid_similar(self, playername: str, players_list: List[str]) -> Optional[str]:
        """
        this function compares a playername with whole list of players name and chooses best alternative name

        playername: name which we're going to compare it
        players_list: list which we're comparing playername with it
        """

        found = difflib.get_close_matches(playername, players_list, n=1, cutoff=0.0)[0]
        matcher = difflib.SequenceMatcher(None, playername, found)
        diff_ratio = matcher.ratio()

        if diff_ratio >= 0.70:
            if len(playername) > len(found):
                main_name = playername
            else:
                main_name = found

            return main_name

        else:
            return None

    def mix_similars(self, df: pd.DataFrame, LP: str) -> pd.DataFrame:
        """
        some names are for one person but in different forms on df;
        this function makes them as one.

        df: dataframe with alternative names
        LP: either table is player related or lineup related
        """

        if LP == "P":
            players = df["Player Name"].to_list()
        else:
            df["Lineup"] = df["Lineup"].apply(ast.literal_eval)
            players = df["Lineup"].to_list()
            players = [element for tup in players for element in tup]

        # may need second iteration cause some strings are gradual to appeare their main_name
        for i in range(2):
            if LP == "P":
                for ind, row in df.iterrows():
                    playername = row["Player Name"]
                    comparing_ls = players.copy()
                    comparing_ls.remove(playername)

                    main_name = self.find_valid_similar(playername, comparing_ls)

                    if main_name:
                        df.loc[ind, "Player Name"] = main_name

            else:
                for ind, row in df.iterrows():
                    for i, player in enumerate(row["Lineup"]):
                        comparing_ls = players.copy()
                        comparing_ls.remove(player)

                        main_name = self.find_valid_similar(player, comparing_ls)

                        if main_name:
                            list_version = list(df.loc[ind, "Lineup"])
                            list_version[i] = main_name
                            tuple_version = tuple(list_version)
                            if df.loc[ind, "Lineup"] != tuple_version:
                                df.loc[ind, "Lineup"] = tuple_version

            df = df.groupby(["Player Name" if LP == "P" else "Lineup"]).sum()
            df = df.reset_index()

        return df

    async def measure_report(self, dfs_dict: Dict[str, List[pd.DataFrame]]) -> List[pd.DataFrame]:
        """
        the function sticks dataframes of a team from all season wide and sums up players statistic together and also adds new columns
        dfs_ls: dictionary of an specific team dataframes from all over season
        """

        dfs = []
        for key in dfs_dict:
            print(key)
            concat_df = pd.concat(dfs_dict[key])

            try:
                # CAUTION: last 5min efficiencies should be somehow filtered of "Not in the time" first and then 
                # you can get mean of all the columns to show for each player !!!
                summed_df = concat_df.groupby(["Player Name"]).sum()
            except:
                summed_df = concat_df.groupby(["Lineup"]).sum()

            summed_df = summed_df.reset_index()
            LP = key[0]
            summed_df = await asyncio.to_thread(self.mix_similars, summed_df, LP)

            if "E" not in key:
                summed_df["Eff"] = summed_df.apply(lambda row: cal_eff(row["total off possession"],
                                                                    row["total def possession"],
                                                                    row["minutes"]), axis=1)

                if LP == "P":
                    ptsKey = "realPtsScored"
                else:
                    ptsKey = "PtsScored"

                summed_df["OffRtg"] = summed_df.apply(lambda row: cal_rtg(row[ptsKey],
                                                                    row["total off possession"]), axis=1)

                summed_df["DefRtg"] = summed_df.apply(lambda row: cal_rtg(row["PtsConceded"],
                                                                    row["total def possession"]), axis=1)

                summed_df["NetRtg"] = summed_df["OffRtg"] - summed_df["DefRtg"]

            dfs.append(summed_df)

        return dfs

    async def fill_team_dict(self, home: str, updating_teams: List[str]) -> None:
        if home not in updating_teams:
            return None

        await asyncio.sleep(0)
        home_path = os.path.join(self.tables_path, home)
        visitor_teams = os.listdir(home_path)
        try:
            visitor_teams.remove(".DS_Store")
        except:
            pass
        for visitor in visitor_teams:
            if visitor not in updating_teams:
                return None

            visitor_path = os.path.join(home_path, visitor)
            dates = os.listdir(visitor_path)
            try:
                dates.remove(".DS_Store")
            except:
                pass
            for date in dates:
                for HorV in ("Home", "Visitor"):
                    teamname = home if HorV == "Home" else visitor
                    try:
                        final_table_path = os.path.join(home_path, visitor, date, HorV, "PFinalTable.csv")
                        final_table = pd.read_csv(final_table_path)

                        lineup_table_path = os.path.join(home_path, visitor, date, HorV, "LFinalTable.csv")
                        lineup_table = pd.read_csv(lineup_table_path)

                        Pevents_table_path = os.path.join(home_path, visitor, date, HorV, "PAllEvents.csv")
                        Pevents_table = pd.read_csv(Pevents_table_path)

                        Levents_table_path = os.path.join(home_path, visitor, date, HorV, "LAllEvents.csv")
                        Levents_table = pd.read_csv(Levents_table_path)

                        print(f"{home} VS {visitor} at {date} --> {HorV}")

                    except FileNotFoundError:
                        print("Table not found!")
                        break

                    # create team key if it doesn't exist on teams_dict
                    if teamname not in self.teams_dict:
                        self.teams_dict[teamname] = {
                            "P":[],
                            "L":[],
                            "PE":[],
                            "LE":[],
                        }

                    # dropping unneccessary columns
                    try:
                        drops = ["date", "game_type", "home/visitor", 
                                "opponent", "OffRtg", "DefRtg",
                                "NetRtg", "global efficiency", "quarter2 last 5min efficiency",
                                "quarter4 last 5min efficiency"]

                        final_table = final_table.drop(drops, axis=1)
                        final_table = final_table.drop(columns=final_table.filter(like="Unnamed").columns)
                    except:
                        pass

                    self.teams_dict[teamname]["P"].append(final_table)
                    self.teams_dict[teamname]["L"].append(lineup_table)
                    self.teams_dict[teamname]["PE"].append(Pevents_table)
                    self.teams_dict[teamname]["LE"].append(Levents_table)

    async def team_report(self, team: str) -> None:
        await asyncio.sleep(0)
        team_report_path = os.path.join(self.reports_path, team)
        if not os.path.exists(team_report_path):
            os.makedirs(team_report_path)

        print(team, "started")

        try:
            team_data = await asyncio.create_task(self.measure_report(self.teams_dict[team]))

            print(team, "ended")
            for i, df in enumerate(team_data):
                if i == 0:
                    players_report = df
                elif i == 1:
                    lineup_report = df
                elif i == 2:
                    Pevents_report = df
                else:
                    Levents_report = df

            players_path = os.path.join(team_report_path, "PSeasonalReport.csv")
            lineup_path = os.path.join(team_report_path, "LSeasonalReport.csv")
            Pevents_path = os.path.join(team_report_path, "PEventsSeasonalReport.csv")
            Levents_path = os.path.join(team_report_path, "LEventsSeasonalReport.csv")
            players_report.to_csv(players_path)
            lineup_report.to_csv(lineup_path)
            Pevents_report.to_csv(Pevents_path)
            Levents_report.to_csv(Levents_path)

        except ValueError:
            pass

    def updating_teams_(self, added_sheets: List[str]) -> List[str]:
        teams = []
        for sheet in added_sheets:
            splited = sheet.split("_")
            teams.append(splited[0])
            teams.append(splited[1])

        updating_teams = list(np.unique(teams))
        return updating_teams

    def chunk_tasks(self, tasks:List[Coroutine], chunk_size:int) -> Generator[List[Coroutine], None, None]:
        """
        Chunks list of tasks into multiple lists

        tasks: list of all tasks
        chunk_size: how many tasks would be in each chunk (this means how many tasks will be done at same time)
        """

        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i + chunk_size]
            yield chunk

    async def main(self, added_sheets: List[str]) -> None:
        """
        Running core

        added_sheets: list of sheets that reporter should update
        """

        existing_teams = os.listdir(self.tables_path)
        try:
            existing_teams.remove("inventory.csv")
            existing_teams.remove(".DS_Store")
        except:
            pass

        updating_teams = self.updating_teams_(added_sheets)

        homes_task = []
        for home in existing_teams:
            task = self.fill_team_dict(home, updating_teams)
            homes_task.append(task)

        await asyncio.gather(*homes_task)

        teams_task = []
        for team in self.teams_dict:
            task = self.team_report(team)
            teams_task.append(task)

        for chunk in self.chunk_tasks(teams_task, self.report_per_iter):
            await asyncio.gather(*chunk)

if __name__ == "__main__":
    reporter = Reporter(25)
    asyncio.run(reporter.main())
