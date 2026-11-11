import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.escolas.models import Escola

from .querysets import (
    AvaliacaoQuerySet,
    CicloAvaliacaoQuerySet,
    ParticipacaoQuerySet,
    PerguntaQuerySet,
    RespostaEscalaQuerySet,
    RespostaTextoQuerySet,
    ResumoVinculoQuerySet,
)


class CicloAvaliacao(models.Model):
    class Status(models.TextChoices):
        ABERTO = "ABERTO", "Aberto"
        FECHADO = "FECHADO", "Fechado"
        PUBLICADO = "PUBLICADO", "Publicado"

    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name="ciclos_avaliacao",
        verbose_name="escola",
    )
    nome = models.CharField("nome", max_length=180)
    status = models.CharField(
        "status", max_length=10, choices=Status.choices, default=Status.ABERTO
    )
    objects = CicloAvaliacaoQuerySet.as_manager()

    class Meta:
        ordering = ("nome",)
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("escola",),
                condition=Q(status__in=("ABERTO", "FECHADO")),
                name="avaliacoes_um_ciclo_nao_publicado_escola",
            )
        ]
        verbose_name = "ciclo de avaliação"
        verbose_name_plural = "ciclos de avaliação"

    def __str__(self):
        return f"{self.nome} — {self.escola.nome}"


class Pergunta(models.Model):
    class Tipo(models.TextChoices):
        ESCALA_1_5 = "ESCALA_1_5", "Escala de 1 a 5"
        TEXTO = "TEXTO", "Texto"

    ciclo = models.ForeignKey(
        CicloAvaliacao,
        on_delete=models.CASCADE,
        related_name="perguntas",
        verbose_name="ciclo",
    )
    texto = models.TextField("texto")
    tipo = models.CharField("tipo", max_length=10, choices=Tipo.choices)
    dimensao = models.CharField("dimensão", max_length=40, blank=True)
    ordem = models.PositiveSmallIntegerField("ordem")
    objects = PerguntaQuerySet.as_manager()

    class Meta:
        ordering = ("ordem",)
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("ciclo", "ordem"), name="avaliacoes_pergunta_ciclo_ordem_unica"
            )
        ]
        verbose_name = "pergunta"
        verbose_name_plural = "perguntas"

    def __str__(self):
        return self.texto


class Participacao(models.Model):
    aluno = models.ForeignKey(
        "contas.Usuario",
        on_delete=models.CASCADE,
        related_name="participacoes_avaliacao",
        verbose_name="aluno",
    )
    ciclo = models.ForeignKey(
        CicloAvaliacao,
        on_delete=models.CASCADE,
        related_name="participacoes",
        verbose_name="ciclo",
    )
    vinculo = models.ForeignKey(
        "escolas.Vinculo",
        on_delete=models.CASCADE,
        related_name="participacoes",
        verbose_name="vínculo",
    )
    objects = ParticipacaoQuerySet.as_manager()

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("aluno", "ciclo", "vinculo"),
                name="avaliacoes_participacao_aluno_ciclo_vinculo_unica",
            )
        ]
        verbose_name = "participação"
        verbose_name_plural = "participações"


class Avaliacao(models.Model):
    """Conteúdo anônimo: não possui FK, hash ou chave comum com o aluno."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ciclo = models.ForeignKey(
        CicloAvaliacao,
        on_delete=models.PROTECT,
        related_name="conteudos_anonimos",
        verbose_name="ciclo",
    )
    # Scalar by design: a FK to Vinculo would transitively reach Usuario via professor.
    vinculo = models.PositiveBigIntegerField("vínculo", db_column="vinculo_id")
    objects = AvaliacaoQuerySet.as_manager()

    class Meta:
        verbose_name = "avaliação anônima"
        verbose_name_plural = "avaliações anônimas"

    @property
    def vinculo_obj(self):
        from apps.escolas.models import Vinculo

        return Vinculo.objects.select_related("professor", "turma", "disciplina").get(
            pk=self.vinculo
        )


class RespostaEscala(models.Model):
    avaliacao = models.ForeignKey(
        Avaliacao,
        on_delete=models.CASCADE,
        related_name="respostas_escala",
        verbose_name="avaliação",
    )
    pergunta = models.ForeignKey(
        Pergunta,
        on_delete=models.PROTECT,
        related_name="respostas_escala",
        verbose_name="pergunta",
    )
    valor = models.PositiveSmallIntegerField(
        "valor", validators=(MinValueValidator(1), MaxValueValidator(5))
    )
    objects = RespostaEscalaQuerySet.as_manager()

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("avaliacao", "pergunta"),
                name="avaliacoes_resposta_escala_avaliacao_pergunta_unica",
            )
        ]
        verbose_name = "resposta de escala"
        verbose_name_plural = "respostas de escala"


class RespostaTexto(models.Model):
    class StatusModeracao(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        APROVADO = "APROVADO", "Aprovado"
        REJEITADO = "REJEITADO", "Rejeitado"

    avaliacao = models.ForeignKey(
        Avaliacao,
        on_delete=models.CASCADE,
        related_name="respostas_texto",
        verbose_name="avaliação",
    )
    pergunta = models.ForeignKey(
        Pergunta,
        on_delete=models.PROTECT,
        related_name="respostas_texto",
        verbose_name="pergunta",
    )
    texto = models.TextField("texto", blank=True)
    status_moderacao = models.CharField(
        "status de moderação",
        max_length=10,
        choices=StatusModeracao.choices,
        default=StatusModeracao.PENDENTE,
    )
    objects = RespostaTextoQuerySet.as_manager()

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("avaliacao", "pergunta"),
                name="avaliacoes_resposta_texto_avaliacao_pergunta_unica",
            )
        ]
        verbose_name = "resposta de texto"
        verbose_name_plural = "respostas de texto"


class ResumoVinculo(models.Model):
    ciclo = models.ForeignKey(
        CicloAvaliacao,
        on_delete=models.CASCADE,
        related_name="resumos_vinculo",
        verbose_name="ciclo",
    )
    vinculo = models.ForeignKey(
        "escolas.Vinculo",
        on_delete=models.PROTECT,
        db_column="vinculo_id",
        related_name="resumos_avaliacao",
        verbose_name="vínculo",
    )
    n_avaliacoes = models.PositiveIntegerField("número de avaliações")
    medias_por_dimensao = models.JSONField("médias por dimensão", default=dict)
    objects = ResumoVinculoQuerySet.as_manager()

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("ciclo", "vinculo"),
                name="avaliacoes_resumo_ciclo_vinculo_unico",
            )
        ]
        ordering = ("ciclo__nome", "vinculo")
        verbose_name = "resumo por vínculo"
        verbose_name_plural = "resumos por vínculo"
