from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.landing_page, name="home"),
    path("coordenacao/", include("apps.escolas.urls")),
    path("", include("apps.avaliacoes.urls")),
    path("", include("apps.contas.urls")),
]
