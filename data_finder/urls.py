from django.urls import path
from data_finder import views

urlpatterns = [
    path("analytics/", views.analytics, name="df_analytics"),
    path("lineup_eval/", views.lineup_eval, name="df_lineup_eval"),
]
