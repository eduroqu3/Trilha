import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.avaliacoes.models import (
    CicloAvaliacao,
    ModeloQuestionario,
    Pergunta,
    PerguntaModelo,
)
from apps.avaliacoes.services import (
    criar_ciclo_com_questionario,
    criar_modelo_padrao,
    duplicar_modelo,
)
from apps.contas.models import Usuario
from apps.escolas.models import Escola


@pytest.fixture
def escolas(db):
    return Escola.objects.create(nome="Escola V2 A"), Escola.objects.create(nome="Escola V2 B")


@pytest.fixture
def coordenador(escolas):
    return Usuario.objects.create_user(
        email="coordenador-v2@example.com",
        password="Senha-forte-123!",
        nome="Coordenação V2",
        role=Usuario.Role.COORDENACAO,
        escola=escolas[0],
    )


@pytest.mark.django_db
def test_modelo_padrao_e_duplicacao_sao_isolados(escolas):
    escola_a, escola_b = escolas
    padrao = criar_modelo_padrao(escola_a)
    assert ModeloQuestionario.objects.filter(escola=escola_b).count() == 0
    copia = duplicar_modelo(padrao, escola_a, "Escuta personalizada")
    assert copia.escola_id == escola_a.pk
    assert copia.padrao is False
    assert copia.perguntas_modelo.count() == 8


@pytest.mark.django_db
def test_snapshot_nao_muda_quando_modelo_muda(escolas):
    escola_a, _ = escolas
    modelo = duplicar_modelo(criar_modelo_padrao(escola_a), escola_a, "Minha escuta")
    ciclo = criar_ciclo_com_questionario(escola_a, "Ciclo V2", modelo)
    original = list(ciclo.perguntas.values_list("texto", "opcoes"))
    pergunta_modelo = modelo.perguntas_modelo.first()
    pergunta_modelo.texto = "Texto revisado para futuros ciclos"
    pergunta_modelo.save(update_fields=("texto",))
    assert list(ciclo.perguntas.values_list("texto", "opcoes")) == original


@pytest.mark.django_db
def test_perguntas_do_ciclo_aberto_ficam_travadas(escolas):
    escola_a, _ = escolas
    ciclo = criar_ciclo_com_questionario(escola_a, "Ciclo travado")
    pergunta = ciclo.perguntas.first()
    pergunta.texto = "tentativa de alteração"
    with pytest.raises(ValidationError):
        pergunta.save()


@pytest.mark.django_db
def test_limites_e_termos_de_anonimato():
    escola = Escola.objects.create(nome="Escola limites")
    modelo = ModeloQuestionario.objects.create(escola=escola, nome="Validação")
    with pytest.raises(ValidationError):
        PerguntaModelo.objects.create(
            modelo=modelo,
            texto="Qual é seu nome?",
            tipo=PerguntaModelo.Tipo.ESCALA_1_5,
            ordem=1,
        )
    for ordem in range(1, 5):
        PerguntaModelo.objects.create(
            modelo=modelo,
            texto=f"Pergunta segura {ordem}",
            tipo=PerguntaModelo.Tipo.ESCALA_1_5,
            ordem=ordem,
        )
    with pytest.raises(ValidationError):
        modelo.clean()


@pytest.mark.django_db
def test_escolha_unica_exige_de_duas_a_seis_opcoes():
    escola = Escola.objects.create(nome="Escola escolhas")
    modelo = ModeloQuestionario.objects.create(escola=escola, nome="Escolhas")
    with pytest.raises(ValidationError):
        PerguntaModelo.objects.create(
            modelo=modelo,
            texto="Como foi a aula?",
            tipo=PerguntaModelo.Tipo.ESCOLHA_UNICA,
            ordem=1,
            opcoes=["uma"],
        )


@pytest.mark.django_db
def test_ciclos_legados_continuam_com_snapshot_de_perguntas(escolas):
    escola_a, _ = escolas
    ciclo = CicloAvaliacao.objects.create(
        escola=escola_a,
        nome="Legado",
        status=CicloAvaliacao.Status.ABERTO,
    )
    Pergunta.objects.create(
        ciclo=ciclo,
        texto="Pergunta legada",
        tipo=Pergunta.Tipo.ESCALA_1_5,
        ordem=1,
    )
    assert ciclo.modelo_questionario_id is None
    assert ciclo.perguntas.count() == 1


@pytest.mark.django_db
def test_modelo_padrao_nao_pode_ser_excluido():
    escola = Escola.objects.create(nome="Escola proteção")
    modelo = criar_modelo_padrao(escola)
    with pytest.raises(ValidationError):
        modelo.delete()


