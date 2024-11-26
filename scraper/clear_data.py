import os
import pandas as pd


data_directory = os.path.join(os.getcwd(), "data")

def contains_csv(directory):
    """
    Check if a directory or its subdirectories contain any .csv files.
    """
    for dirpath, _, filenames in os.walk(directory):
        for file in filenames:
            if file.endswith('.csv'):
                return True
    return False

def delete_non_csv_dirs(directory):
    """
    Recursively deletes directories that do not contain any .csv files.
    """
    for entry in os.listdir(directory):
        entry_path = os.path.join(directory, entry)
        if os.path.isdir(entry_path):
            # Recursively check the subdirectory
            delete_non_csv_dirs(entry_path)
            # If the directory is now empty, remove it
            if not os.listdir(entry_path) and not contains_csv(entry_path):
                os.rmdir(entry_path)
                print(f"Deleted empty directory: {entry_path}")

def edit_inv():
    for gender in ["men", "women"]:
        inv_path = os.path.join(data_directory, gender, "tables", "inventory.csv")
        df = pd.read_csv(inv_path)

        new_inv = pd.DataFrame(columns=df.columns)
        for i, row in df.iterrows():
            path = os.path.join(os.path.dirname(inv_path), row["Home"], row["Visitor"])
            if os.path.exists(path):
                adding_df = pd.DataFrame(data={
                    "Home": row["Home"],
                    "Visitor": row["Visitor"],
                    "Date": row["Date"],
                }, index=[0])

                new_inv = pd.concat([new_inv, adding_df], ignore_index=True)

        new_inv = new_inv.loc[:, ~new_inv.columns.str.contains("^Unnamed")]
        new_inv.to_csv(inv_path)

data_directory = os.path.join(os.getcwd(), "data")
delete_non_csv_dirs(data_directory)
edit_inv()
