from django.db import models


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
