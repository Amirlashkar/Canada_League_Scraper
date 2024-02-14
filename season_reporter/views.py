from django.shortcuts import render, redirect
from scraper.tables_function import data_showoff
from scraper.constants import show_table, lineup_show_table
import pandas as pd
import os

reports_path = os.path.join(os.getcwd(), "reports")

def report_render(request):
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
        switch = "P" if request.POST["switch"] == "players" else "L"
        
        data_path = os.path.join(reports_path, team, f"{switch[0].upper()}SeasonalReport.csv")
        if os.path.exists(data_path):

            table = pd.read_csv(data_path)
            if switch[0] == "P":
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

            render_dict["theaders"] = table.columns
            render_dict["next_rows"] = data
            render_dict["result"] = True
        else:
            render_dict["no_data"] = True

    return render(request, "season_reporter.html", render_dict)
