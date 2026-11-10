from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.contas.decorators import papel_requerido
from apps.contas.models import Usuario
from apps.escolas.models import Matricula, Vinculo

from .forms import AvaliacaoForm, CicloAvaliacaoForm
from .models import (
    Avaliacao,
    CicloAvaliacao,
    Participacao,
    Pergunta,
    RespostaEscala,
    RespostaTexto,
)
from .services import criar_ciclo_com_questionario

COORDENACAO = Usuario.Role.COORDENACAO
ALUNO = Usuario.Role.ALUNO


def _ciclo_aberto(user):
    return (
        CicloAvaliacao.objects.para_usuario(user)
        .filter(status=CicloAvaliacao.Status.ABERTO)
        .first()
    )


@papel_requerido(COORDENACAO)
def ciclos(request):
    form = CicloAvaliacaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            criar_ciclo_com_questionario(request.user.escola, form.cleaned_data["nome"])
        except IntegrityError:
            form.add_error(
                None,
                "Já existe um ciclo não publicado para esta escola. Conclua esse ciclo antes de abrir outro.",
            )
        else:
            messages.success(request, "Ciclo aberto com questionário padrão.")
            return redirect("coordenacao_ciclos")
    return render(
        request,
        "coordenacao/ciclos.html",
        {
            "form": form,
            "ciclos": CicloAvaliacao.objects.para_usuario(request.user),
        },
    )


def _pendencias(user):
    ciclo = _ciclo_aberto(user)
    if ciclo is None:
        return None, []
    turma_ids = (
        Matricula.objects.para_usuario(user)
        .filter(aluno_id=user.pk)
        .values_list("turma_id", flat=True)
    )
    vinculos = list(
        Vinculo.objects.para_usuario(user)
        .filter(turma_id__in=turma_ids)
        .select_related("professor", "turma", "disciplina")
    )
    concluidos = set(
        Participacao.objects.para_usuario(user)
        .filter(aluno_id=user.pk, ciclo_id=ciclo.pk)
        .values_list("vinculo_id", flat=True)
    )
    return ciclo, [vinculo for vinculo in vinculos if vinculo.pk not in concluidos]


@papel_requerido(ALUNO)
def pendencias(request):
    ciclo, vinculos = _pendencias(request.user)
    return render(
        request,
        "aluno/pendencias.html",
        {"ciclo": ciclo, "vinculos": vinculos},
    )


@papel_requerido(ALUNO)
def avaliar(request, vinculo_id):
    vinculo = get_object_or_404(
        Vinculo.objects.para_usuario(request.user).select_related(
            "professor", "turma", "disciplina"
        ),
        pk=vinculo_id,
    )
    ciclo = _ciclo_aberto(request.user)
    if (
        ciclo is None
        or not Matricula.objects.para_usuario(request.user)
        .filter(aluno_id=request.user.pk, turma_id=vinculo.turma_id)
        .exists()
    ):
        raise Http404
    ja_participou = (
        Participacao.objects.para_usuario(request.user)
        .filter(aluno_id=request.user.pk, ciclo_id=ciclo.pk, vinculo_id=vinculo.pk)
        .exists()
    )
    if ja_participou and request.method != "POST":
        messages.info(
            request, "Essa aula já foi registrada. Obrigado por participar da escuta."
        )
        return redirect("aluno")
    perguntas = list(Pergunta.objects.filter(ciclo_id=ciclo.pk).order_by("ordem"))
    form = AvaliacaoForm(perguntas, request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if Participacao.objects.filter(
                    aluno_id=request.user.pk, ciclo_id=ciclo.pk, vinculo_id=vinculo.pk
                ).exists():
                    raise IntegrityError("participacao_duplicada")
                Participacao.objects.create(
                    aluno=request.user, ciclo=ciclo, vinculo=vinculo
                )
                avaliacao = Avaliacao.objects.create(ciclo=ciclo, vinculo=vinculo.pk)
                for pergunta, resposta in form.respostas():
                    if pergunta.tipo == Pergunta.Tipo.ESCALA_1_5:
                        RespostaEscala.objects.create(
                            avaliacao=avaliacao, pergunta=pergunta, valor=resposta
                        )
                    else:
                        RespostaTexto.objects.create(
                            avaliacao=avaliacao,
                            pergunta=pergunta,
                            texto=(resposta or "").strip(),
                        )
        except IntegrityError:
            form.add_error(
                None,
                "Essa aula já foi registrada. Sua contribuição já está protegida e não foi duplicada.",
            )
        else:
            return redirect("aluno_obrigado")
    return render(
        request,
        "aluno/avaliar.html",
        {"form": form, "ciclo": ciclo, "vinculo": vinculo},
    )


@papel_requerido(ALUNO)
def obrigado(request):
    return render(request, "aluno/obrigado.html")
