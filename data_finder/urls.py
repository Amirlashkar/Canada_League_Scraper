from django.urls import path
from data_finder import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("", views.is_superuser, name="is_superuser"),
    path("analytics/", views.analytics, name="analytics"),
    path("lineup_eval/", views.lineup_eval, name="lineup_eval"),
    path('logout/', LogoutView.as_view(next_page="is_superuser"), name='logout'),
]
