from django.urls import path

from . import views

urlpatterns = [
    path("turmas/", views.turmas, name="coordenacao_turmas"),
    path("turmas/<int:pk>/remover/", views.remover_turma, name="remover_turma"),
    path("disciplinas/", views.disciplinas, name="coordenacao_disciplinas"),
    path(
        "disciplinas/<int:pk>/remover/",
        views.remover_disciplina,
        name="remover_disciplina",
    ),
    path("professores/", views.professores, name="coordenacao_professores"),
    path(
        "professores/importar/",
        views.importar_professores_csv,
        name="importar_professores",
    ),
    path("alunos/", views.alunos, name="coordenacao_alunos"),
    path("alunos/importar/", views.importar_alunos_csv, name="importar_alunos"),
    path("vinculos/", views.vinculos, name="coordenacao_vinculos"),
    path("vinculos/<int:pk>/remover/", views.remover_vinculo, name="remover_vinculo"),
    path(
        "importacao/credenciais.csv",
        views.download_importacao,
        name="download_importacao",
    ),
]
