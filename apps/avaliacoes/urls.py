from django.urls import path

from . import views

urlpatterns = [
    path("coordenacao/questionarios/", views.questionarios, name="coordenacao_questionarios"),
    path("coordenacao/questionarios/<int:modelo_id>/", views.questionario_editar, name="coordenacao_questionario_editar"),
    path("coordenacao/questionarios/<int:modelo_id>/duplicar/", views.questionario_duplicar, name="coordenacao_questionario_duplicar"),
    path("coordenacao/questionarios/<int:modelo_id>/preview/", views.questionario_preview, name="coordenacao_questionario_preview"),
    path("coordenacao/ciclos/", views.ciclos, name="coordenacao_ciclos"),
    path("coordenacao/ciclos/<int:ciclo_id>/encerrar/", views.encerrar_ciclo, name="coordenacao_encerrar_ciclo"),
    path("coordenacao/ciclos/<int:ciclo_id>/publicar/", views.publicar, name="coordenacao_publicar_ciclo"),
    path("coordenacao/moderacao/<int:resposta_id>/", views.moderar_resposta, name="coordenacao_moderar_resposta"),
    path("aluno/", views.pendencias, name="aluno"),
    path("aluno/avaliar/<int:vinculo_id>/", views.avaliar, name="aluno_avaliar"),
    path("aluno/obrigado/", views.obrigado, name="aluno_obrigado"),
]
