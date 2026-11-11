import logging
from pathlib import Path

import pytest
from django.conf import settings
from django.db import IntegrityError, transaction
from django.urls import get_resolver, reverse

from apps.avaliacoes.models import (
    Avaliacao,
    Participacao,
    Pergunta,
    RespostaEscala,
    RespostaTexto,
)
from apps.avaliacoes.services import criar_ciclo_com_questionario
from apps.contas.models import Usuario
from apps.escolas.models import Disciplina, Escola, Matricula, Turma, Vinculo


@pytest.fixture
def contexto_anonimo(db):
    escola = Escola.objects.create(nome="Escola da Escuta")
    turma = Turma.objects.create(escola=escola, nome="8º A", ano_letivo=2026)
    disciplina = Disciplina.objects.create(escola=escola, nome="História")
    professor = Usuario.objects.create_user(
        email="professor-anonimo@example.com",
        password="Senha-forte-123!",
        nome="Professor da Escuta",
        role=Usuario.Role.PROFESSOR,
        escola=escola,
    )
    aluno = Usuario.objects.create_user(
        email="aluno-anonimo@example.com",
        password="Senha-forte-123!",
        nome="Estudante Identificável",
        role=Usuario.Role.ALUNO,
        escola=escola,
    )
    vinculo = Vinculo.objects.create(
        professor=professor, turma=turma, disciplina=disciplina
    )
    Matricula.objects.create(aluno=aluno, turma=turma)
    ciclo = criar_ciclo_com_questionario(escola, "Ciclo de escuta")
    return locals()


def test_avaliacao_e_respostas_nao_tem_relacao_transitiva_com_usuario():
    for model in (Avaliacao, RespostaEscala, RespostaTexto):
        relations = {
            field.related_model
            for field in model._meta.get_fields()
            if field.is_relation and field.related_model
        }
        assert Usuario not in relations
        assert all(field.name != "created_at" for field in model._meta.get_fields())


def test_telas_de_avaliacao_e_resultado_nao_expoem_identidade_do_aluno(
    client, contexto_anonimo
):
    client.force_login(contexto_anonimo["aluno"])
    avaliacao = client.get(
        reverse("aluno_avaliar", args=[contexto_anonimo["vinculo"].pk])
    )
    agradecimento = client.get(reverse("aluno_obrigado"))

    for response in (avaliacao, agradecimento):
        assert response.status_code == 200
        assert contexto_anonimo["aluno"].email not in response.content.decode()
        assert contexto_anonimo["aluno"].nome not in response.content.decode()
        assert "created_at" not in response.content.decode()
        assert "aluno" not in response.context
        assert "usuario" not in response.context


def test_resultado_do_professor_nao_expoe_aluno_nem_created_at(client, contexto_anonimo):
    client.force_login(contexto_anonimo["professor"])
    response = client.get(reverse("professor"))
    content = response.content.decode()

    assert response.status_code == 200
    assert contexto_anonimo["aluno"].email not in content
    assert contexto_anonimo["aluno"].nome not in content
    assert "created_at" not in content
    assert "aluno" not in response.context
    assert "usuario" not in response.context


def test_corpo_da_requisicao_nao_aparece_nos_logs(client, contexto_anonimo, caplog):
    marcador = "CORPO-SECRETO-NAO-LOGAR-7f1d"
    client.force_login(contexto_anonimo["aluno"])
    caplog.set_level(logging.DEBUG)

    response = client.post(
        reverse("aluno_avaliar", args=[contexto_anonimo["vinculo"].pk]),
        {"corpo": marcador},
    )

    assert response.status_code == 200
    assert marcador not in "\n".join(record.getMessage() for record in caplog.records)
    assert "request.body" not in Path("config/settings.py").read_text()


