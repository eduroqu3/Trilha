import uuid

from django.core.exceptions import ValidationError
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

DIMENSOES_PADRAO = ("clareza", "escuta", "ritmo", "organização", "incentivo", "acolhimento")
TERMOS_SENSIVEIS = (
    "nome", "gênero", "genero", "idade", "raça", "raca", "cor", "bairro",
    "endereço", "endereco", "cpf", "rg", "telefone", "e-mail", "email",
    "data de nascimento", "sexo", "religião", "religiao", "etnia",
)


def validar_texto_pergunta(texto):
    normalizado = " ".join(texto.lower().split())
    encontrados = [termo for termo in TERMOS_SENSIVEIS if termo in normalizado]
    if encontrados:
        raise ValidationError(
            "Perguntas não podem solicitar dados pessoais ou demográficos "
            f"(termo identificado: {encontrados[0]}). A escuta deve permanecer anônima."
        )


class ModeloQuestionario(models.Model):
    escola = models.ForeignKey(
        Escola, on_delete=models.CASCADE, related_name="modelos_questionario", verbose_name="escola"
    )
    nome = models.CharField("nome", max_length=180)
    descricao = models.TextField("descrição", blank=True)
    ativo = models.BooleanField("ativo", default=True)
    padrao = models.BooleanField("modelo padrão", default=False)

    class Meta:
        ordering = ("nome", "pk")
        constraints = [  # noqa: RUF012  # noqa: RUF012
            models.UniqueConstraint(fields=("escola", "nome"), name="avaliacoes_modelo_escola_nome_unico")
        ]
        verbose_name = "modelo de questionário"
        verbose_name_plural = "modelos de questionário"

    def __str__(self):
        return self.nome

    def clean(self):
        if self.padrao and self.pk:
            antigo = type(self).objects.filter(pk=self.pk).first()
            if antigo and any(getattr(self, campo) != getattr(antigo, campo) for campo in ("nome", "descricao", "ativo")):
                raise ValidationError("O modelo padrão da Trilha não pode ser editado; duplique-o para personalizar.")
        if self.pk:
            validar_regras_modelo(self)


def validar_regras_modelo(modelo):
    perguntas = list(modelo.perguntas_modelo.all()) if modelo.pk else []
    if not 5 <= len(perguntas) <= 15:
        raise ValidationError("O modelo deve ter entre 5 e 15 perguntas.")
    if sum(p.tipo == PerguntaModelo.Tipo.TEXTO for p in perguntas) > 3:
        raise ValidationError("O modelo pode ter no máximo 3 perguntas de texto.")
    if sum(p.tipo == PerguntaModelo.Tipo.ESCALA_1_5 for p in perguntas) < 2:
        raise ValidationError("O modelo deve ter pelo menos 2 perguntas de escala.")


