import pandas as pd
import numpy as np
import os, difflib

from tables_function import cal_eff, cal_rtg


class Reporter:

    def __init__(self) -> None:

        # defining static pathes
        self.tables_path = os.path.join(os.getcwd(), "tables")
        self.reports_path = os.path.join(os.getcwd(), "reports")

        self.teams_dict = {}

        # reports dir will be created if not exists
        if not os.path.exists(self.reports_path):
            os.makedirs(self.reports_path)

    def mix_similars(self, df:pd.DataFrame) -> pd.DataFrame:
        """
        some names are for one person but in different forms on df;
        this function makes them as one.
        df: dataframe with alternative names
        """

        players = df["Player Name"].to_list()
        # may need second iteration cause some strings are gradual to appeare their main_name
        for i in range(2):
            for ind, row in df.iterrows():

                playername = row["Player Name"]
                comparing_ls = players.copy()
                comparing_ls.remove(playername)

                found = difflib.get_close_matches(playername, comparing_ls, n=1, cutoff=0.0)[0]
                matcher = difflib.SequenceMatcher(None, playername, found)
                diff_ratio = matcher.ratio()

                if diff_ratio >= 0.70:
                    if len(playername) > len(found):
                        main_name = playername
                    else:
                        main_name = found
                    
                    df.loc[ind, "Player Name"] = main_name

            df = df.groupby(["Player Name"]).sum()
            df = df.reset_index()

        return df


    def measure_report(self, dfs_ls:list) -> pd.DataFrame:
        """
        the function sticks dataframes of a team from all season wide and sums up players statistic together and also adds new columns
        dfs_ls: list of an specific team dataframes from all over season
        """
        concat_df = pd.concat(dfs_ls)
        summed_df = concat_df.groupby(["Player Name"]).sum()
        summed_df = summed_df.reset_index()
        summed_df = self.mix_similars(summed_df)

        summed_df["Eff"] = summed_df.apply(lambda row: cal_eff(row["total off possession"],
                                                               row["total def possession"],
                                                               row["minutes"]), axis=1)

        summed_df["OffRtg"] = summed_df.apply(lambda row: cal_rtg(row["PtScored"],
                                                               row["total off possession"]), axis=1)

        summed_df["DefRtg"] = summed_df.apply(lambda row: cal_rtg(row["ptsconceded"],
                                                               row["total def possession"]), axis=1)

        summed_df["NetRtg"] = summed_df["OffRtg"] - summed_df["DefRtg"]
        
        return summed_df

    def report(self):

        existing_teams = os.listdir(self.tables_path)
        try:
            existing_teams.remove(".DS_Store")
        except:
            pass
        for home in existing_teams:
            home_path = os.path.join(self.tables_path, home)
            visitor_teams = os.listdir(home_path)
            try:
                visitor_teams.remove(".DS_Store")
            except:
                pass
            for visitor in visitor_teams:
                visitor_path = os.path.join(home_path, visitor)
                dates = os.listdir(visitor_path)
                try:
                    dates.remove(".DS_Store")
                except:
                    pass
                for date in dates:
                    final_table_path = os.path.join(home_path, visitor, date, "PFinalTable.csv")
                    final_table = pd.read_csv(final_table_path)
                    
                    # create team key if it doesn't exist on teams_dict
                    if "Carleton" not in self.teams_dict:
                        self.teams_dict["Carleton"] = []
                    
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

                    self.teams_dict["Carleton"].append(final_table)

        for team in self.teams_dict:
            
            team_report_path = os.path.join(self.reports_path, team)
            if not os.path.exists(team_report_path):
                os.makedirs(team_report_path)
            
            players_report = self.measure_report(self.teams_dict[team])
            players_report_path = os.path.join(team_report_path, "PSeasonalReport.csv")
            players_report.to_csv(players_report_path)

reporter = Reporter()
reporter.report()
