from django.urls import path

from . import views

urlpatterns = [
    path("coordenacao/ciclos/", views.ciclos, name="coordenacao_ciclos"),
    path(
        "coordenacao/ciclos/<int:ciclo_id>/encerrar/",
        views.encerrar_ciclo,
        name="coordenacao_encerrar_ciclo",
    ),
    path(
        "coordenacao/ciclos/<int:ciclo_id>/publicar/",
        views.publicar,
        name="coordenacao_publicar_ciclo",
    ),
    path(
        "coordenacao/moderacao/<int:resposta_id>/",
        views.moderar_resposta,
        name="coordenacao_moderar_resposta",
    ),
    path("aluno/", views.pendencias, name="aluno"),
    path("aluno/avaliar/<int:vinculo_id>/", views.avaliar, name="aluno_avaliar"),
    path("aluno/obrigado/", views.obrigado, name="aluno_obrigado"),
]