class PerguntaModelo(models.Model):
    class Tipo(models.TextChoices):
        ESCALA_1_5 = "ESCALA_1_5", "Escala de 1 a 5"
        ESCOLHA_UNICA = "ESCOLHA_UNICA", "Escolha única"
        TEXTO = "TEXTO", "Texto"

    modelo = models.ForeignKey(ModeloQuestionario, on_delete=models.CASCADE, related_name="perguntas_modelo")
    texto = models.TextField("texto")
    tipo = models.CharField("tipo", max_length=15, choices=Tipo.choices)
    dimensao = models.CharField("dimensão", max_length=80, blank=True)
    ordem = models.PositiveSmallIntegerField("ordem")
    obrigatoria = models.BooleanField("obrigatória", default=True)
    opcoes = models.JSONField("opções", default=list, blank=True)

    class Meta:
        ordering = ("ordem", "pk")
        constraints = [  # noqa: RUF012  # noqa: RUF012
            models.UniqueConstraint(fields=("modelo", "ordem"), name="avaliacoes_perguntamodelo_ordem_unica")
        ]
        verbose_name = "pergunta do modelo"
        verbose_name_plural = "perguntas do modelo"

    def clean(self):
        validar_texto_pergunta(self.texto)
        opcoes = [str(op).strip() for op in (self.opcoes or []) if str(op).strip()]
        if self.tipo == self.Tipo.ESCOLHA_UNICA and not 2 <= len(opcoes) <= 6:
            raise ValidationError({"opcoes": "Escolha única deve ter de 2 a 6 opções fixas."})
        if self.tipo != self.Tipo.ESCOLHA_UNICA and opcoes:
            raise ValidationError({"opcoes": "Somente perguntas de escolha única possuem opções."})

    def save(self, *args, **kwargs):
        if self.pk and self.modelo.padrao:
            raise ValidationError("As perguntas do modelo padrão não podem ser editadas; duplique-o para personalizar.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.modelo.padrao:
            raise ValidationError("As perguntas do modelo padrão não podem ser removidas; duplique-o para personalizar.")
        return super().delete(*args, **kwargs)


class CicloAvaliacao(models.Model):
    class Status(models.TextChoices):
        ABERTO = "ABERTO", "Aberto"
        FECHADO = "FECHADO", "Fechado"
        PUBLICADO = "PUBLICADO", "Publicado"

    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name="ciclos_avaliacao", verbose_name="escola")
    nome = models.CharField("nome", max_length=180)
    status = models.CharField("status", max_length=10, choices=Status.choices, default=Status.ABERTO)
    modelo_questionario = models.ForeignKey(ModeloQuestionario, null=True, blank=True, on_delete=models.PROTECT, related_name="ciclos")
    objects = CicloAvaliacaoQuerySet.as_manager()

    class Meta:
        ordering = ("nome",)
        constraints = [  # noqa: RUF012  # noqa: RUF012
            models.UniqueConstraint(fields=("escola",), condition=Q(status__in=("ABERTO", "FECHADO")), name="avaliacoes_um_ciclo_nao_publicado_escola")
        ]
        verbose_name = "ciclo de avaliação"
        verbose_name_plural = "ciclos de avaliação"

    def __str__(self):
        return f"{self.nome} — {self.escola.nome}"


