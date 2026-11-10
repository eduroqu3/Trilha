import csv

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.contas.decorators import papel_requerido
from apps.contas.models import Usuario

from .forms import (
    AlunoForm,
    CSVImportForm,
    DisciplinaForm,
    ProfessorForm,
    TurmaForm,
    VinculoForm,
)
from .models import Disciplina, Turma, Vinculo
from .services import (
    criar_aluno,
    criar_professor,
    importar_alunos,
    importar_professores,
)

COORDENACAO = Usuario.Role.COORDENACAO


def _resultado_importacao(request, tipo, resultado):
    request.session["coordenacao_importacao"] = {"tipo": tipo, **resultado}
    return render(
        request,
        "coordenacao/importacao_resultado.html",
        {"tipo": tipo, **resultado},
    )


@papel_requerido(COORDENACAO)
def turmas(request):
    form = TurmaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        turma = form.save(commit=False)
        turma.escola = request.user.escola
        try:
            turma.save()
        except IntegrityError:
            form.add_error(None, "Essa turma já existe para este ano letivo.")
        else:
            messages.success(request, "Turma criada com sucesso.")
            return redirect("coordenacao_turmas")
    return render(
        request,
        "coordenacao/turmas.html",
        {"form": form, "turmas": Turma.objects.para_usuario(request.user)},
    )


@papel_requerido(COORDENACAO)
@require_POST
def remover_turma(request, pk):
    turma = get_object_or_404(Turma.objects.para_usuario(request.user), pk=pk)
    turma.delete()
    messages.success(request, "Turma removida com sucesso.")
    return redirect("coordenacao_turmas")


@papel_requerido(COORDENACAO)
def disciplinas(request):
    form = DisciplinaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        disciplina = form.save(commit=False)
        disciplina.escola = request.user.escola
        try:
            disciplina.save()
        except IntegrityError:
            form.add_error(None, "Essa disciplina já existe para esta escola.")
        else:
            messages.success(request, "Disciplina criada com sucesso.")
            return redirect("coordenacao_disciplinas")
    return render(
        request,
        "coordenacao/disciplinas.html",
        {
            "form": form,
            "disciplinas": Disciplina.objects.para_usuario(request.user),
        },
    )


@papel_requerido(COORDENACAO)
@require_POST
def remover_disciplina(request, pk):
    disciplina = get_object_or_404(Disciplina.objects.para_usuario(request.user), pk=pk)
    disciplina.delete()
    messages.success(request, "Disciplina removida com sucesso.")
    return redirect("coordenacao_disciplinas")


@papel_requerido(COORDENACAO)
def professores(request):
    form = ProfessorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                professor, senha = criar_professor(
                    request.user.escola,
                    form.cleaned_data["nome"],
                    form.cleaned_data["email"],
                )
        except IntegrityError:
            form.add_error(None, "Não foi possível criar este professor agora.")
        else:
            return _resultado_importacao(
                request,
                "professores",
                {
                    "criados": [
                        {
                            "nome": professor.nome,
                            "email": professor.email,
                            "senha": senha,
                        }
                    ],
                    "erros": [],
                },
            )
    return render(
        request,
        "coordenacao/professores.html",
        {
            "form": form,
            "csv_form": CSVImportForm(("nome", "email")),
            "professores": Usuario.objects.da_escola(
                request.user, role=Usuario.Role.PROFESSOR
            ),
        },
    )


@papel_requerido(COORDENACAO)
def importar_professores_csv(request):
    if request.method != "POST":
        return redirect("coordenacao_professores")
    form = CSVImportForm(("nome", "email"), request.POST, request.FILES)
    if not form.is_valid():
        return render(
            request,
            "coordenacao/professores.html",
            {
                "form": ProfessorForm(),
                "csv_form": form,
                "professores": Usuario.objects.da_escola(
                    request.user, role=Usuario.Role.PROFESSOR
                ),
            },
        )
    return _resultado_importacao(
        request,
        "professores",
        importar_professores(request.user, form.cleaned_data["arquivo"].linhas_csv),
    )


@papel_requerido(COORDENACAO)
def alunos(request):
    form = AlunoForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                aluno, senha = criar_aluno(
                    request.user.escola,
                    form.cleaned_data["nome"],
                    form.cleaned_data["email"],
                    form.cleaned_data["turma"],
                )
        except IntegrityError:
            form.add_error(None, "Não foi possível criar este aluno agora.")
        else:
            return _resultado_importacao(
                request,
                "alunos",
                {
                    "criados": [
                        {
                            "nome": aluno.nome,
                            "email": aluno.email,
                            "senha": senha,
                            "turma": form.cleaned_data["turma"].nome,
                        }
                    ],
                    "erros": [],
                },
            )
    return render(
        request,
        "coordenacao/alunos.html",
        {
            "form": form,
            "csv_form": CSVImportForm(("nome", "email", "turma")),
            "alunos": Usuario.objects.da_escola(
                request.user, role=Usuario.Role.ALUNO
            ).prefetch_related("matriculas__turma"),
        },
    )


@papel_requerido(COORDENACAO)
def importar_alunos_csv(request):
    if request.method != "POST":
        return redirect("coordenacao_alunos")
    form = CSVImportForm(("nome", "email", "turma"), request.POST, request.FILES)
    if not form.is_valid():
        return render(
            request,
            "coordenacao/alunos.html",
            {
                "form": AlunoForm(request.user),
                "csv_form": form,
                "alunos": Usuario.objects.da_escola(
                    request.user, role=Usuario.Role.ALUNO
                ).prefetch_related("matriculas__turma"),
            },
        )
    return _resultado_importacao(
        request,
        "alunos",
        importar_alunos(request.user, form.cleaned_data["arquivo"].linhas_csv),
    )


@papel_requerido(COORDENACAO)
def vinculos(request):
    form = VinculoForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Vínculo criado com sucesso.")
        return redirect("coordenacao_vinculos")
    vinculos_qs = Vinculo.objects.para_usuario(request.user).select_related(
        "professor", "turma", "disciplina"
    )
    return render(
        request,
        "coordenacao/vinculos.html",
        {"form": form, "vinculos": vinculos_qs},
    )


@papel_requerido(COORDENACAO)
@require_POST
def remover_vinculo(request, pk):
    vinculo = get_object_or_404(Vinculo.objects.para_usuario(request.user), pk=pk)
    vinculo.delete()
    messages.success(request, "Vínculo removido com sucesso.")
    return redirect("coordenacao_vinculos")


@papel_requerido(COORDENACAO)
def download_importacao(request):
    resultado = request.session.pop("coordenacao_importacao", None)
    if not resultado:
        return redirect("coordenacao")
    campos = ["nome", "email", "senha"]
    if resultado["tipo"] == "alunos":
        campos.append("turma")
    resposta = HttpResponse(content_type="text/csv; charset=utf-8")
    resposta["Content-Disposition"] = (
        f'attachment; filename="credenciais-{resultado["tipo"]}.csv"'
    )
    escritor = csv.DictWriter(resposta, fieldnames=campos)
    escritor.writeheader()
    escritor.writerows(
        {campo: linha.get(campo, "") for campo in campos}
        for linha in resultado["criados"]
    )
    return resposta
