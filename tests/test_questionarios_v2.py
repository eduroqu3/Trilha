import pytest
from django.core.exceptions import ValidationError

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
from apps.escolas.models import Escola


@pytest.fixture
def escolas(db):
    return Escola.objects.create(nome="Escola V2 A"), Escola.objects.create(nome="Escola V2 B")


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
        PerguntaModelo.objects.create(modelo=modelo, texto="Qual é seu nome?", tipo=PerguntaModelo.Tipo.ESCALA_1_5, ordem=1)
    for ordem in range(1, 5):
        PerguntaModelo.objects.create(modelo=modelo, texto=f"Pergunta segura {ordem}", tipo=PerguntaModelo.Tipo.ESCALA_1_5, ordem=ordem)
    with pytest.raises(ValidationError):
        modelo.clean()


@pytest.mark.django_db
def test_escolha_unica_exige_de_duas_a_seis_opcoes():
    escola = Escola.objects.create(nome="Escola escolhas")
    modelo = ModeloQuestionario.objects.create(escola=escola, nome="Escolhas")
    with pytest.raises(ValidationError):
        PerguntaModelo.objects.create(modelo=modelo, texto="Como foi a aula?", tipo=PerguntaModelo.Tipo.ESCOLHA_UNICA, ordem=1, opcoes=["uma"])


@pytest.mark.django_db
def test_ciclos_legados_continuam_com_snapshot_de_perguntas(escolas):
    escola_a, _ = escolas
    ciclo = CicloAvaliacao.objects.create(escola=escola_a, nome="Legado", status=CicloAvaliacao.Status.ABERTO)
    Pergunta.objects.create(ciclo=ciclo, texto="Pergunta legada", tipo=Pergunta.Tipo.ESCALA_1_5, ordem=1)
    assert ciclo.modelo_questionario_id is None
    assert ciclo.perguntas.count() == 1