class Pergunta(models.Model):
    class Tipo(models.TextChoices):
        ESCALA_1_5 = "ESCALA_1_5", "Escala de 1 a 5"
        ESCOLHA_UNICA = "ESCOLHA_UNICA", "Escolha única"
        TEXTO = "TEXTO", "Texto"

    ciclo = models.ForeignKey(CicloAvaliacao, on_delete=models.CASCADE, related_name="perguntas", verbose_name="ciclo")
    texto = models.TextField("texto")
    tipo = models.CharField("tipo", max_length=15, choices=Tipo.choices)
    dimensao = models.CharField("dimensão", max_length=80, blank=True)
    ordem = models.PositiveSmallIntegerField("ordem")
    obrigatoria = models.BooleanField("obrigatória", default=True)
    opcoes = models.JSONField("opções", default=list, blank=True)
    objects = PerguntaQuerySet.as_manager()

    class Meta:
        ordering = ("ordem",)
        constraints = [  # noqa: RUF012  # noqa: RUF012
            models.UniqueConstraint(fields=("ciclo", "ordem"), name="avaliacoes_pergunta_ciclo_ordem_unica")
        ]
        verbose_name = "pergunta"
        verbose_name_plural = "perguntas"

    def __str__(self):
        return self.texto

    def save(self, *args, **kwargs):
        if self.pk and self.ciclo.status != CicloAvaliacao.Status.ABERTO:
            raise ValidationError("As perguntas de um ciclo encerrado estão travadas.")
        validar_texto_pergunta(self.texto)
        if self.tipo == self.Tipo.ESCOLHA_UNICA and not 2 <= len(self.opcoes or []) <= 6:
            raise ValidationError("Escolha única deve ter de 2 a 6 opções.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.ciclo.status != CicloAvaliacao.Status.ABERTO:
            raise ValidationError("As perguntas de um ciclo encerrado estão travadas.")
        return super().delete(*args, **kwargs)


class Participacao(models.Model):
    aluno = models.ForeignKey("contas.Usuario", on_delete=models.CASCADE, related_name="participacoes_avaliacao", verbose_name="aluno")
    ciclo = models.ForeignKey(CicloAvaliacao, on_delete=models.CASCADE, related_name="participacoes", verbose_name="ciclo")
    vinculo = models.ForeignKey("escolas.Vinculo", on_delete=models.CASCADE, related_name="participacoes", verbose_name="vínculo")
    objects = ParticipacaoQuerySet.as_manager()

    class Meta:
        constraints = [  # noqa: RUF012  # noqa: RUF012
            models.UniqueConstraint(fields=("aluno", "ciclo", "vinculo"), name="avaliacoes_participacao_aluno_ciclo_vinculo_unica")
        ]
        verbose_name = "participação"
        verbose_name_plural = "participações"


class Avaliacao(models.Model):
    """Conteúdo anônimo: não possui FK, hash ou chave comum com o aluno."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ciclo = models.ForeignKey(CicloAvaliacao, on_delete=models.PROTECT, related_name="conteudos_anonimos", verbose_name="ciclo")
    vinculo = models.PositiveBigIntegerField("vínculo", db_column="vinculo_id")
    objects = AvaliacaoQuerySet.as_manager()

    class Meta:
        verbose_name = "avaliação anônima"
        verbose_name_plural = "avaliações anônimas"

    @property
    def vinculo_obj(self):
        from apps.escolas.models import Vinculo
        return Vinculo.objects.select_related("professor", "turma", "disciplina").get(pk=self.vinculo)


class RespostaEscala(models.Model):
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE, related_name="respostas_escala", verbose_name="avaliação")
    pergunta = models.ForeignKey(Pergunta, on_delete=models.PROTECT, related_name="respostas_escala", verbose_name="pergunta")
    valor = models.PositiveSmallIntegerField("valor", validators=(MinValueValidator(1), MaxValueValidator(5)))
    objects = RespostaEscalaQuerySet.as_manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=("avaliacao", "pergunta"), name="avaliacoes_resposta_escala_avaliacao_pergunta_unica")]  # noqa: RUF012
        verbose_name = "resposta de escala"
        verbose_name_plural = "respostas de escala"


class RespostaEscolhaUnica(models.Model):
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE, related_name="respostas_escolha", verbose_name="avaliação")
    pergunta = models.ForeignKey(Pergunta, on_delete=models.PROTECT, related_name="respostas_escolha", verbose_name="pergunta")
    opcao = models.CharField("opção", max_length=180)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("avaliacao", "pergunta"), name="avaliacoes_resposta_escolha_avaliacao_pergunta_unica")]  # noqa: RUF012
        verbose_name = "resposta de escolha única"
        verbose_name_plural = "respostas de escolha única"


class RespostaTexto(models.Model):
    class StatusModeracao(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        APROVADO = "APROVADO", "Aprovado"
        REJEITADO = "REJEITADO", "Rejeitado"

    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE, related_name="respostas_texto", verbose_name="avaliação")
    pergunta = models.ForeignKey(Pergunta, on_delete=models.PROTECT, related_name="respostas_texto", verbose_name="pergunta")
    texto = models.TextField("texto", blank=True)
    status_moderacao = models.CharField("status de moderação", max_length=10, choices=StatusModeracao.choices, default=StatusModeracao.PENDENTE)
    objects = RespostaTextoQuerySet.as_manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=("avaliacao", "pergunta"), name="avaliacoes_resposta_texto_avaliacao_pergunta_unica")]  # noqa: RUF012
        verbose_name = "resposta de texto"
        verbose_name_plural = "respostas de texto"


class ResumoVinculo(models.Model):
    ciclo = models.ForeignKey(CicloAvaliacao, on_delete=models.CASCADE, related_name="resumos_vinculo", verbose_name="ciclo")
    vinculo = models.ForeignKey("escolas.Vinculo", on_delete=models.PROTECT, db_column="vinculo_id", related_name="resumos_avaliacao", verbose_name="vínculo")
    n_avaliacoes = models.PositiveIntegerField("número de avaliações")
    medias_por_dimensao = models.JSONField("médias por dimensão", default=dict)
    distribuicoes_por_pergunta = models.JSONField("distribuições por pergunta", default=dict)
    objects = ResumoVinculoQuerySet.as_manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=("ciclo", "vinculo"), name="avaliacoes_resumo_ciclo_vinculo_unico")]  # noqa: RUF012
        ordering = ("ciclo__nome", "vinculo")
        verbose_name = "resumo por vínculo"
        verbose_name_plural = "resumos por vínculo"
