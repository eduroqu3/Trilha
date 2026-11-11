from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .decorators import papel_requerido
from .forms import CadastroEscolaForm, ContaPasswordChangeForm, LoginForm
from .models import Usuario

CADASTRO_LIMITE = 5
CADASTRO_JANELA = 15 * 60


def _ip(request):
    return request.META.get("REMOTE_ADDR", "unknown")


def cadastro_escola(request):
    chave = f"cadastro-escola:{_ip(request)}"
    bloqueado = cache.get(chave, 0) >= CADASTRO_LIMITE
    form = CadastroEscolaForm(request.POST or None)
    if request.method == "POST":
        if bloqueado:
            form.add_error(None, "Aguarde alguns minutos antes de tentar novamente.")
        elif form.is_valid() and not form.cleaned_data.get("website"):
            try:
                with transaction.atomic():
                    usuario = form.save()
            except IntegrityError:
                form.add_error(
                    None, "Não foi possível concluir o cadastro agora. Tente novamente."
                )
            else:
                cache.delete(chave)
                login(request, usuario, backend="apps.contas.backends.EmailBackend")
                return redirect("coordenacao")
        if not bloqueado:
            cache.set(chave, cache.get(chave, 0) + 1, CADASTRO_JANELA)
    return render(
        request, "contas/cadastro_escola.html", {"form": form, "bloqueado": bloqueado}
    )


def _next_url(request):
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return ""


def entrar(request):
    next_url = _next_url(request)
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["senha"],
        )
        if user is not None:
            login(request, user)
            return redirect(next_url or user_dashboard(user))
        form.add_error(
            None,
            "Não foi possível entrar com esses dados. Confira e-mail e senha e tente novamente.",
        )
    return render(request, "contas/entrar.html", {"form": form, "next": next_url})


def user_dashboard(user):
    return {
        Usuario.Role.ALUNO: "aluno",
        Usuario.Role.PROFESSOR: "professor",
        Usuario.Role.COORDENACAO: "coordenacao",
    }[user.role]


def sair(request):
    if request.method != "POST":
        return redirect("home")
    logout(request)
    messages.success(request, "Você saiu com segurança.")
    return redirect("entrar")


@login_required
def trocar_senha(request):
    form = ContaPasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sua senha foi atualizada.")
        return redirect(user_dashboard(request.user))
    return render(request, "contas/trocar_senha.html", {"form": form})


def _painel(request, papel, titulo):
    return render(request, "painel/dashboard.html", {"titulo": titulo, "papel": papel})


@papel_requerido(Usuario.Role.ALUNO)
def aluno(request):
    return _painel(request, "aluno", "Espaço do estudante")


@papel_requerido(Usuario.Role.PROFESSOR)
def professor(request):
    from apps.avaliacoes.models import CicloAvaliacao, RespostaTexto, ResumoVinculo
    from apps.escolas.models import Vinculo

    vinculo_ids = Vinculo.objects.para_usuario(request.user).filter(
        professor_id=request.user.pk
    ).values_list("pk", flat=True)
    resumos = ResumoVinculo.objects.para_usuario(request.user).select_related(
        "ciclo", "vinculo__turma", "vinculo__disciplina"
    ).filter(
        ciclo__status=CicloAvaliacao.Status.PUBLICADO,
        vinculo__in=vinculo_ids,
    )
    resultados = []
    for resumo in resumos:
        vinculo = resumo.vinculo
        comentarios = list(
            RespostaTexto.objects.filter(
                avaliacao__ciclo=resumo.ciclo,
                avaliacao__vinculo=resumo.vinculo_id,
                status_moderacao=RespostaTexto.StatusModeracao.APROVADO,
            )
            .exclude(texto="")
            .order_by("?")
            .values_list("texto", flat=True)
        )
        medias = [
            {
                "dimensao": dimensao,
                "media": media,
                "largura": round(float(media) * 20),
            }
            for dimensao, media in resumo.medias_por_dimensao.items()
        ]
        resultados.append(
            {
                "ciclo": resumo.ciclo,
                "vinculo": vinculo,
                "medias": medias,
                "comentarios": comentarios,
            }
        )
    return render(
        request,
        "painel/professor.html",
        {"titulo": "Espaço do professor", "papel": "professor", "resultados": resultados},
    )


@papel_requerido(Usuario.Role.COORDENACAO)
def coordenacao(request):
    return _painel(request, "coordenacao", "Espaço da coordenação")
