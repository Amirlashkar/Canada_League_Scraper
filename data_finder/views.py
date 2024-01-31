from django.shortcuts import redirect, render
from scraper.functions import *
from scraper.tables_function import list_players, data_showoff
import pandas as pd
import numpy as np
import os


tables_path = os.path.join(os.getcwd(), "tables")
inventory_path = os.path.join(os.getcwd(), "data", "inventory.csv")
inventory_csv = pd.read_csv(inventory_path)


def is_superuser(request):
    # This functions checks if user is admin or not
    return render(
        request, "is_superuser.html", {"is_superuser": str(request.user.is_superuser)}
    )


def analytics(request):
    # the user who is not an admin accessed analitycs url would be redirected to root url
    if not request.user.is_superuser:
        return redirect("is_superuser")
    
    render_dict = {}
    # taking uniques of team list to show on dropdowns cause they are repeatitive
    render_dict["home_teams"] = np.unique(inventory_csv["Home"].to_list())
    render_dict["visitor_teams"] = np.unique(inventory_csv["Visitor"].to_list())
    # for the matter of user logging
    print(f"USER: {request.user.username}")
    # check if user directory exists ; if not creates it
    user_path = os.path.join(os.getcwd(), "users", request.user.username)
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    
    # conditions different buttons clicking
    if "find-dates" in request.POST:

        # saving selected teams on django sessions also
        home_team = request.session["home"] = request.POST["home-team"]
        visitor_team = request.session["visitor"] = request.POST["visitor-team"]

        # selected teams would be shown as static html tags after the condition button selected not as dropdowns
        render_dict["home"] = home_team
        render_dict["visitor"] = visitor_team

        # checking if selected match with specific home, visitor and date exists or not
        match_tables_path = os.path.join(tables_path, home_team, visitor_team)
        if os.path.exists(match_tables_path):
            matches_date = [
                # making date better-looking
                date.replace("_", "/") for date in os.listdir(match_tables_path)
            ]
            # at what dates two team played together
            render_dict["dates"] = matches_date
            # availables reset button
            render_dict["reset_available"] = True
        else:
            # this activates error massage tag on html which says: "No such match found on database"
            render_dict["no_dates"] = True

    elif "submit-match" in request.POST:
        # some lines are repeated thus comments are the same
        home = request.session["home"]
        visitor = request.session["visitor"]
        date = request.POST["date"].replace("/", "_")
        
        # getting selected data
        switch = "P" if request.POST["switch"] == "players" else "L"
        table_path = os.path.join(tables_path, home, visitor, date, f"{switch}FinalTable.csv")
        table = pd.read_csv(table_path)

        # some match tables may have extra column starting with Unnamed that we drop it
        try:
            # unneeded columns are also dropped (some are shown on other tags and some are empty)
            if switch == "P":
                table = table.drop(["date", "game_type", "home/visitor", "opponent"], axis=1)
            else:
                table = table.drop(["home/visitor", "opponent"], axis=1)

            table = table.drop(columns=table.filter(like="Unnamed").columns)
        except:
            pass


        # this function iterates over data and tries to summerize floats by two digits after floating-point and save them on new data
        data = table.to_numpy()
        data = data_showoff(data)
        
        # main content
        render_dict["next_rows"] = data
        # table headers
        render_dict["theaders"] = table.columns
        # this element controls visualization of some buttons
        render_dict["result"] = True

        home_team = request.session["home"]
        visitor_team = request.session["visitor"]
        render_dict["home"] = home_team
        render_dict["visitor"] = visitor_team
        render_dict["reset_available"] = True
        # needed for advertising lineup evaluation app
        render_dict["switch"] = switch

    # just checking reset button clicking is enough to reset all to first form
    elif "reset" in request.POST:
        # but in case of assurance we also delete session data
        del request.session["home"]
        del request.session["visitor"]

    return render(request, "analytics.html", render_dict)


def lineup_eval(request):
    if not request.user.is_superuser:
        return redirect("is_superuser")

    render_dict = {}
    render_dict["home_teams"] = np.unique(inventory_csv["Home"].to_list())
    render_dict["visitor_teams"] = np.unique(inventory_csv["Visitor"].to_list())
    
    if "find-dates" in request.POST:

        home_team = request.session["home"] = request.POST["home-team"]
        visitor_team = request.session["visitor"] = request.POST["visitor-team"]

        render_dict["home"] = home_team
        render_dict["visitor"] = visitor_team

        match_tables_path = os.path.join(tables_path, home_team, visitor_team)
        if os.path.exists(match_tables_path):
            matches_date = [
                date.replace("_", "/") for date in os.listdir(match_tables_path)
            ]
            render_dict["dates"] = matches_date
            render_dict["reset_available"] = True
        else:
            render_dict["no_dates"] = True

    elif "submit-match" in request.POST:

        home = request.session["home"]
        visitor = request.session["visitor"]
        date = request.session["date"] = request.POST["date"].replace("/", "_")

        filename = home + "_" + visitor + "_" + date + ".csv"
        file_path = os.path.join(os.path.dirname(inventory_path), filename)
        raw_data = pd.read_csv(file_path)
        HorV = "Home" if "Carleton" in home else "Visitor"
        players, _ = list_players(raw_data, 0, HorV)

        render_dict["players"] = request.session["players"] = players
        render_dict["home"] = home
        render_dict["visitor"] =visitor
        render_dict["selected_date"] = request.POST["date"]
        render_dict["reset_available"] = True

    elif "submit-lineup" in request.POST:
        
        home = request.session["home"]
        visitor = request.session["visitor"]
        date = request.session["date"]

        lineup_table_path = os.path.join(tables_path, home, visitor, date, "LFinalTable.csv")
        lineup_table = pd.read_csv(lineup_table_path)

        chosen_players = []
        for num in range(1, 6):
            chosen_players.append(request.POST[f"p{num}"])

        chosen_players = str(tuple(sorted(chosen_players)))
        table = lineup_table.loc[lineup_table["Lineup"] == chosen_players]
        if not table.empty:

            try:
                table = table.drop(["home/visitor", "opponent"], axis=1)
                table = table.drop(columns=table.filter(like="Unnamed").columns)
            except:
                pass
            
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
        except:
            pass

    return render(request, "lineup_eval.html", render_dict)
