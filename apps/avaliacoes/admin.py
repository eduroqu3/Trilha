from django.contrib import admin

from .models import (
    Avaliacao,
    CicloAvaliacao,
    Participacao,
    Pergunta,
    RespostaEscala,
    RespostaTexto,
    ResumoVinculo,
)


@admin.register(CicloAvaliacao)
class CicloAvaliacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "escola", "status")
    list_filter = ("status", "escola")
    search_fields = ("nome", "escola__nome")


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ("texto", "ciclo", "tipo", "dimensao", "ordem")
    list_filter = ("tipo", "dimensao", "ciclo__escola")
    search_fields = ("texto", "dimensao")


@admin.register(Participacao)
class ParticipacaoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "ciclo", "vinculo")
    list_filter = ("ciclo__escola", "ciclo")
    search_fields = ("aluno__email", "aluno__nome")


class ConteudoAnonimoAdminMixin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Avaliacao)
class AvaliacaoAdmin(ConteudoAnonimoAdminMixin):
    list_display = ("id", "ciclo", "vinculo")
    list_filter = ("ciclo__escola", "ciclo")
    readonly_fields = ("id", "ciclo", "vinculo")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RespostaEscala)
class RespostaEscalaAdmin(ConteudoAnonimoAdminMixin):
    list_display = ("avaliacao", "pergunta", "valor")
    list_filter = ("pergunta__ciclo__escola", "pergunta__tipo")
    readonly_fields = ("avaliacao", "pergunta", "valor")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RespostaTexto)
class RespostaTextoAdmin(ConteudoAnonimoAdminMixin):
    list_display = ("avaliacao", "pergunta", "status_moderacao")
    list_filter = ("status_moderacao", "pergunta__ciclo__escola")
    readonly_fields = ("avaliacao", "pergunta", "texto", "status_moderacao")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ResumoVinculo)
class ResumoVinculoAdmin(ConteudoAnonimoAdminMixin):
    list_display = ("ciclo", "vinculo", "n_avaliacoes", "medias_por_dimensao")
    list_filter = ("ciclo__escola", "ciclo")
    readonly_fields = ("ciclo", "vinculo", "n_avaliacoes", "medias_por_dimensao")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
