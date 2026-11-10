from django.contrib import admin

from .models import Disciplina, Escola, Matricula, Turma, Vinculo


@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ("nome", "limiar_minimo", "criada_em")
    search_fields = ("nome",)


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ano_letivo", "escola")
    list_filter = ("ano_letivo", "escola")
    search_fields = ("nome", "escola__nome")


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ("nome", "escola")
    list_filter = ("escola",)
    search_fields = ("nome", "escola__nome")


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ("aluno", "turma")
    list_filter = ("turma__escola",)
    search_fields = ("aluno__nome", "aluno__email", "turma__nome")


@admin.register(Vinculo)
class VinculoAdmin(admin.ModelAdmin):
    list_display = ("professor", "turma", "disciplina")
    list_filter = ("turma__escola", "disciplina")
    search_fields = (
        "professor__nome",
        "professor__email",
        "turma__nome",
        "disciplina__nome",
    )
