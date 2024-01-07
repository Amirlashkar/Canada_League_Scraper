from tables_function import *
import os


class Converter:
    def __init__(self):
        self.data_path = os.path.join(os.getcwd(), "data")
        self.tables_path = os.path.join(os.getcwd(), "tables")
        self.custom_min = 1

    def check_match_dir(self, home: str, visitor: str, date: str):
        match_dir = os.path.join(self.tables_path, home, visitor, date)
        if not os.path.exists(match_dir):
            os.makedirs(match_dir)

    def data2tables(self):
        files = os.listdir(self.data_path)
        files.remove("inventory.csv")
        for file in files:
            if "Carleton" in file:
                print(file)
                splitted_name = file.split(".")[0]
                splitted_name = splitted_name.split("_")
                home = splitted_name[0]
                visitor = splitted_name[1]
                date = f"{splitted_name[2]}_{splitted_name[3]}_{splitted_name[4]}"
                match_dir = os.path.join(self.tables_path, home, visitor, date)
                HorV = "Home" if home == "Carleton" else "Visitor"
                self.check_match_dir(home, visitor, date)

                raw_df = provide_data(home, visitor, date)
                raw_df = initial_edit(raw_df)

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
                    ) = main_loop(raw_df, HorV, self.custom_min)

                    eff_df = create_eff_df(cusMin_df, eff_columns, self.custom_min)
                    pfinal_table = create_pfinal_df(
                        raw_df,
                        HorV,
                        events_df,
                        time_score_df,
                        events_df5min,
                        time_score_df5min,
                    )
                    lfinal_table = create_lfinal_df(
                        raw_df, HorV, lineup_time_score_df, lineup_event_df
                    )

                    cusMin_df.to_csv(os.path.join(match_dir, "CustomMinuteEvents.csv"))
                    events_df.to_csv(os.path.join(match_dir, "PAllEvents.csv"))
                    lineup_event_df.to_csv(os.path.join(match_dir, "LAllEvents.csv"))
                    time_score_df.to_csv(os.path.join(match_dir, "PTimeScore.csv"))
                    lineup_time_score_df.to_csv(
                        os.path.join(match_dir, "LTimeScore.csv")
                    )
                    events_df5min.to_csv(os.path.join(match_dir, "5MinEvents.csv"))
                    time_score_df5min.to_csv(
                        os.path.join(match_dir, "5MinTimeScore.csv")
                    )
                    eff_df.to_csv(os.path.join(match_dir, "Effectiveness.csv"))
                    pfinal_table.to_csv(os.path.join(match_dir, "PFinalTable.csv"))
                    lfinal_table.to_csv(os.path.join(match_dir, "LFinalTable.csv"))

                except Exception as e:
                    print(f"error: {e}")
                    continue


conv = Converter()
conv.data2tables()
