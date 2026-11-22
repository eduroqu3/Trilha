from io import StringIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.urls import reverse

from apps.contas.models import Usuario
from apps.escolas.models import Disciplina, Escola, Matricula, Turma, Vinculo


@pytest.fixture
def escola(db):
    return Escola.objects.create(nome="Escola Horizonte")


@pytest.fixture
def coordenacao(escola):
    return Usuario.objects.create_user(
        email="coordenacao@horizonte.example",
        password="Senha-forte-123!",
        nome="Coordenação Horizonte",
        role=Usuario.Role.COORDENACAO,
        escola=escola,
    )


@pytest.fixture
def outra_coordenacao(db):
    escola = Escola.objects.create(nome="Escola Caminhos")
    usuario = Usuario.objects.create_user(
        email="coordenacao@caminhos.example",
        password="Senha-forte-123!",
        nome="Coordenação Caminhos",
        role=Usuario.Role.COORDENACAO,
        escola=escola,
    )
    return usuario


def login_coord(client, usuario):
    client.force_login(usuario)


def arquivo_csv(conteudo):
    return SimpleUploadedFile(
        "pessoas.csv", conteudo.encode("utf-8"), content_type="text/csv"
    )


def test_isolamento_por_escola_na_lista_e_na_remocao(
    client, coordenacao, outra_coordenacao
):
    turma_visivel = Turma.objects.create(
        escola=coordenacao.escola, nome="6º A", ano_letivo=2026
    )
    turma_oculta = Turma.objects.create(
        escola=outra_coordenacao.escola, nome="7º B", ano_letivo=2026
    )
    login_coord(client, coordenacao)

    response = client.get(reverse("coordenacao_turmas"))

    assert response.status_code == 200
    assert "6º A" in response.content.decode()
    assert "7º B" not in response.content.decode()
    delete_response = client.post(reverse("remover_turma", args=[turma_oculta.pk]))
    assert delete_response.status_code == 404
    assert Turma.objects.filter(pk=turma_oculta.pk).exists()
    assert Turma.objects.filter(pk=turma_visivel.pk).exists()


def test_papel_nao_coordena_nao_acessa_gestao(client, escola):
    aluno = Usuario.objects.create_user(
        email="aluno@horizonte.example",
        password="Senha-forte-123!",
        nome="Aluno",
        role=Usuario.Role.ALUNO,
        escola=escola,
    )
    login_coord(client, aluno)

    response = client.get(reverse("coordenacao_turmas"))

    assert response.status_code == 302
    assert response.url == reverse("home")


@pytest.mark.parametrize(
    "url_name",
    [
        "coordenacao_ciclos",
        "coordenacao_turmas",
        "coordenacao_professores",
        "coordenacao_alunos",
        "coordenacao_vinculos",
    ],
)
def test_telas_da_coordenacao_exibem_acoes_de_conta(client, coordenacao, url_name):
    login_coord(client, coordenacao)

    response = client.get(reverse(url_name))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Voltar" in content
    assert 'action="/sair/"' in content


def test_coordenacao_disciplinas_redireciona_para_turmas(client, coordenacao):
    login_coord(client, coordenacao)

    response = client.get(reverse("coordenacao_disciplinas"))
    assert response.status_code == 302
    assert response.url == reverse("coordenacao_turmas")


def test_coordena_cadastra_turma_e_disciplina(client, coordenacao):
    login_coord(client, coordenacao)

    turma_response = client.post(
        reverse("coordenacao_turmas"), {"nome": "8º ano A", "ano_letivo": 2026}
    )
    disciplina_response = client.post(
        reverse("coordenacao_disciplinas"), {"nome": "História"}
    )

    assert turma_response.status_code == 302
    assert disciplina_response.status_code == 302
    assert Turma.objects.filter(escola=coordenacao.escola, nome="8º ano A").exists()
    assert Disciplina.objects.filter(
        escola=coordenacao.escola, nome="História"
    ).exists()


