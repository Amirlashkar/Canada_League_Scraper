from django.shortcuts import render
from django.utils.text import slugify
from django.http import FileResponse
from scraper.functions import *
from scraper.tables_function import list_players
import time, os, ast
import pandas as pd
import numpy as np


tables_path = os.path.join(os.getcwd(), "tables")
inventory_path = os.path.join(os.getcwd(), "data", "inventory.csv")
inventory_csv = pd.read_csv(inventory_path)

def is_superuser(request):
    return render(
        request, "is_superuser.html", {
            "is_superuser": str(request.user.is_superuser)}
    )


def analytics(request):
    render_dict = {}
    render_dict["home_teams"] = np.unique(inventory_csv["Home"].to_list())
    render_dict["visitor_teams"] = np.unique(inventory_csv["Visitor"].to_list())
    print(f"USER: {request.user.username}")
    user_path = os.path.join(os.getcwd(), "users", request.user.username)
    if not os.path.exists(user_path):
        os.makedirs(user_path)

    if "find" in request.POST:
        month = int(request.POST['match-month'])
        day = int(request.POST['match-day'])
        year = request.POST['match-year']
        match_date = f"{month:02d}" + "_" + f"{day:02d}" + "_" + year
        home_team = request.POST["home-team"]
        visitor_team = request.POST["visitor-team"]
        match_tables_path = os.path.join(os.getcwd(), "tables", home_team, visitor_team, match_date)
        
        table_existance = find_final_tables(home_team, visitor_team, match_date)
        if table_existance != "Empty":
            zip_name = f"{slugify(home_team)}V{slugify(visitor_team)}On{slugify(match_date)}_{int(time.time())}.zip"
            saving_path = zipper(user_path, zip_name, match_tables_path)
            request.session["file_path"] = saving_path
            render_dict["file_ready"] = True
    elif "download" in request.POST:
        response = FileResponse(open(request.session["file_path"], "rb"))
        return response

    return render(request, "analytics.html", render_dict)


def lineup_eval(request):
    render_dict = {"phase": ""}
    render_dict["home_teams"] = np.unique(inventory_csv["Home"].to_list())
    render_dict["visitor_teams"] = np.unique(inventory_csv["Visitor"].to_list())

    try:
        render_dict["phase"] = request.session["phase"]
    except KeyError:
        render_dict["phase"] = "team_selection"

    if render_dict["phase"] == "team_selection":
        if "find" in request.POST:
            home_team = request.POST["home-team"]
            visitor_team = request.POST["visitor-team"]
            month = int(request.POST['match-month'])
            day = int(request.POST['match-day'])
            year = request.POST['match-year']
            match_date = f"{month:02d}" + "_" + f"{day:02d}" + "_" + year

            request.session["home_team"] = home_team
            request.session["visitor_team"] = visitor_team
            request.session["match_date"] = match_date

            table_existance = find_final_tables(home_team, visitor_team, match_date)
            if table_existance == "Empty":
                render_dict["result"] = table_existance
            else:
                render_dict["phase"] = "lineup_selection"
                request.session["phase"] = "lineup_selection"

                filename = home_team + "_" + visitor_team + "_" + match_date + ".csv"
                file_path = os.path.join(os.path.dirname(inventory_path), filename)
                raw_data = pd.read_csv(file_path)
                HorV = "Home" if "Carleton" in home_team else "Visitor"
                players, _ = list_players(raw_data, 0, HorV)
                render_dict["players"] = players
    else:
        if "back" in request.POST:
            del request.session["phase"]
            render_dict["phase"] = "team_selection"
        elif "eval" in request.POST:
            home_team = request.session["home_team"]
            visitor_team = request.session["visitor_team"]
            match_date = request.session["match_date"]
            lineup_table_path = os.path.join(tables_path, home_team, visitor_team, match_date, "LFinalTable.csv")
            lineup_table = pd.read_csv(lineup_table_path)

            chosen_players = []
            for num in range(1, 6):
                chosen_players.append(request.POST[f"p{num}"])

            chosen_players = str(tuple(sorted(chosen_players)))
            row = lineup_table.loc[lineup_table["Lineup"] == chosen_players]


    return render(request, "lineup_eval.html", render_dict)
