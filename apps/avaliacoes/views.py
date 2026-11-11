from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.contas.decorators import papel_requerido
from apps.contas.models import Usuario
from apps.escolas.models import Matricula, Turma, Vinculo

from .forms import AvaliacaoForm, CicloAvaliacaoForm
from .models import (
    Avaliacao,
    CicloAvaliacao,
    Participacao,
    Pergunta,
    RespostaEscala,
    RespostaTexto,
)
from .services import (
    criar_ciclo_com_questionario,
    publicar_ciclo,
    respostas_pendentes,
)

COORDENACAO = Usuario.Role.COORDENACAO
ALUNO = Usuario.Role.ALUNO


def _ciclo_aberto(user):
    return (
        CicloAvaliacao.objects.para_usuario(user)
        .filter(status=CicloAvaliacao.Status.ABERTO)
        .first()
    )


def _adesao_por_turma(ciclo, user):
    turmas = Turma.objects.para_usuario(user).prefetch_related("matriculas")
    return [
        {
            "turma": turma,
            "total": turma.matriculas.count(),
            "respondidos": (
                Participacao.objects.filter(
                    ciclo=ciclo, vinculo__turma=turma
                )
                .values("aluno_id")
                .distinct()
                .count()
            ),
        }
        for turma in turmas
    ]


def _contexto_ciclos(user):
    ciclos = list(CicloAvaliacao.objects.para_usuario(user))
    pendentes = RespostaTexto.objects.filter(
        avaliacao__ciclo__escola_id=user.escola_id,
        status_moderacao=RespostaTexto.StatusModeracao.PENDENTE,
    ).exclude(texto="").order_by("?")
    for ciclo in ciclos:
        ciclo.adesao_por_turma = _adesao_por_turma(ciclo, user)
        ciclo.pendentes_moderacao = pendentes.filter(avaliacao__ciclo=ciclo)
    return ciclos, pendentes


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
    ciclos_contexto, pendentes = _contexto_ciclos(request.user)
    return render(
        request,
        "coordenacao/ciclos.html",
        {
            "form": form,
            "ciclos": ciclos_contexto,
            "fila_moderacao": pendentes,
        },
    )


@papel_requerido(COORDENACAO)
def encerrar_ciclo(request, ciclo_id):
    if request.method != "POST":
        return redirect("coordenacao_ciclos")
    ciclo = get_object_or_404(
        CicloAvaliacao.objects.para_usuario(request.user), pk=ciclo_id
    )
    if ciclo.status == CicloAvaliacao.Status.ABERTO:
        ciclo.status = CicloAvaliacao.Status.FECHADO
        ciclo.save(update_fields=("status",))
        messages.success(request, "Ciclo encerrado. A escuta está pronta para moderação.")
    else:
        messages.info(request, "Este ciclo não está aberto para encerramento.")
    return redirect("coordenacao_ciclos")


@papel_requerido(COORDENACAO)
def publicar(request, ciclo_id):
    if request.method != "POST":
        return redirect("coordenacao_ciclos")
    ciclo = get_object_or_404(
        CicloAvaliacao.objects.para_usuario(request.user), pk=ciclo_id
    )
    if publicar_ciclo(ciclo):
        messages.success(request, "Resultados publicados com cuidado e transparência.")
    elif respostas_pendentes(ciclo).exists():
        messages.error(request, "Ainda há comentários aguardando moderação antes da publicação.")
    else:
        messages.info(request, "O ciclo precisa estar fechado para ser publicado.")
    return redirect("coordenacao_ciclos")


@papel_requerido(COORDENACAO)
def moderar_resposta(request, resposta_id):
    if request.method != "POST":
        return redirect("coordenacao_ciclos")
    resposta = get_object_or_404(
        RespostaTexto.objects.filter(
            avaliacao__ciclo__escola_id=request.user.escola_id,
            status_moderacao=RespostaTexto.StatusModeracao.PENDENTE,
        ),
        pk=resposta_id,
    )
    acao = request.POST.get("acao")
    novo_status = {
        "aprovar": RespostaTexto.StatusModeracao.APROVADO,
        "rejeitar": RespostaTexto.StatusModeracao.REJEITADO,
    }.get(acao)
    if novo_status:
        resposta.status_moderacao = novo_status
        resposta.save(update_fields=("status_moderacao",))
        messages.success(request, "Comentário moderado sem expor qualquer identificação.")
    return redirect("coordenacao_ciclos")


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
