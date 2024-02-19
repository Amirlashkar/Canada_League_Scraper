from django.shortcuts import render, redirect
from scraper.tables_function import data_showoff
from scraper.constants import show_table, lineup_show_table
import pandas as pd
import os

reports_path = os.path.join(os.getcwd(), "reports")

def analytics(request):
    # the user who is not an admin accessed analitycs url would be redirected to root url
    if not request.user.is_superuser:
        return redirect("is_superuser")

    render_dict = {}
    teams = os.listdir(reports_path)
    if ".DS_Store" in teams:
        teams.remove(".DS_Store")

    render_dict["teams"] = teams

    if "find-data" in request.POST:
        team = request.POST["team"]
        switch = request.POST["switch"]

        data_path = os.path.join(reports_path, team, f"{switch.upper()[0]}SeasonalReport.csv")
        table = pd.read_csv(data_path)

        if switch == "players":
            table = table.reindex(columns=show_table)
            # CAUTION: last 5min efficiencies should first become measured to be shown
            table = table.drop(columns=table.filter(like="last").columns)
        else:
            table = table.reindex(columns=lineup_show_table)

        try:
            table = table.drop(columns=table.filter(like="Unnamed").columns)
        except:
            pass
        
        data = table.to_numpy()
        data = data_showoff(data)
 
        request.session["table"] = table.to_dict()

        render_dict["theaders"] = table.columns
        render_dict["next_rows"] = data
        render_dict["result"] = True
        render_dict["selected_team"] = request.session["selected_team"] = team

    elif "sort" in request.POST:
        table = request.session["table"]
        table = pd.DataFrame(table)
        selected_col = request.POST["sort"]

        data = table.sort_values(by=selected_col, ascending=False)
        data = data.to_numpy()
        data = data_showoff(data)

        render_dict["theaders"] = table.columns
        render_dict["next_rows"] = data
        render_dict["result"] = True
        render_dict["selected_col"] = selected_col
        render_dict["selected_team"] = request.session["selected_team"]

    elif "reset" in request.POST:
        try:
            del request.session["table"]
            del request.session["selected_team"]
        except KeyError:
            pass
    
    return render(request, "sr_analytics.html", render_dict)


def lineup_eval(request):
    if not request.user.is_superuser:
        return redirect("is_superuser")

    teams = os.listdir(reports_path)
    if ".DS_Store" in teams:
        teams.remove(".DS_Store")
    
    render_dict = {}
    render_dict["teams"] = teams
    
    if "find-data" in request.POST:
        selected_team = request.POST["team"]
        player_table_path = os.path.join(reports_path, selected_team, "PSeasonalReport.csv")
        players = pd.read_csv(player_table_path)["Player Name"].to_list()

        render_dict["players"] = request.session["players"] = players
        render_dict["selected_team"] = request.session["selected_team"] = selected_team
    
    elif "submit-lineup" in request.POST:
        selected_team = request.session["selected_team"]
        lineup_table_path = os.path.join(reports_path, selected_team, "LSeasonalReport.csv")
        lineup_table = pd.read_csv(lineup_table_path)

        chosen_players = []
        for num in range(1, 6):
            chosen_players.append(request.POST[f"p{num}"])
        
        chosen_players = str(tuple(sorted(chosen_players)))
        table = lineup_table.loc[lineup_table["Lineup"] == chosen_players]
        if not table.empty:
            table = table.reindex(columns=lineup_show_table)

            data = table.to_numpy()
            data = data_showoff(data)

            render_dict["theaders"] = table.columns
            render_dict["next_rows"] = data
            render_dict["result"] = True

        else:
            render_dict["no_lineup"] = True

    elif "reset" in request.POST:
        del request.session["selected_team"]
        del request.session["players"]

    return render(request, "sr_lineup_eval.html", render_dict)
