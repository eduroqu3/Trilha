from django.db import models


class EscolaQuerySet(models.QuerySet):
    def para_usuario(self, user):
        escola_id = getattr(user, "escola_id", None)
        if not getattr(user, "is_authenticated", False) or not escola_id:
            return self.none()
        return self.filter(escola_id=escola_id)


class TurmaQuerySet(EscolaQuerySet):
    pass


class DisciplinaQuerySet(EscolaQuerySet):
    pass


class MatriculaQuerySet(models.QuerySet):
    def para_usuario(self, user):
        escola_id = getattr(user, "escola_id", None)
        if not getattr(user, "is_authenticated", False) or not escola_id:
            return self.none()
        return self.filter(turma__escola_id=escola_id)


class VinculoQuerySet(models.QuerySet):
    def para_usuario(self, user):
        escola_id = getattr(user, "escola_id", None)
        if not getattr(user, "is_authenticated", False) or not escola_id:
            return self.none()
        return self.filter(turma__escola_id=escola_id)
