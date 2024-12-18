from copy import copy
from django.shortcuts import redirect, render
from django.contrib.auth import logout
from django.http import JsonResponse
from scraper.tables_function import convert_min, list_players, data_showoff
from scraper.constants import show_table, lineup_show_table
import pandas as pd
import numpy as np
import os


# tables_path = os.path.join(os.getcwd(), "tables")
# inventory_path = os.path.join(os.getcwd(), "tables", "inventory.csv")
# inventory_csv = pd.read_csv(inventory_path)


def is_superuser(request):
    # This functions checks if user is admin or not

    stuck_keys = "".join(list(request.POST.keys()))
    render_dict = {}
    if "data_finder" in request.POST or "season" in request.POST:
        menORwomen = request.session["menORwomen"] = request.POST["mw"]
        data_path = os.path.join(os.getcwd(), "data", menORwomen)
        tables_path = request.session["tables_path"] = os.path.join(data_path, "tables")
        inv_path = request.session["inv_path"] = os.path.join(tables_path, "inventory.csv")
        request.session["reports_path"] = os.path.join(data_path, "reports")
        request.session["inv_csv"] = pd.read_csv(inv_path).to_json()

        if "data_finder" in request.POST:
            render_dict["data_finder"] = True

        elif "season" in request.POST:
            render_dict["season"] = True

    elif "analytics" in stuck_keys or "lineup_eval" in stuck_keys:
        for k in request.POST:
            if "analytics" in k or "lineup_eval" in k:
                req = k
                break

        return redirect(req)

    return render(request, "is_superuser.html", render_dict)


def analytics(request):
    # the user who is not an admin accessed analitycs url would be redirected to root url
    # if not request.user.is_superuser or "menORwomen" not in request.session:
    #     return redirect("is_superuser")
    if "menORwomen" not in request.session:
        return redirect("is_superuser")

    render_dict = {}
    # taking uniques of team list to show on dropdowns cause they are repeatitive
    inventory_csv = pd.DataFrame(eval(request.session["inv_csv"]))
    render_dict["home_teams"] = sorted(np.unique(inventory_csv["Home"].to_list()))
    render_dict["visitor_teams"] = sorted(np.unique(inventory_csv["Visitor"].to_list()))
    # check if user directory exists ; if not creates it
    user_path = os.path.join(os.getcwd(), "users", request.user.username)
    if not os.path.exists(user_path):
        os.makedirs(user_path)

    # conditions different buttons clicking
    if "find-dates" in request.POST:
        # in case of update_selects functionality
        if "is_updated" in request.session:
            del request.session["is_updated"]

        # saving selected teams on django sessions also
        home_team = request.session["home"] = request.POST["home-team"]
        visitor_team = request.session["visitor"] = request.POST["visitor-team"]
        HV = render_dict["HV"] = request.session["HV"] = request.POST["hv"]

        # selected teams would be shown as static html tags after the condition button selected not as dropdowns
        render_dict["home"] = home_team
        render_dict["visitor"] = visitor_team
        # availables reset button
        render_dict["reset_available"] = True

        # checking if selected match with specific home, visitor and date exists or not
        match_tables_path = os.path.join(request.session["tables_path"], home_team, visitor_team)
        if os.path.exists(match_tables_path):
            matches_date = [
                # making date better-looking
                date.replace("_", "/") for date in os.listdir(match_tables_path)
            ]
            # at what dates two team played together
            render_dict["dates"] = matches_date
        else:
            # this activates error massage tag on html which says: "No such match found on database"
            render_dict["no_dates"] = True

    elif "submit-match" in request.POST:
        # some lines are repeated thus comments are the same
        home = request.session["home"]
        visitor = request.session["visitor"]
        date = request.session["selected_date"] = request.POST["date"].replace("/", "_")

        # getting selected data
        HV = render_dict["HV"] = request.session["HV"]
        PL = request.POST["pl"]
        table_path = os.path.join(request.session["tables_path"], home, visitor, date, HV, f"{PL.upper()[0]}FinalTable.csv")
        if os.path.exists(table_path):
            table = pd.read_csv(table_path)

            # choosing showing tables to user
            if PL == "Players":
                table = table.reindex(columns=show_table)
            else:
                table = table.reindex(columns=lineup_show_table)

            # this function iterates over data and tries to summerize floats by two digits after floating-point and save them on new data
            # sorting players table alphabetically for the first time
            if PL == "Players":
                table = table.sort_values(by="Player Name", ascending=True)

            table = table.rename(columns={"minutes": "time"})
            data_ = copy(table)
            data_["time"] = data_.apply(lambda row: convert_min(row["time"]), axis=1)
            data = data_.to_numpy()
            data = data_showoff(data)

            # session savings
            request.session["table"] = table.to_dict()
            request.session["PL"] = PL

            # main content
            render_dict["next_rows"] = data
            # table headers
            render_dict["theaders"] = data_.columns
            # this element controls visualization of some buttons
            render_dict["result"] = True

            # feed selected teams to template to show as static tag
            render_dict["home"] = home
            render_dict["visitor"] = visitor
            render_dict["selected_date"] = date

            # show reset button and also changing in some tags appearence
            render_dict["reset_available"] = True

            # needed for advertising lineup evaluation app
            render_dict["PL"] = PL

            # events link would be available
            render_dict["events"] = True

        else:
            hv_path = os.path.dirname(table_path)
            if not os.path.exists(hv_path):
                render_dict["no_side"] = True
            else:
                render_dict["no_dates"] = True

            render_dict["home"] = home
            render_dict["visitor"] = visitor
            render_dict["selected_date"] = date
            render_dict["reset_available"] = True

    elif "events" in request.POST:
        return redirect("df_events")

    elif "sort" in request.POST:
        home = request.session["home"]
        visitor = request.session["visitor"]
        date = request.session["selected_date"]

        table = request.session["table"]
        table = pd.DataFrame(table)
        selected_col = request.POST["sort"]

        data = table.sort_values(by=selected_col, ascending=False)
        data["time"] = data.apply(lambda row: convert_min(row["time"]), axis=1)
        data = data.to_numpy()
        data = data_showoff(data)

        render_dict["home"] = home
        render_dict["visitor"] = visitor
        render_dict["selected_date"] = date
        render_dict["theaders"] = table.columns
        render_dict["next_rows"] = data
        render_dict["reset_available"] = True
        render_dict["result"] = True
        render_dict["PL"] = request.session["PL"]
        render_dict["HV"] = request.session["HV"]
        render_dict["selected_col"] = selected_col
        render_dict["events"] = True

    # just checking reset button clicking is enough to reset all to first form
    elif "reset" in request.POST:
        # but in case of assurance we also delete session data
        try:
            del request.session["home"]
            del request.session["visitor"]
            del request.session["table"]
            del request.session["PL"]
            del request.session["HV"]
        except KeyError:
            pass

    return render(request, "df_analytics.html", render_dict)


