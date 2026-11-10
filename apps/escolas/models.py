from django.core.exceptions import ValidationError
from django.db import models

from .querysets import (
    DisciplinaQuerySet,
    MatriculaQuerySet,
    TurmaQuerySet,
    VinculoQuerySet,
)


class Escola(models.Model):
    nome = models.CharField("nome", max_length=180)
    limiar_minimo = models.PositiveSmallIntegerField(default=5)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("nome",)
        verbose_name = "escola"
        verbose_name_plural = "escolas"

    def __str__(self):
        return self.nome


class Turma(models.Model):
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name="turmas",
        verbose_name="escola",
    )
    nome = models.CharField("nome", max_length=120)
    ano_letivo = models.PositiveSmallIntegerField("ano letivo")
    objects = TurmaQuerySet.as_manager()

    class Meta:
        ordering = ("ano_letivo", "nome")
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("escola", "nome", "ano_letivo"),
                name="escolas_turma_escola_nome_ano_unico",
            )
        ]
        verbose_name = "turma"
        verbose_name_plural = "turmas"

    def __str__(self):
        return f"{self.nome} ({self.ano_letivo})"


class Disciplina(models.Model):
    escola = models.ForeignKey(
        Escola,
        on_delete=models.CASCADE,
        related_name="disciplinas",
        verbose_name="escola",
    )
    nome = models.CharField("nome", max_length=120)
    objects = DisciplinaQuerySet.as_manager()

    class Meta:
        ordering = ("nome",)
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("escola", "nome"),
                name="escolas_disciplina_escola_nome_unico",
            )
        ]
        verbose_name = "disciplina"
        verbose_name_plural = "disciplinas"

    def __str__(self):
        return self.nome


class Matricula(models.Model):
    aluno = models.ForeignKey(
        "contas.Usuario",
        on_delete=models.CASCADE,
        related_name="matriculas",
        verbose_name="aluno",
    )
    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name="matriculas",
        verbose_name="turma",
    )
    objects = MatriculaQuerySet.as_manager()

    class Meta:
        ordering = ("aluno__nome",)
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("aluno", "turma"),
                name="escolas_matricula_aluno_turma_unica",
            )
        ]
        verbose_name = "matrícula"
        verbose_name_plural = "matrículas"

    def clean(self):
        if self.aluno_id and self.aluno.role != "ALUNO":
            raise ValidationError({"aluno": "A matrícula exige um usuário aluno."})
        if (
            self.aluno_id
            and self.turma_id
            and self.aluno.escola_id != self.turma.escola_id
        ):
            raise ValidationError("Aluno e turma precisam pertencer à mesma escola.")

    def __str__(self):
        return f"{self.aluno.nome} — {self.turma}"


class Vinculo(models.Model):
    professor = models.ForeignKey(
        "contas.Usuario",
        on_delete=models.CASCADE,
        related_name="vinculos_professor",
        verbose_name="professor",
    )
    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name="vinculos",
        verbose_name="turma",
    )
    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        related_name="vinculos",
        verbose_name="disciplina",
    )
    objects = VinculoQuerySet.as_manager()

    class Meta:
        ordering = ("turma__ano_letivo", "turma__nome", "disciplina__nome")
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=("professor", "turma", "disciplina"),
                name="escolas_vinculo_trio_unico",
            )
        ]
        verbose_name = "vínculo"
        verbose_name_plural = "vínculos"

    def clean(self):
        if self.professor_id and self.professor.role != "PROFESSOR":
            raise ValidationError(
                {"professor": "O vínculo exige um usuário professor."}
            )
        if (
            self.professor_id
            and self.turma_id
            and self.professor.escola_id != self.turma.escola_id
        ):
            raise ValidationError(
                "Professor e turma precisam pertencer à mesma escola."
            )
        if (
            self.turma_id
            and self.disciplina_id
            and self.turma.escola_id != self.disciplina.escola_id
        ):
            raise ValidationError(
                "Turma e disciplina precisam pertencer à mesma escola."
            )

    def __str__(self):
        return f"{self.professor.nome} — {self.turma} — {self.disciplina}"
