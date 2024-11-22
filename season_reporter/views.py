from django.shortcuts import render, redirect
from scraper.tables_function import convert_min, data_showoff
from scraper.constants import show_table, lineup_show_table
from copy import copy
import pandas as pd
import os


def analytics(request):
    # the user who is not an admin accessed analitycs url would be redirected to root url
    if not request.user.is_superuser or "menORwomen" not in request.session:
        return redirect("is_superuser")

    render_dict = {}
    teams = sorted(os.listdir(request.session["reports_path"]))
    if ".DS_Store" in teams:
        teams.remove(".DS_Store")

    render_dict["teams"] = teams

    if "find-data" in request.POST:
        team = request.session["team"] = request.POST["team"]
        PL = request.POST["pl"]

        data_path = os.path.join(request.session["reports_path"], team, f"{PL.upper()[0]}SeasonalReport.csv")
        table = pd.read_csv(data_path)

        if PL == "Players":
            table = table.reindex(columns=show_table)
            # CAUTION: last 5min efficiencies should first become measured to be shown
            table = table.drop(columns=table.filter(like="last").columns)
        else:
            table = table.reindex(columns=lineup_show_table)

        try:
            table = table.drop(columns=table.filter(like="Unnamed").columns)
        except:
            pass

        # sorting players table alphabetically for the first time
        if PL == "Players":
            table = table.sort_values(by="Player Name", ascending=True)

        table = table.rename(columns={"minutes": "time"})
        data_ = copy(table)
        data_["time"] = data_.apply(lambda row: convert_min(row["time"]), axis=1)
        data = data_.to_numpy()
        data = data_showoff(data)

        request.session["table"] = table.to_dict()
        request.session["PL"] = PL

        render_dict["theaders"] = data_.columns
        render_dict["next_rows"] = data
        render_dict["result"] = True
        render_dict["events"] = True
        render_dict["selected_team"] = request.session["selected_team"] = team
        render_dict["PL"] = PL

    elif "events" in request.POST:
        return redirect("sr_events")

    elif "sort" in request.POST:
        table = request.session["table"]
        table = pd.DataFrame(table)
        selected_col = request.POST["sort"]

        data = table.sort_values(by=selected_col, ascending=False)
        data["time"] = data.apply(lambda row: convert_min(row["time"]), axis=1)
        data = data.to_numpy()
        data = data_showoff(data)

        render_dict["theaders"] = table.columns
        render_dict["next_rows"] = data
        render_dict["result"] = True
        render_dict["events"] = True
        render_dict["selected_col"] = selected_col
        render_dict["selected_team"] = request.session["selected_team"]
        render_dict["PL"] = request.session["PL"]

    elif "reset" in request.POST:
        try:
            del request.session["table"]
            del request.session["selected_team"]
        except KeyError:
            pass

    return render(request, "sr_analytics.html", render_dict)


def events(request):
    if not request.user.is_superuser or "menORwomen" not in request.session:
        return redirect("is_superuser")
    elif "home" not in request.session:
        return redirect("sr_analytics")

    render_dict = {}

    team = request.session["team"]
    PL = request.session["PL"]
    report_path = os.path.join(
        request.session["reports_path"],
        request.session["team"],
        f"{PL[0]}EventsSeasonalReport.csv",
    )

    report = pd.read_csv(report_path)
    try:
        report = report.drop(columns=report.filter(like="poss").columns)
    except:
        pass

    try:
        report = report.drop(columns=report.filter(like="Unnamed").columns)
    except:
        pass

    # sorting players table alphabetically for the first time
    if PL == "Players":
        report = report.sort_values(by="Player Name", ascending=True)

    data = report.to_numpy()
    data = data_showoff(data)

    request.session["report"] = report.to_dict()

    render_dict["theaders"] = ["#" + col if col not in ("Player Name", "Lineup") else col for col in report.columns]
    render_dict["next_rows"] = data
    render_dict["team"] = team
    render_dict["result"] = True

    if "back" in request.POST:
        return redirect("sr_analytics")

    elif "sort" in request.POST:
        report = request.session["report"]
        report = pd.DataFrame(report)
        selected_col = request.POST["sort"].replace("#", "")

        data = report.sort_values(by=selected_col, ascending=False)
        data = data.to_numpy()
        data = data_showoff(data)

        render_dict["reset_available"] = True
        render_dict["selected_col"] = "#" + selected_col

    return render(request, "sr_events.html", render_dict)

def lineup_eval(request):
    if not request.user.is_superuser or "menORwomen" not in request.session:
        return redirect("is_superuser")

    teams = sorted(os.listdir(request.session["reports_path"]))
    if ".DS_Store" in teams:
        teams.remove(".DS_Store")

    render_dict = {}
    render_dict["teams"] = teams

    if "find-data" in request.POST:
        selected_team = request.POST["team"]
        player_table_path = os.path.join(request.session["reports_path"], selected_team, "PSeasonalReport.csv")
        players = pd.read_csv(player_table_path)["Player Name"].to_list()

        render_dict["players"] = request.session["players"] = players
        render_dict["selected_team"] = request.session["selected_team"] = selected_team

    elif "submit-lineup" in request.POST:
        selected_team = request.session["selected_team"]
        lineup_table_path = os.path.join(request.session["reports_path"], selected_team, "LSeasonalReport.csv")
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
