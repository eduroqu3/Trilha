import django.db.models.deletion
from django.db import migrations, models

PERGUNTAS = (
    ("A clareza das explicações ajuda você a acompanhar a aula?", "clareza", "ESCALA_1_5", []),
    ("Você sente que sua participação é escutada durante a aula?", "escuta", "ESCALA_1_5", []),
    ("O ritmo da aula favorece sua aprendizagem?", "ritmo", "ESCALA_1_5", []),
    ("A organização da aula ajuda você a aprender?", "organização", "ESCALA_1_5", []),
    ("As propostas da aula incentivam sua aprendizagem?", "incentivo", "ESCALA_1_5", []),
    ("Você se sente acolhido ou acolhida durante a aula?", "acolhimento", "ESCALA_1_5", []),
    ("O que ajuda você a aprender nessa aula?", "", "TEXTO", []),
    ("O que poderia mudar para a aprendizagem fluir melhor?", "", "TEXTO", []),
)


def criar_padroes(apps, schema_editor):
    Escola = apps.get_model("escolas", "Escola")
    Modelo = apps.get_model("avaliacoes", "ModeloQuestionario")
    PerguntaModelo = apps.get_model("avaliacoes", "PerguntaModelo")
    for escola in Escola.objects.all().iterator():
        modelo, criado = Modelo.objects.get_or_create(
            escola_id=escola.pk,
            padrao=True,
            defaults={"nome": "Questionário padrão da Trilha", "descricao": "Modelo base de escuta pedagógica.", "ativo": True},
        )
        if criado:
            PerguntaModelo.objects.bulk_create([
                PerguntaModelo(modelo_id=modelo.pk, texto=texto, dimensao=dimensao, tipo=tipo, ordem=ordem, obrigatoria=tipo != "TEXTO", opcoes=opcoes)
                for ordem, (texto, dimensao, tipo, opcoes) in enumerate(PERGUNTAS, 1)
            ])


def remover_padroes(apps, schema_editor):
    apps.get_model("avaliacoes", "ModeloQuestionario").objects.filter(padrao=True).delete()


class Migration(migrations.Migration):
    dependencies = [("avaliacoes", "0003_alter_resumovinculo_vinculo")]  # noqa: RUF012

    operations = [  # noqa: RUF012
        migrations.CreateModel(
            name="ModeloQuestionario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=180, verbose_name="nome")),
                ("descricao", models.TextField(blank=True, verbose_name="descrição")),
                ("ativo", models.BooleanField(default=True, verbose_name="ativo")),
                ("padrao", models.BooleanField(default=False, verbose_name="modelo padrão")),
                ("escola", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="modelos_questionario", to="escolas.escola", verbose_name="escola")),
            ],
            options={"ordering": ("nome", "pk"), "verbose_name": "modelo de questionário", "verbose_name_plural": "modelos de questionário"},
        ),
        migrations.CreateModel(
            name="PerguntaModelo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("texto", models.TextField(verbose_name="texto")),
                ("tipo", models.CharField(choices=[("ESCALA_1_5", "Escala de 1 a 5"), ("ESCOLHA_UNICA", "Escolha única"), ("TEXTO", "Texto")], max_length=15, verbose_name="tipo")),
                ("dimensao", models.CharField(blank=True, max_length=80, verbose_name="dimensão")),
                ("ordem", models.PositiveSmallIntegerField(verbose_name="ordem")),
                ("obrigatoria", models.BooleanField(default=True, verbose_name="obrigatória")),
                ("opcoes", models.JSONField(blank=True, default=list, verbose_name="opções")),
                ("modelo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="perguntas_modelo", to="avaliacoes.modeloquestionario")),
            ],
            options={"ordering": ("ordem", "pk"), "verbose_name": "pergunta do modelo", "verbose_name_plural": "perguntas do modelo"},
        ),
        migrations.AddConstraint(model_name="modeloquestionario", constraint=models.UniqueConstraint(fields=("escola", "nome"), name="avaliacoes_modelo_escola_nome_unico")),
        migrations.AddConstraint(model_name="perguntamodelo", constraint=models.UniqueConstraint(fields=("modelo", "ordem"), name="avaliacoes_perguntamodelo_ordem_unica")),
        migrations.AddField(model_name="cicloavaliacao", name="modelo_questionario", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="ciclos", to="avaliacoes.modeloquestionario")),
        migrations.AddField(model_name="pergunta", name="obrigatoria", field=models.BooleanField(default=True, verbose_name="obrigatória")),
        migrations.AddField(model_name="pergunta", name="opcoes", field=models.JSONField(blank=True, default=list, verbose_name="opções")),
        migrations.AlterField(model_name="pergunta", name="tipo", field=models.CharField(choices=[("ESCALA_1_5", "Escala de 1 a 5"), ("ESCOLHA_UNICA", "Escolha única"), ("TEXTO", "Texto")], max_length=15, verbose_name="tipo")),
        migrations.CreateModel(
            name="RespostaEscolhaUnica",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("opcao", models.CharField(max_length=180, verbose_name="opção")),
                ("avaliacao", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="respostas_escolha", to="avaliacoes.avaliacao", verbose_name="avaliação")),
                ("pergunta", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="respostas_escolha", to="avaliacoes.pergunta", verbose_name="pergunta")),
            ],
            options={"verbose_name": "resposta de escolha única", "verbose_name_plural": "respostas de escolha única"},
        ),
        migrations.AddConstraint(model_name="respostaescolhaunica", constraint=models.UniqueConstraint(fields=("avaliacao", "pergunta"), name="avaliacoes_resposta_escolha_avaliacao_pergunta_unica")),
        migrations.AddField(model_name="resumovinculo", name="distribuicoes_por_pergunta", field=models.JSONField(default=dict, verbose_name="distribuições por pergunta")),
        migrations.RunPython(criar_padroes, remover_padroes),
    ]
