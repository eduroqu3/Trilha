from django.shortcuts import redirect
from django.urls import reverse


class TrocaObrigatoriaSenhaMiddleware:
    """
    Se o usuário estiver autenticado e com precisa_trocar_senha=True,
    redireciona qualquer requisição interna para a página de troca de senha,
    permitindo apenas trocar a senha, efetuar logout ou carregar arquivos estáticos.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and getattr(request.user, "precisa_trocar_senha", False):
            rotas_permitidas = {
                reverse("trocar_senha"),
                reverse("sair"),
            }
            if request.path not in rotas_permitidas and not request.path.startswith("/static/"):
                return redirect("trocar_senha")
        return self.get_response(request)
