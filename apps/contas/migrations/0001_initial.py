import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
from django.db import migrations, models

# Generated migration containers are intentionally mutable for Django.
# ruff: noqa: RUF012


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("escolas", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Usuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
                ("date_joined", models.DateTimeField(auto_now_add=True, verbose_name="date joined")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="e-mail")),
                ("nome", models.CharField(max_length=180, verbose_name="nome")),
                ("role", models.CharField(choices=[("ALUNO", "Aluno"), ("PROFESSOR", "Professor"), ("COORDENACAO", "Coordenação")], max_length=20, verbose_name="papel")),
                ("escola", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="usuarios", to="escolas.escola", verbose_name="escola")),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.", related_name="usuario_set", related_query_name="usuario", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="usuario_set", related_query_name="usuario", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"verbose_name": "user", "verbose_name_plural": "users"},
            managers=[("objects", django.contrib.auth.models.UserManager())],
        ),
    ]
