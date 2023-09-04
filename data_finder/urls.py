from django.urls import path
from data_finder import views

urlpatterns = [
    path("", views.is_superuser),
    path("data_finder/", views.data_finder),
]