def test_cadastro_individual_de_professor_e_aluno_exibe_senha_uma_vez(
    client, coordenacao
):
    turma = Turma.objects.create(
        escola=coordenacao.escola, nome="9º ano A", ano_letivo=2026
    )
    login_coord(client, coordenacao)

    professor_response = client.post(
        reverse("coordenacao_professores"),
        {"nome": "Professora Lúcia", "email": "lucia@example.com"},
    )
    aluno_response = client.post(
        reverse("coordenacao_alunos"),
        {
            "nome": "João Aluno",
            "email": "joao@example.com",
            "turma": turma.pk,
        },
    )

    assert professor_response.status_code == 200
    assert aluno_response.status_code == 200
    assert Usuario.objects.filter(email="lucia@example.com", role="PROFESSOR").exists()
    aluno = Usuario.objects.get(email="joao@example.com")
    assert Matricula.objects.filter(aluno=aluno, turma=turma).exists()
    assert b"Senha provis\xc3\xb3ria" in professor_response.content
    assert b"Senha provis\xc3\xb3ria" in aluno_response.content
    assert b"Baixar CSV" in professor_response.content


def test_importacao_csv_valida_professores_e_rejeita_linhas_invalidas(
    client, coordenacao
):
    login_coord(client, coordenacao)
    response = client.post(
        reverse("importar_professores"),
        {
            "arquivo": arquivo_csv(
                "nome,email\nAna,ana@example.com\nInválido,nao-email\n"
            )
        },
    )

    assert response.status_code == 200
    assert Usuario.objects.filter(email="ana@example.com").exists()
    assert not Usuario.objects.filter(email="nao-email").exists()
    assert "Linha 3" in response.content.decode()


def test_importacao_csv_valida_alunos_e_turma_desconhecida(coordenacao, client):
    turma = Turma.objects.create(
        escola=coordenacao.escola, nome="7º ano A", ano_letivo=2026
    )
    login_coord(client, coordenacao)
    response = client.post(
        reverse("importar_alunos"),
        {
            "arquivo": arquivo_csv(
                "nome,email,turma\nBia,bia@example.com,7º ano A\nCa,ca@example.com,Outra\n"
            )
        },
    )

    assert response.status_code == 200
    aluno = Usuario.objects.get(email="bia@example.com")
    assert Matricula.objects.filter(aluno=aluno, turma=turma).exists()
    assert not Usuario.objects.filter(email="ca@example.com").exists()
    assert "turma não encontrada" in response.content.decode()


def test_vinculo_duplicado_e_rejeitado(client, coordenacao):
    professor = Usuario.objects.create_user(
        email="prof@example.com",
        password="Senha-forte-123!",
        nome="Professor",
        role=Usuario.Role.PROFESSOR,
        escola=coordenacao.escola,
    )
    turma = Turma.objects.create(
        escola=coordenacao.escola, nome="6º A", ano_letivo=2026
    )
    disciplina = Disciplina.objects.create(escola=coordenacao.escola, nome="Matemática")
    dados = {"professor": professor.pk, "turma": turma.pk, "disciplina": disciplina.pk}
    login_coord(client, coordenacao)

    primeira = client.post(reverse("coordenacao_vinculos"), dados)
    segunda = client.post(reverse("coordenacao_vinculos"), dados)

    assert primeira.status_code == 302
    assert segunda.status_code == 200
    assert (
        Vinculo.objects.filter(
            professor=professor, turma=turma, disciplina=disciplina
        ).count()
        == 1
    )


def test_seed_demo_recusa_ambiente_de_producao():
    with (
        override_settings(DEBUG=False, ALLOW_SEED_DEMO=False),
        pytest.raises(CommandError, match="seed_demo bloqueado"),
    ):
        call_command("seed_demo", stdout=StringIO())


def test_seed_demo_autorizado_cria_cenario_completo(db):
    saida = StringIO()

    with override_settings(DEBUG=True, ALLOW_SEED_DEMO=False):
        call_command("seed_demo", stdout=saida)

    assert Escola.objects.filter(nome="Escola Horizonte Demo").exists()
    assert Turma.objects.filter(escola__nome="Escola Horizonte Demo").count() == 2
    assert Disciplina.objects.filter(escola__nome="Escola Horizonte Demo").count() == 3
    assert (
        Usuario.objects.filter(
            escola__nome="Escola Horizonte Demo", role="ALUNO"
        ).count()
        == 12
    )
    assert (
        Usuario.objects.filter(
            escola__nome="Escola Horizonte Demo", role="PROFESSOR"
        ).count()
        == 3
    )
    assert (
        Usuario.objects.filter(
            escola__nome="Escola Horizonte Demo", role="COORDENACAO"
        ).count()
        == 1
    )
    assert (
        Matricula.objects.filter(turma__escola__nome="Escola Horizonte Demo").count()
        == 12
    )
    assert (
        Vinculo.objects.filter(turma__escola__nome="Escola Horizonte Demo").count() == 3
    )
    assert "Credenciais de teste" in saida.getvalue()