def update_selects(request):
    default = None
    selected_type = request.GET["select_type"]
    selected_value = request.GET["selected_value"]
    changing_select = "Home" if selected_type == "visitor" else "Visitor"

    inventory_csv = pd.DataFrame(eval(request.session["inv_csv"]))
    if "is_updated" in request.session:
        del request.session["is_updated"]
        return JsonResponse({"options":[], "default": default})

    else:
        request.session["is_updated"] = True
        col = selected_type[0].upper() + selected_type[1:]
        filtered_df = inventory_csv.loc[inventory_csv[col] == selected_value]

        dynamic_ls = sorted(np.unique(filtered_df[changing_select]))
        options_ls = [{"id": i, "name": name} for i, name in enumerate(dynamic_ls)]

        return JsonResponse({"options": options_ls, "default": default})


def events(request):
    # if not request.user.is_superuser or "menORwomen" not in request.session:
    #     return redirect("is_superuser")
    if "menORwomen" not in request.session:
        return redirect("is_superuser")
    elif "home" not in request.session:
        return redirect("df_analytics")

    render_dict = {
        "home": request.session["home"],
        "visitor": request.session["visitor"],
        "selected_date": request.session["selected_date"].replace("_", "/"),
        "HV": request.session["HV"],
    }

    HV = request.session["HV"]
    PL = request.session["PL"]
    table_path = os.path.join(
        request.session["tables_path"],
        request.session["home"],
        request.session["visitor"],
        request.session["selected_date"],
        HV,
        f"{PL[0]}AllEvents.csv"
    )

    table = pd.read_csv(table_path)
    try:
        table = table.drop(columns=table.filter(like="poss").columns)
    except:
        pass

    try:
        table = table.drop(columns=table.filter(like="Unnamed").columns)
    except:
        pass

    # sorting players table alphabetically for the first time
    if PL == "Players":
        table = table.sort_values(by="Player Name", ascending=True)

    data = table.to_numpy()
    data = data_showoff(data)

    request.session["table"] = table.to_dict()

    render_dict["theaders"] = ["#" + col if col not in ("Player Name", "Lineup") else col for col in table.columns]
    render_dict["next_rows"] = data
    render_dict["result"] = True

    if "back" in request.POST:
        return redirect("df_analytics")

    elif "sort" in request.POST:
        table = request.session["table"]
        table = pd.DataFrame(table)
        selected_col = request.POST["sort"].replace("#", "")

        data = table.sort_values(by=selected_col, ascending=False)
        data = data.to_numpy()
        data = data_showoff(data)

        render_dict["reset_available"] = True
        render_dict["selected_col"] = "#" + selected_col

    return render(request, "df_events.html", render_dict)


