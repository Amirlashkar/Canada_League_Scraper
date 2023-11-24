from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime
import pandas as pd
import os

inventory_path = os.path.join(os.getcwd(), "data", "inventory.csv")    
if not os.path.exists(inventory_path):
    df = pd.DataFrame(columns=["Follow Up Team", "Opponent Team", "Date"])
    df.to_csv(inventory_path)

def main_sheet(df_list:list, sheet_name:str) -> None:
    q = 1
    ls = []
    for i, df in enumerate(df_list):
        if type(df) == pd.DataFrame:
            quarter_row = pd.DataFrame([[f"Quarter {q}" for _ in range(6)]], columns=df.columns)
            print(df_list[i - 1])
            quarter_row["Home"] = [df_list[i - 1]]
            df = pd.concat([quarter_row, df], ignore_index=True)
            ls.append(df)
            q += 1

    df = pd.concat(ls, ignore_index=True)
    data_path = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    df.to_csv(os.path.join(data_path, f"{sheet_name}.csv"))


def inventory_sheet(followup_team, op_team, date):
    data = {
        "Follow Up Team": [followup_team],
        "Opponent Team": [op_team],
        "Date": [date],
    }
    inventory_df = pd.read_csv(inventory_path)
    adding_df = pd.DataFrame(data)
    df = pd.concat([inventory_df, adding_df], ignore_index=True)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.to_csv(inventory_path)

def check_inventory(followup_team, op_team, date) -> bool:
    df = pd.read_csv(inventory_path)
    expression = df[(df["Follow Up Team"] == followup_team) & (df["Opponent Team"] == op_team) & (df["Date"] == date)]

    # retrun true if there is no such data
    return len(expression) == 0
    

def finder(*, followup_team="Carleton", start_date, end_date):
    inventory_df = pd.read_csv(inventory_path)
    inventory_df["Date"] = pd.to_datetime(inventory_df["Date"])
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    filtered_df = inventory_df[(inventory_df["Follow Up Team"] == followup_team) & (inventory_df["Date"] > start_date_obj) & (inventory_df["Date"] <= end_date_obj)]

    if filtered_df.empty:
        return "Empty"
    else:
        return filtered_df

def zipper(user_path, zip_name, result_df):
    saving_path = os.path.join(user_path, zip_name)
    with ZipFile(saving_path, "w",
                compression=ZIP_DEFLATED,
                compresslevel=9) as zf:
        for index, row in result_df.iterrows():
            filename = row["Follow Up Team"] + "|" + row["Opponent Team"] + "|" + row["Date"].strftime("%Y-%m-%d") + ".csv"
            file_path = os.path.join(os.getcwd(), "data", filename)
            zf.write(file_path, arcname=filename)
    return saving_path