@pytest.mark.django_db
def test_exclusao_de_modelo_personalizado_remove_suas_perguntas():
    escola = Escola.objects.create(nome="Escola exclusão")
    modelo = ModeloQuestionario.objects.create(escola=escola, nome="Temporário")
    PerguntaModelo.objects.create(
        modelo=modelo,
        texto="Pergunta segura",
        tipo=PerguntaModelo.Tipo.ESCALA_1_5,
        ordem=1,
    )
    modelo_id = modelo.pk
    modelo.delete()
    assert not ModeloQuestionario.objects.filter(pk=modelo_id).exists()


@pytest.mark.django_db
def test_view_crud_ordena_edita_e_remove_perguntas(client, coordenador):
    modelo = ModeloQuestionario.objects.create(escola=coordenador.escola, nome="CRUD")
    perguntas = [
        PerguntaModelo.objects.create(
            modelo=modelo,
            texto=f"Pergunta {ordem}",
            tipo=PerguntaModelo.Tipo.ESCALA_1_5,
            ordem=ordem,
        )
        for ordem in range(1, 4)
    ]
    client.force_login(coordenador)
    url = reverse("coordenacao_questionario_editar", args=(modelo.pk,))
    resposta = client.post(url, {"pergunta_id": perguntas[0].pk, "mover": "descer"})
    assert resposta.status_code == 200
    assert list(modelo.perguntas_modelo.values_list("texto", flat=True)) == ["Pergunta 2", "Pergunta 1", "Pergunta 3"]
    resposta = client.post(
        url,
        {
            "pergunta_id": perguntas[1].pk,
            "editar": "Salvar pergunta",
            "texto": "Pergunta revisada",
            "tipo": PerguntaModelo.Tipo.TEXTO,
            "dimensao": "",
            "obrigatoria": "on",
        },
    )
    assert resposta.status_code == 200
    assert PerguntaModelo.objects.get(pk=perguntas[1].pk).texto == "Pergunta revisada"
    client.post(url, {"pergunta_id": perguntas[2].pk, "remover": "Remover"})
    assert list(modelo.perguntas_modelo.values_list("ordem", flat=True)) == [1, 2]


@pytest.mark.django_db
def test_view_reordenacao_ajax_retorna_json(client, coordenador):
    modelo = ModeloQuestionario.objects.create(escola=coordenador.escola, nome="AJAX")
    perguntas = [
        PerguntaModelo.objects.create(
            modelo=modelo,
            texto=f"Pergunta {ordem}",
            tipo=PerguntaModelo.Tipo.ESCALA_1_5,
            ordem=ordem,
        )
        for ordem in range(1, 3)
    ]
    client.force_login(coordenador)
    resposta = client.post(
        reverse("coordenacao_questionario_editar", args=(modelo.pk,)),
        {"pergunta_id": perguntas[0].pk, "mover": "descer"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        HTTP_ACCEPT="application/json",
    )
    assert resposta.status_code == 200
    assert resposta.json()["ok"] is True


@pytest.mark.django_db
def test_view_bloqueia_limites_de_15_perguntas_e_3_textos(client, coordenador):
    modelo = ModeloQuestionario.objects.create(escola=coordenador.escola, nome="Limites")
    PerguntaModelo.objects.bulk_create(
        [
            PerguntaModelo(
                modelo=modelo,
                texto=f"Escala {ordem}",
                tipo=PerguntaModelo.Tipo.ESCALA_1_5,
                ordem=ordem,
            )
            for ordem in range(1, 16)
        ]
    )
    client.force_login(coordenador)
    url = reverse("coordenacao_questionario_editar", args=(modelo.pk,))
    client.post(url, {"adicionar": "Adicionar", "texto": "Excedente", "tipo": PerguntaModelo.Tipo.ESCALA_1_5})
    assert modelo.perguntas_modelo.count() == 15
    modelo.perguntas_modelo.all().delete()
    PerguntaModelo.objects.bulk_create(
        [
            PerguntaModelo(
                modelo=modelo,
                texto=f"Texto {ordem}",
                tipo=PerguntaModelo.Tipo.TEXTO,
                ordem=ordem,
            )
            for ordem in range(1, 4)
        ]
    )
    client.post(url, {"adicionar": "Adicionar", "texto": "Quarto texto", "tipo": PerguntaModelo.Tipo.TEXTO})
    assert modelo.perguntas_modelo.count() == 3
