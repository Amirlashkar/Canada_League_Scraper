from django.shortcuts import render, redirect
from django.http import JsonResponse
from scraper.tables_function import convert_min, data_showoff
from scraper.constants import show_table, lineup_show_table
from season_reporter import functions
from copy import copy
import pandas as pd
import os, json
import plotly.express as px
from plotly.offline import plot
from plotly.graph_objs import Figure


def analytics(request):
    # in case to check ajax requests
    body = str(request.body)

    # the user who is not an admin accessed analitycs url would be redirected to root url
    if "menORwomen" not in request.session:
        return redirect("is_superuser")

    render_dict = {}
    teams = sorted(os.listdir(request.session["reports_path"]))
    if ".DS_Store" in teams:
        teams.remove(".DS_Store")

    render_dict["teams"] = teams

    if "find-data" in request.POST:
        functions.reset_plots(request)

        team = request.session["team"] = request.POST["team"]
        team_path = os.path.join(request.session["reports_path"], team)
        PL = request.POST["pl"]

        data_path = os.path.join(team_path, f"{PL.upper()[0]}SeasonalReport.csv")
        if os.path.exists(data_path):
            table = pd.read_csv(data_path)

            per_path = os.path.join(team_path, f"PERSeasonalReport.csv")
            if os.path.exists(per_path):
                per_table = pd.read_csv(per_path)
                p_names = request.session["p_names"] = per_table["Player Name"].to_list()
                render_dict["p_names"] = p_names
            else:
                render_dict["no_plot"] = request.session["no_plot"] = True

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

            table = table.rename(columns={"minutes": "time"})

            # sorting players table alphabetically for the first time
            if PL == "Players":
                table = table.sort_values(by="Player Name", ascending=True)
                # tables needed for double bar chart plot
                if not render_dict.get("no_plot"):
                    htable = pd.read_csv(os.path.join(team_path, "PHSeasonalReport.csv"))
                    vtable = pd.read_csv(os.path.join(team_path, "PVSeasonalReport.csv"))
                    plot_div = functions.create_barchart_div(htable, vtable)
                    render_dict["pts_plot"] = request.session["pts_plot"] = plot_div

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

        else:
            render_dict["no_table"] = True

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

        if not request.session.get("no_plot"):
            render_dict["pts_plot"] = request.session["pts_plot"]
            render_dict["p_names"] = request.session["p_names"]

    elif "pperf_select" in body:
        team_path = os.path.join(request.session["reports_path"], request.session["team"])
        per_path = os.path.join(team_path, f"PERSeasonalReport.csv")
        sacc_path = os.path.join(team_path, f"SACCSeasonalReport.csv")
        per_table = pd.read_csv(per_path)
        sacc_table = pd.read_csv(sacc_path)

        body_dict = json.loads(request.body)
        per_plot_div = functions.create_linechart_div(per_table, "PER", body_dict["pperf_select"])
        sacc_plot_div = functions.create_linechart_div(sacc_table, "Shots Accuracy", body_dict["pperf_select"])

        return JsonResponse({"per_plot_div": per_plot_div, "sacc_plot_div": sacc_plot_div})

    elif "reset" in request.POST:
        functions.reset_plots(request)
        try:
            del request.session["table"]
            del request.session["selected_team"]
        except KeyError:
            pass

    return render(request, "sr_analytics.html", render_dict)


def events(request):
    if "menORwomen" not in request.session:
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
    if "menORwomen" not in request.session:
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
