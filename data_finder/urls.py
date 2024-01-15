from django.urls import path
from data_finder import views

urlpatterns = [
    path("", views.is_superuser),
    path("analytics/", views.analytics),
    path("lineup_eval/", views.lineup_eval),
]
