from django.shortcuts import render
from django.utils.text import slugify
from django.http import FileResponse
from scraper.functions import *
import time
import os


def is_superuser(request):
    return render(
        request, "is_superuser.html", {"is_superuser": str(request.user.is_superuser)}
    )


def data_finder(request):
    render_dict = {}
    print(f"USER: {request.user.username}")
    user_path = os.path.join(os.getcwd(), "users", request.user.username)
    if not os.path.exists(user_path):
        os.makedirs(user_path)

    if "search" in request.POST:
        start_date = (
            request.POST["start-year"]
            + "-"
            + request.POST["start-month"]
            + "-"
            + request.POST["start-day"]
        )
        end_date = (
            request.POST["end-year"]
            + "-"
            + request.POST["end-month"]
            + "-"
            + request.POST["end-day"]
        )
        result = finder("Carleton", start_date=start_date, end_date=end_date)
        if type(result) == str:
            render_dict["result"] = "Empty"
        else:
            zip_name = f"{slugify(start_date)}-{end_date}|{int(time.time())}.zip"
            saving_path = zipper(user_path, zip_name, result)
            request.session["file_path"] = saving_path
            render_dict["file_ready"] = "1"
    elif "download" in request.POST:
        response = FileResponse(open(request.session["file_path"], "rb"))
        return response

    return render(request, "data_finder.html", render_dict)
