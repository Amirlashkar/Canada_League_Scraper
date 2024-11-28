"""website_core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from data_finder import views as dtf
from season_reporter import views as rpt

urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    path("", dtf.is_superuser, name="is_superuser"),
    path('logout/', LogoutView.as_view(next_page="is_superuser"), name='logout'),
    path("data_finder/", include("data_finder.urls")),
    path("update_selects/", dtf.update_selects),
    path("season/", include("season_reporter.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
