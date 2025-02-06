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
        self.inventory_csv = pd.read_csv(os.path.join(self.tables_path, "inventory.csv"))

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

        try:
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
        except IndexError:
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

    async def measure_report(self, dfs_dict: Dict[str, List[pd.DataFrame]]) -> Dict[str, List[pd.DataFrame]]:
        """
        the function sticks dataframes of a team from all season wide and sums up players statistic together and also adds new columns

        dfs_ls: dictionary of an specific team dataframes from all over season
        """

        new_dfs = {key: None for key in list(dfs_dict.keys())}
        for key in dfs_dict:
            if "M" not in key:
                print(key)
                concat_df = pd.concat(dfs_dict[key])

                try:
                    # CAUTION: last 5min efficiencies should be somehow filtered of "Not in the time" first and then 
                    # you can get mean of all the columns to show for each player !!!
                    if "E" in key:
                        summed_df = concat_df.groupby(["Player Name"]).sum()
                    else:
                        summed_df = concat_df.groupby("Player Name").agg({
                            "PER": "mean",
                            "Shots Accuracy": "mean",
                            **{col: "sum" for col in concat_df.columns if col not in ["Player Name", "PER", "Shots Accuracy"]}
                        })
                except KeyError:
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

                new_dfs[key] = summed_df

        # creating PER and shots accuracy tables for whole season
        per_dfs = []
        shots_acc_dfs = []
        for i, df in enumerate(dfs_dict["P"]):
            per_df = df[["Player Name", "PER"]]
            shots_acc_df = df[["Player Name", "Shots Accuracy"]]

            # renaming value columns to corresponding match names
            per_df = per_df.rename(columns={"PER": dfs_dict["M"][i]})
            shots_acc_df = shots_acc_df.rename(columns={"Shots Accuracy": dfs_dict["M"][i]})

            per_dfs.append(per_df)
            shots_acc_dfs.append(shots_acc_df)

        season_per = pd.concat(per_dfs, ignore_index=True)
        season_shots_acc = pd.concat(shots_acc_dfs, ignore_index=True)

        # slow function should be awaited
        season_per = season_per.groupby("Player Name", as_index=False).agg(lambda x: list(set(x.dropna()))[0] if x.any() else None)
        season_shots_acc = season_shots_acc.groupby("Player Name", as_index=False).agg(lambda x: list(set(x.dropna()))[0] if x.any() else None)

        new_dfs["PER"] = season_per
        new_dfs["SACC"] = season_shots_acc
        new_dfs["PERH"] = season_per[["Player Name"] + dfs_dict["MH"]]
        new_dfs["PERV"] = season_per[["Player Name"] + dfs_dict["MV"]]
        new_dfs["SACCH"] = season_shots_acc[["Player Name"] + dfs_dict["MH"]]
        new_dfs["SACCV"] = season_shots_acc[["Player Name"] + dfs_dict["MV"]]

        return new_dfs

    async def fill_team_dict(self, updating_teams: List[str]) -> None:
        await asyncio.sleep(0)
        for team in updating_teams:
            filtered_inv = self.inventory_csv.loc[(self.inventory_csv["Home"] == team) | (self.inventory_csv["Visitor"] == team)]
            filtered_inv["Date"] = pd.to_datetime(filtered_inv["Date"], format="%m_%d_%Y")
            filtered_inv = filtered_inv.sort_values(by="Date")

            for _, match in filtered_inv.iterrows():
                HorV = "Home" if match["Home"] == team else "Visitor"
                date = match["Date"].strftime(format="%m_%d_%Y")
                match_path = os.path.join(self.tables_path, match["Home"], match["Visitor"], date)
                match_str = f"{match['Home']}_{match['Visitor']}_{date}"

                try:
                    final_table_path = os.path.join(match_path, HorV, "PFinalTable.csv")
                    final_table = pd.read_csv(final_table_path)

                    lineup_table_path = os.path.join(match_path, HorV, "LFinalTable.csv")
                    lineup_table = pd.read_csv(lineup_table_path)

                    Pevents_table_path = os.path.join(match_path, HorV, "PAllEvents.csv")
                    Pevents_table = pd.read_csv(Pevents_table_path)

                    Levents_table_path = os.path.join(match_path, HorV, "LAllEvents.csv")
                    Levents_table = pd.read_csv(Levents_table_path)

                    print(f"{match['Home']} VS {match['Visitor']} at {date} --> {HorV}")

                except FileNotFoundError:
                    print("Table not found!")
                    break

                # create team key if it doesn't exist on teams_dict
                if team not in self.teams_dict:
                    self.teams_dict[team] = {
                        "P": [],
                        "L": [],
                        "PE": [],
                        "LE": [],
                        "PH": [],
                        "PV": [],
                        "M": [],
                        "MH": [],
                        "MV": [],
                    }

                # dropping unneccessary columns
                try:
                    drops = [
                        "date", "game_type", "home/visitor",
                        "opponent", "OffRtg", "DefRtg",
                        "NetRtg", "global efficiency",
                        "quarter2 last 5min efficiency",
                        "quarter4 last 5min efficiency"
                    ]

                    final_table = final_table.drop(drops, axis=1)
                    final_table = final_table.drop(columns=final_table.filter(like="Unnamed").columns)
                except:
                    pass

                self.teams_dict[team]["P"].append(final_table)
                self.teams_dict[team]["L"].append(lineup_table)
                self.teams_dict[team]["PE"].append(Pevents_table)
                self.teams_dict[team]["LE"].append(Levents_table)
                self.teams_dict[team][f"P{HorV[0]}"].append(final_table)
                self.teams_dict[team]["M"].append(match_str)
                self.teams_dict[team][f"M{HorV[0]}"].append(match_str)

    async def team_report(self, team: str) -> None:
        await asyncio.sleep(0)
        team_report_path = os.path.join(self.reports_path, team)
        if not os.path.exists(team_report_path):
            os.makedirs(team_report_path)

        print(team, "started")

        try:
            try:
                team_data = await asyncio.create_task(self.measure_report(self.teams_dict[team]))
            except Exception as e:
                print(f"Error(report measuring): {e}")

            try:
                players_report = team_data["P"]
                lineup_report = team_data["L"]
                Pevents_report = team_data["PE"]
                Levents_report = team_data["LE"]
                Hplayers_report = team_data["PH"]
                Vplayers_report = team_data["PV"]
                PER_report = team_data["PER"]
                PERH_report = team_data["PERH"]
                PERV_report = team_data["PERV"]
                SACC_report = team_data["SACC"]
                SACCH_report = team_data["SACCH"]
                SACCV_report = team_data["SACCV"]

                players_path = os.path.join(team_report_path, "PSeasonalReport.csv")
                lineup_path = os.path.join(team_report_path, "LSeasonalReport.csv")
                Pevents_path = os.path.join(team_report_path, "PEventsSeasonalReport.csv")
                Levents_path = os.path.join(team_report_path, "LEventsSeasonalReport.csv")
                Hplayers_path = os.path.join(team_report_path, "PHSeasonalReport.csv")
                Vplayers_path = os.path.join(team_report_path, "PVSeasonalReport.csv")
                PER_path = os.path.join(team_report_path, "PERSeasonalReport.csv")
                PERH_path = os.path.join(team_report_path, "PERHSeasonalReport.csv")
                PERV_path = os.path.join(team_report_path, "PERVSeasonalReport.csv")
                SACC_path = os.path.join(team_report_path, "SACCSeasonalReport.csv")
                SACCH_path = os.path.join(team_report_path, "SACCHSeasonalReport.csv")
                SACCV_path = os.path.join(team_report_path, "SACCVSeasonalReport.csv")

                players_report.to_csv(players_path)
                lineup_report.to_csv(lineup_path)
                Pevents_report.to_csv(Pevents_path)
                Levents_report.to_csv(Levents_path)
                Hplayers_report.to_csv(Hplayers_path)
                Vplayers_report.to_csv(Vplayers_path)
                PER_report.to_csv(PER_path)
                PERH_report.to_csv(PERH_path)
                PERV_report.to_csv(PERV_path)
                SACC_report.to_csv(SACC_path)
                SACCH_report.to_csv(SACCH_path)
                SACCV_report.to_csv(SACCV_path)

                print(team, "ended")

            except Exception as e:
                print(f"Error(report saving): {e}")

        except Exception as e:
            print(f"Error: {e}")

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

        await self.fill_team_dict(updating_teams)

        teams_task = []
        for team in self.teams_dict:
            task = asyncio.create_task(self.team_report(team))
            teams_task.append(task)

        for chunk in self.chunk_tasks(teams_task, self.report_per_iter):
            _, _ = await asyncio.wait(chunk)


if __name__ == "__main__":
    # test code for updating some sample teams report
    for gender in ["men", "women"]:
        reporter = Reporter(gender, 25)
        row_path = os.path.join(reporter.data_path, "rows")
        added_sheets = os.listdir(row_path)
        asyncio.run(reporter.main(added_sheets))
