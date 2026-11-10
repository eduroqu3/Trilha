from django.db import models


class IsolamentoEscolaQuerySet(models.QuerySet):
    def para_usuario(self, user):
        return self.filter(escola_id=user.escola_id)


class CicloAvaliacaoQuerySet(IsolamentoEscolaQuerySet):
    pass


class PerguntaQuerySet(models.QuerySet):
    def para_usuario(self, user):
        return self.filter(ciclo__escola_id=user.escola_id)


class ParticipacaoQuerySet(models.QuerySet):
    def para_usuario(self, user):
        return self.filter(ciclo__escola_id=user.escola_id)


class AvaliacaoQuerySet(models.QuerySet):
    pass


class RespostaEscalaQuerySet(models.QuerySet):
    pass


class RespostaTextoQuerySet(models.QuerySet):
    pass
