import pandas as pd
import os, difflib, ast
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

    def find_valid_similar(self, playername, players_list):
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

    def mix_similars(self, df:pd.DataFrame, LP:str) -> pd.DataFrame:
        """
        some names are for one person but in different forms on df;
        this function makes them as one.
        df: dataframe with alternative names
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
                    print("#", end="", flush=True)
                    playername = row["Player Name"]
                    comparing_ls = players.copy()
                    comparing_ls.remove(playername)

                    main_name = self.find_valid_similar(playername, comparing_ls)
                    
                    if main_name != None:
                        df.loc[ind, "Player Name"] = main_name

            else:
                for ind, row in df.iterrows():
                    for i, player in enumerate(row["Lineup"]):
                        print("#", end="", flush=True)
                        comparing_ls = players.copy()
                        comparing_ls.remove(player)

                        main_name = self.find_valid_similar(player, comparing_ls)

                        if main_name != None:
                            list_version = list(df.loc[ind, "Lineup"])
                            list_version[i] = main_name
                            tuple_version = tuple(list_version)
                            if df.loc[ind, "Lineup"] != tuple_version:
                                df.loc[ind, "Lineup"] = tuple_version

            df = df.groupby(["Player Name" if LP == "P" else "Lineup"]).sum()
            df = df.reset_index()

        return df


    def measure_report(self, dfs_ls:list):
        """
        the function sticks dataframes of a team from all season wide and sums up players statistic together and also adds new columns
        dfs_ls: list of an specific team dataframes from all over season
        """
        for each in range(len(dfs_ls)):
            concat_df = pd.concat(dfs_ls[each])

            try:
                # CAUTION: last 5min efficiencies should be somehow filtered of "Not in the time" first and then 
                # you can get mean of all the columns to show for each player !!!
                summed_df = concat_df.groupby(["Player Name"]).sum()
            except:
                summed_df = concat_df.groupby(["Lineup"]).sum()

            summed_df = summed_df.reset_index()
            LP = "P" if each == 0 else "L"
            summed_df = self.mix_similars(summed_df, LP)

            summed_df["Eff"] = summed_df.apply(lambda row: cal_eff(row["total off possession"],
                                                                row["total def possession"],
                                                                row["minutes"]), axis=1)
            
            if LP == "P":
                ptsKey = "realPtsScored"
            else:
                ptsKey = "PtsScored"
            summed_df["OffRtg"] = summed_df.apply(lambda row: cal_rtg(row["realPtsScored"],
                                                                row["total off possession"]), axis=1)

            summed_df["DefRtg"] = summed_df.apply(lambda row: cal_rtg(row["PtsConceded"],
                                                                row["total def possession"]), axis=1)

            summed_df["NetRtg"] = summed_df["OffRtg"] - summed_df["DefRtg"]

            yield summed_df

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
                    for HorV in ("Home", "Visitor"):
                        teamname = home if HorV == "Home" else visitor
                        try:
                            final_table_path = os.path.join(home_path, visitor, date, HorV, "PFinalTable.csv")
                            final_table = pd.read_csv(final_table_path)

                            lineup_table_path = os.path.join(home_path, visitor, date, HorV, "LFinalTable.csv")
                            lineup_table = pd.read_csv(lineup_table_path)

                            print(f"{home} VS {visitor} at {date} --> {HorV}")

                        except FileNotFoundError:
                            print("Table not found!")
                            break
                        
                        # create team key if it doesn't exist on teams_dict
                        if teamname not in self.teams_dict:
                            self.teams_dict[teamname] = [[], []]
                        
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

                        self.teams_dict[teamname][0].append(final_table)
                        self.teams_dict[teamname][1].append(lineup_table)

        for team in self.teams_dict:
            team_report_path = os.path.join(self.reports_path, team)
            if not os.path.exists(team_report_path):
                os.makedirs(team_report_path)
            
            # players_report = self.measure_report(self.teams_dict[team])
            for i, df in enumerate(self.measure_report(self.teams_dict[team])):
                if i == 0:
                    players_report = df
                else:
                    lineup_report = df

            players_report_path = os.path.join(team_report_path, "PSeasonalReport.csv")
            lineup_report_path = os.path.join(team_report_path, "LSeasonalReport.csv")
            players_report.to_csv(players_report_path) ; lineup_report.to_csv(lineup_report_path)

reporter = Reporter()
reporter.report()
