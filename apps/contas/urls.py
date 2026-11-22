from django.urls import path

from . import views

urlpatterns = [
    path("cadastrar-escola/", views.cadastro_escola, name="cadastro_escola"),
    path("entrar/", views.entrar, name="entrar"),
    path("sair/", views.sair, name="sair"),
    path("conta/senha/", views.trocar_senha, name="trocar_senha"),
    path("aluno/", views.aluno, name="aluno"),
    path("professor/", views.professor, name="professor"),
    path("coordenacao/", views.coordenacao, name="coordenacao"),
    path("coordenacao/usuarios/", views.coordenacao_usuarios, name="coordenacao_usuarios"),
    path("coordenacao/usuarios/<int:pk>/status/", views.alternar_status_usuario, name="coordenacao_usuario_status"),
    path("coordenacao/usuarios/<int:pk>/resetar-senha/", views.resetar_senha_usuario, name="coordenacao_usuario_resetar_senha"),
]
