from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing_page, name="home"),
    path("manus-routes.json", views.route_manifest, name="route-manifest"),
]
