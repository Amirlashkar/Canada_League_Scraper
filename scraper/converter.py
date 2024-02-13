from tables_function import *
import os, asyncio


class Converter:

    def __init__(self) -> None:
        self.data_path = os.path.join(os.getcwd(), "data")
        self.tables_path = os.path.join(os.getcwd(), "tables")
        self.custom_min = 1

    def check_match_dir(self, home: str, visitor: str, date: str, HorV:str):
        match_dir = os.path.join(self.tables_path, home, visitor, date, HorV)
        if not os.path.exists(match_dir):
            os.makedirs(match_dir)

    async def data2table(self, filename):
        invalids = 0
        for HorV in ("Home", "Visitor"):
            await asyncio.sleep(0)
            # if "Carleton" in filename:
            print(filename, "--->", HorV)
            splitted_name = filename.replace(".csv", "")
            splitted_name = splitted_name.split("_")
            home = splitted_name[0]
            visitor = splitted_name[1]
            date = f"{splitted_name[2]}_{splitted_name[3]}_{splitted_name[4]}"
            match_dir = os.path.join(self.tables_path, home, visitor, date, HorV)
            # HorV = "Home" if home == "Carleton" else "Visitor"
            self.check_match_dir(home, visitor, date, HorV)

            raw_df = provide_data(home, visitor, date)
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
                ) = await main_loop(raw_df, HorV, self.custom_min)

            except ValueError:
                invalids += 1
                print("Invalid substitution data!")
                continue
            
            except IndexError:
                invalids += 1
                print("Empty Dataframe!")
                continue

            eff_dict = create_eff_df(cusMin_df, eff_columns, self.custom_min)
            eff_df = pd.DataFrame(eff_dict)
            pfinal_table = create_pfinal_df(
                raw_df,
                HorV,
                date,
                events_df,
                time_score_df,
                events_df5min,
                time_score_df5min,
            )
            
            lfinal_table = create_lfinal_df(
                raw_df, HorV, date, lineup_time_score_df, lineup_event_df
            )
            lfinal_table = pd.DataFrame(lfinal_table)
            
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

    def get_tasks(self):
        files = os.listdir(self.data_path)
        files.remove("inventory.csv")
        files.remove(".DS_Store")
        tasks = []
        for file in files:
            tasks.append(self.data2table(file))

        return tasks

    async def convert(self):
        tasks = self.get_tasks()
        invalids = await asyncio.gather(*tasks)
        print(sum(list(invalids)))
        

conv = Converter()
asyncio.run(conv.convert())
