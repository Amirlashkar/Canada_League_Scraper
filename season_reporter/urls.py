from django.urls import path
from season_reporter import views

urlpatterns = [
    path("analytics/", views.analytics, name="sr_analytics"),
    path("lineup_eval/", views.lineup_eval, name="sr_lineup_eval"),
    path("events/", views.events, name="sr_events"),
]
