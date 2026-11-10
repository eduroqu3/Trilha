from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if (
            extra_fields.get("is_staff") is not True
            or extra_fields.get("is_superuser") is not True
        ):
            raise ValueError(
                "Superusuário precisa de is_staff=True e is_superuser=True."
            )
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractUser):
    class Role(models.TextChoices):
        ALUNO = "ALUNO", "Aluno"
        PROFESSOR = "PROFESSOR", "Professor"
        COORDENACAO = "COORDENACAO", "Coordenação"

    username = None
    email = models.EmailField("e-mail", unique=True)
    nome = models.CharField("nome", max_length=180)
    role = models.CharField("papel", max_length=20, choices=Role.choices)
    escola = models.ForeignKey(
        "escolas.Escola",
        on_delete=models.PROTECT,
        related_name="usuarios",
        verbose_name="escola",
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("nome", "role", "escola")
    objects = UsuarioManager()

    def __str__(self):
        return self.email