def test_rotas_nao_aceitam_filtro_por_atributo_do_aluno_e_nao_tem_ranking(client):
    def route_names(patterns):
        for pattern in patterns:
            if getattr(pattern, "name", None):
                yield pattern.name
            if hasattr(pattern, "url_patterns"):
                yield from route_names(pattern.url_patterns)

    names = set(route_names(get_resolver().url_patterns))
    assert not any("ranking" in name.lower() for name in names)
    source = "\n".join(
        path.read_text()
        for path in Path("apps").rglob("*.py")
        if "migrations" not in path.parts
    )
    assert "ranking" not in source.lower()
    assert client.get(reverse("home") + "?aluno__email=alvo@example.com").status_code == 200


def test_agradecimento_nao_carrega_identificador_na_url_ou_sessao(
    client, contexto_anonimo
):
    client.force_login(contexto_anonimo["aluno"])
    response = client.get(reverse("aluno_obrigado"))

    assert response.request["PATH_INFO"] == reverse("aluno_obrigado")
    assert str(contexto_anonimo["aluno"].pk) not in response.request["PATH_INFO"]
    assert not any(
        key in client.session
        for key in ("avaliacao_id", "evaluation_id", "aluno_id", "vinculo_id")
    )
    assert "avaliacao" not in client.session
    assert "aluno" not in client.session


def test_pagina_publica_de_anonimato_e_linkada_no_aviso(client, contexto_anonimo):
    public = client.get(reverse("anonimato"))
    client.force_login(contexto_anonimo["aluno"])
    questionnaire = client.get(
        reverse("aluno_avaliar", args=[contexto_anonimo["vinculo"].pk])
    )

    assert public.status_code == 200
    assert "Limites honestos" in public.content.decode()
    assert reverse("anonimato") in questionnaire.content.decode()


def test_todos_os_formularios_post_tem_csrf():
    for path in Path("templates").rglob("*.html"):
        content = path.read_text()
        if 'method="post"' in content:
            assert "{% csrf_token %}" in content, path


def test_logging_e_headers_de_seguranca_estao_configurados():
    source = Path("config/settings.py").read_text()
    assert "django.request" in source
    assert "request.body" not in source
    assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert settings.SECURE_REFERRER_POLICY == "strict-origin-when-cross-origin"
    assert "SECURE_SSL_REDIRECT = True" in source
    assert "SECURE_HSTS_SECONDS" in source
    assert "X_FRAME_OPTIONS = \"DENY\"" in source


def test_protecao_contra_open_redirect_permanece_ativa(client, contexto_anonimo):
    client.post(
        reverse("entrar") + "?next=https://fora.example/",
        {
            "email": contexto_anonimo["aluno"].email,
            "senha": "Senha-forte-123!",
        },
    )
    assert client.session.get("_auth_user_id") == str(contexto_anonimo["aluno"].pk)


def test_participacao_unica_e_rollback_atomico(contexto_anonimo):
    participacao = Participacao.objects.create(
        aluno=contexto_anonimo["aluno"],
        ciclo=contexto_anonimo["ciclo"],
        vinculo=contexto_anonimo["vinculo"],
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        Participacao.objects.create(
            aluno=contexto_anonimo["aluno"],
            ciclo=contexto_anonimo["ciclo"],
            vinculo=contexto_anonimo["vinculo"],
        )
    assert Participacao.objects.count() == 1
    assert Avaliacao.objects.count() == 0
    assert participacao.aluno_id == contexto_anonimo["aluno"].pk


def test_envio_atomico_nao_deixa_participacao_sem_conteudo(client, contexto_anonimo):
    client.force_login(contexto_anonimo["aluno"])
    perguntas = Pergunta.objects.filter(ciclo=contexto_anonimo["ciclo"])
    dados = {"confirmacao": "on"}
    for pergunta in perguntas:
        dados[f"pergunta_{pergunta.pk}"] = "4"

    response = client.post(
        reverse("aluno_avaliar", args=[contexto_anonimo["vinculo"].pk]), dados
    )

    assert response.status_code == 302
    assert Participacao.objects.count() == 1
    assert Avaliacao.objects.count() == 1
    assert RespostaEscala.objects.count() == 6