def lineup_eval(request):
    # some lines are repeatitive so i won't write comments on them
    if "menORwomen" not in request.session:
        return redirect("is_superuser")

    render_dict = {}
    inventory_csv = pd.DataFrame(eval(request.session["inv_csv"]))
    render_dict["home_teams"] = sorted(np.unique(inventory_csv["Home"].to_list()))
    render_dict["visitor_teams"] = sorted(np.unique(inventory_csv["Visitor"].to_list()))

    if "find-dates" in request.POST:
        # in case of update_selects functionality
        if "is_updated" in request.session:
            del request.session["is_updated"]

        home_team = request.session["home"] = request.POST["home-team"]
        visitor_team = request.session["visitor"] = request.POST["visitor-team"]

        render_dict["home"] = home_team
        render_dict["visitor"] = visitor_team
        HV = render_dict["HV"] = request.session["HV"] = request.POST["hv"]

        match_tables_path = os.path.join(request.session["tables_path"], home_team, visitor_team)
        try:
            matches_date = os.listdir(match_tables_path)
            if ".DS_Store" in matches_date:
                matches_date.remove(".DS_Store")

            match_tables_path = os.path.join(match_tables_path, matches_date[0], HV, "LFinalTable.csv")

            # this if statement is for the case if the match folders exists but not the file cause data was invalid to make tables of it
            if os.path.exists(match_tables_path):
                matches_date = [
                    date.replace("_", "/") for date in matches_date
                ]
                render_dict["dates"] = matches_date
                render_dict["reset_available"] = True
            else:
                hv_path = os.path.dirname(match_tables_path)
                if not os.path.exists(hv_path):
                    render_dict["no_side"] = True
                else:
                    render_dict["no_dates"] = True

        # this exception is for the case if match folders totally doesn't exists
        except FileNotFoundError:
            render_dict["no_dates"] = True

    elif "submit-match" in request.POST:

        home = request.session["home"]
        visitor = request.session["visitor"]
        date = request.session["date"] = request.POST["date"].replace("/", "_")

        filename = home + "_" + visitor + "_" + date + ".csv"
        file_path = os.path.join(os.path.dirname(request.session["inv_path"]), "..", "rows", filename)
        raw_data = pd.read_csv(file_path)

        # declaring HV variable to get right list of player for Carleton ;
        # this line should be changed if data analyze is implemented on all teams
        HV = render_dict["HV"] = request.session["HV"]
        # a function to get players list out of first row on raw dataframe
        players, _ = list_players(raw_data, 0, HV)

        render_dict["players"] = request.session["players"] = players
        render_dict["home"] = home
        render_dict["visitor"] =visitor
        render_dict["selected_date"] = request.POST["date"]
        render_dict["reset_available"] = True

    elif "submit-lineup" in request.POST:
        home = request.session["home"]
        visitor = request.session["visitor"]
        date = request.session["date"]

        HV = render_dict["HV"] = request.session["HV"]
        lineup_table_path = os.path.join(request.session["tables_path"], home, visitor, date, HV, "LFinalTable.csv")
        lineup_table = pd.read_csv(lineup_table_path)

        # taking chosen players on template into a list
        chosen_players = []
        for num in range(1, 6):
            chosen_players.append(request.POST[f"p{num}"])

        # chosen players name needs to be sorted as lineups in saved tables are
        chosen_players = str(tuple(sorted(chosen_players)))
        # finding chosen lineup on table
        table = lineup_table.loc[lineup_table["Lineup"] == chosen_players]
        if not table.empty:
            table = table.reindex(columns=lineup_show_table)

            data = table.to_numpy()
            data = data_showoff(data)

            render_dict["theaders"] = table.columns
            render_dict["next_rows"] = data
            render_dict["home"] = home
            render_dict["visitor"] = visitor
            render_dict["selected_date"] = date
            render_dict["players"] = request.session["players"]
            render_dict["reset_available"] = True
            render_dict["result"] = True

        else:
            render_dict["home"] = home
            render_dict["visitor"] = visitor
            render_dict["selected_date"] = date
            render_dict["players"] = request.session["players"]
            render_dict["reset_available"] = True
            render_dict["no_lineup"] = True

    elif "reset" in request.POST:
        try:
            del request.session["home"]
            del request.session["visitor"]
            del request.session["date"]
            del request.session["HV"]
        except:
            pass

    return render(request, "df_lineup_eval.html", render_dict)
