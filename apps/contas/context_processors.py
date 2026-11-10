from urllib.parse import urlparse

from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Usuario

DASHBOARD_POR_PAPEL = {
    Usuario.Role.ALUNO: "aluno",
    Usuario.Role.PROFESSOR: "professor",
    Usuario.Role.COORDENACAO: "coordenacao",
}


def navegacao(request):
    if not request.user.is_authenticated:
        fallback = reverse("home")
    else:
        fallback = reverse(DASHBOARD_POR_PAPEL[request.user.role])

    referer = request.META.get("HTTP_REFERER", "")
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        referer_path = urlparse(referer).path
        if referer_path and referer_path != request.path:
            return {"voltar_url": referer}
    return {"voltar_url": fallback}
