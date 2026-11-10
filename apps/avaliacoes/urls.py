from django.urls import path

from . import views

urlpatterns = [
    path("coordenacao/ciclos/", views.ciclos, name="coordenacao_ciclos"),
    path("aluno/", views.pendencias, name="aluno"),
    path("aluno/avaliar/<int:vinculo_id>/", views.avaliar, name="aluno_avaliar"),
    path("aluno/obrigado/", views.obrigado, name="aluno_obrigado"),
]
