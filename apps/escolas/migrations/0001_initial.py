from django.db import migrations, models

# Generated migration containers are intentionally mutable for Django.
# ruff: noqa: RUF012


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Escola",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=180, verbose_name="nome")),
                ("limiar_minimo", models.PositiveSmallIntegerField(default=5)),
                ("criada_em", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "escola", "verbose_name_plural": "escolas", "ordering": ("nome",)},
        ),
    ]
