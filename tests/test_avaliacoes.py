from pathlib import Path

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.urls import reverse

from apps.avaliacoes.admin import (
    AvaliacaoAdmin,
    RespostaEscalaAdmin,
    RespostaTextoAdmin,
)
from apps.avaliacoes.models import (
    Avaliacao,
    CicloAvaliacao,
    Participacao,
    Pergunta,
    RespostaEscala,
    RespostaTexto,
    ResumoVinculo,
)
from apps.avaliacoes.services import criar_ciclo_com_questionario, gerar_resumos
from apps.contas.models import Usuario
from apps.escolas.models import Disciplina, Escola, Matricula, Turma, Vinculo


def criar_usuario(escola, email, role, nome):
    return Usuario.objects.create_user(
        email=email,
        password="Senha-forte-123!",
        nome=nome,
        role=role,
        escola=escola,
    )


@pytest.fixture
def contexto(db):
    escola = Escola.objects.create(nome="Escola Escuta")
    turma = Turma.objects.create(escola=escola, nome="8º A", ano_letivo=2026)
    disciplina = Disciplina.objects.create(escola=escola, nome="Matemática")
    professor = criar_usuario(
        escola, "professor@escuta.example", Usuario.Role.PROFESSOR, "Professor"
    )
    aluno = criar_usuario(escola, "aluno@escuta.example", Usuario.Role.ALUNO, "Aluno")
    coord = criar_usuario(
        escola, "coord@escuta.example", Usuario.Role.COORDENACAO, "Coordenação"
    )
    vinculo = Vinculo.objects.create(
        professor=professor, turma=turma, disciplina=disciplina
    )
    Matricula.objects.create(aluno=aluno, turma=turma)
    ciclo = criar_ciclo_com_questionario(escola, "Escuta do primeiro semestre")
    return {
        "escola": escola,
        "turma": turma,
        "professor": professor,
        "aluno": aluno,
        "coord": coord,
        "vinculo": vinculo,
        "ciclo": ciclo,
    }


def postar_respostas(client, contexto, **overrides):
    dados = {"confirmacao": "on"}
    for pergunta in Pergunta.objects.filter(ciclo=contexto["ciclo"]):
        dados[f"pergunta_{pergunta.pk}"] = (
            overrides.get(f"pergunta_{pergunta.pk}", "4")
            if pergunta.tipo == Pergunta.Tipo.ESCALA_1_5
            else overrides.get(f"pergunta_{pergunta.pk}", "Uma observação cuidadosa.")
        )
    return client.post(reverse("aluno_avaliar", args=[contexto["vinculo"].pk]), dados)


def test_conteudo_anonimo_nao_alcanca_usuario_nem_tem_tempo():
    modelos = (Avaliacao, RespostaEscala, RespostaTexto)
    visitados = set()

    def modelos_relacionados(modelo):
        if modelo in visitados:
            return set()
        visitados.add(modelo)
        relacionados = set()
        for campo in modelo._meta.get_fields():
            if campo.is_relation and not campo.auto_created and campo.related_model:
                relacionados.add(campo.related_model)
                relacionados.update(modelos_relacionados(campo.related_model))
        return relacionados

    for modelo in modelos:
        campos = modelo._meta.get_fields()
        assert Usuario not in modelos_relacionados(modelo)
        assert not any(
            getattr(campo, "auto_now", False)
            or getattr(campo, "auto_now_add", False)
            or campo.get_internal_type() in {"DateField", "DateTimeField", "TimeField"}
            for campo in campos
        )


def test_ciclo_cria_seis_escalas_e_duas_perguntas_de_texto(client, contexto):
    client.force_login(contexto["coord"])
    response = client.get(reverse("coordenacao_ciclos"))

    assert response.status_code == 200
    assert (
        Pergunta.objects.filter(ciclo=contexto["ciclo"], tipo="ESCALA_1_5").count() == 6
    )
    assert Pergunta.objects.filter(ciclo=contexto["ciclo"], tipo="TEXTO").count() == 2
    assert {
        p.dimensao
        for p in Pergunta.objects.filter(ciclo=contexto["ciclo"], tipo="ESCALA_1_5")
    } == {
        "clareza",
        "escuta",
        "ritmo",
        "organização",
        "incentivo",
        "acolhimento",
    }


def test_questionario_tem_escala_visual_e_acoes_de_conta(client, contexto):
    client.force_login(contexto["aluno"])

    response = client.get(reverse("aluno_avaliar", args=[contexto["vinculo"].pk]))
    content = response.content.decode()

    assert response.status_code == 200
    assert "questionnaire-card" in content
    assert "scale-options" in content
    assert "consent-field" in content
    assert "/static/js/questionnaire.js" in content
    assert "Voltar" in content
    assert 'action="/sair/"' in content


def test_questionario_impede_submit_invalido_e_rola_ate_o_campo():
    script = Path("static/js/questionnaire.js").read_text()

    assert "form.checkValidity()" in script
    assert "event.preventDefault()" in script
    assert "scrollIntoView" in script
    assert 'block: "center"' in script
    assert "markInvalidState" in script
    assert "client-invalid-message" in script
    assert 'target.querySelector(".scale-options")' in script
    assert 'target.querySelector("textarea")' in script
    assert "clearValidTarget" in script
    assert "controls.every((field) => field.checkValidity())" in script
    assert "is-invalid-focus" not in script
    assert "is-invalid-focus" not in Path("tailwind/input.css").read_text()
    assert ".consent-field + .client-invalid-message" in Path("tailwind/input.css").read_text()


def test_conclusao_nao_duplica_o_retorno_da_conta(client, contexto):
    client.force_login(contexto["aluno"])

    response = client.get(reverse("aluno_obrigado"))
    content = response.content.decode()

    assert response.status_code == 200
    assert content.count("Voltar") == 1
    assert "Voltar para minhas pendências" not in content


def test_coordena_nao_abre_segundo_ciclo_nao_publicado(client, contexto):
    client.force_login(contexto["coord"])
    response = client.post(reverse("coordenacao_ciclos"), {"nome": "Outro ciclo"})

    assert response.status_code == 200
    assert CicloAvaliacao.objects.filter(escola=contexto["escola"]).count() == 1
    assert "Já existe um ciclo não publicado" in response.content.decode()


def test_envio_valido_cria_participacao_e_conteudo_sem_aluno(client, contexto):
    client.force_login(contexto["aluno"])

    response = client.get(reverse("aluno_avaliar", args=[contexto["vinculo"].pk]))
    envio = postar_respostas(client, contexto)

    assert response.status_code == 200
    assert envio.status_code == 302
    assert envio.url == reverse("aluno_obrigado")
    assert Participacao.objects.filter(aluno=contexto["aluno"]).count() == 1
    assert Avaliacao.objects.count() == 1
    assert RespostaEscala.objects.count() == 6
    assert RespostaTexto.objects.count() == 2
    assert not hasattr(Avaliacao.objects.first(), "aluno")
    agradecimento = client.get(reverse("aluno_obrigado")).content.decode()
    assert contexto["aluno"].email not in agradecimento
    assert contexto["aluno"].nome not in agradecimento


def test_envio_duplicado_mostra_mensagem_e_nao_cria_novo_conteudo(client, contexto):
    client.force_login(contexto["aluno"])
    postar_respostas(client, contexto)
    segunda = postar_respostas(client, contexto)

    assert segunda.status_code == 200
    assert "já foi registrada" in segunda.content.decode()
    assert Participacao.objects.filter(aluno=contexto["aluno"]).count() == 1
    assert Avaliacao.objects.count() == 1
    assert RespostaEscala.objects.count() == 6
    assert RespostaTexto.objects.count() == 2


def test_ciclo_fechado_nao_recebe_avaliacao(client, contexto):
    contexto["ciclo"].status = CicloAvaliacao.Status.FECHADO
    contexto["ciclo"].save(update_fields=("status",))
    client.force_login(contexto["aluno"])

    response = client.get(reverse("aluno_avaliar", args=[contexto["vinculo"].pk]))
    envio = client.post(reverse("aluno_avaliar", args=[contexto["vinculo"].pk]))

    assert response.status_code == 404
    assert envio.status_code == 404
    assert not Participacao.objects.exists()
    assert not Avaliacao.objects.exists()


def test_aluno_de_outra_turma_nao_pode_enviar(client, contexto):
    outra_turma = Turma.objects.create(
        escola=contexto["escola"], nome="9º B", ano_letivo=2026
    )
    outro_vinculo = Vinculo.objects.create(
        professor=contexto["professor"],
        turma=outra_turma,
        disciplina=Disciplina.objects.get(escola=contexto["escola"], nome="Matemática"),
    )
    client.force_login(contexto["aluno"])

    response = client.get(reverse("aluno_avaliar", args=[outro_vinculo.pk]))

    assert response.status_code == 404
    assert not Avaliacao.objects.exists()


def test_aluno_de_outra_escola_nao_pode_enviar(client, contexto):
    outra_escola = Escola.objects.create(nome="Escola Distante")
    turma = Turma.objects.create(escola=outra_escola, nome="8º A", ano_letivo=2026)
    disciplina = Disciplina.objects.create(escola=outra_escola, nome="História")
    professor = criar_usuario(
        outra_escola,
        "professor@distante.example",
        Usuario.Role.PROFESSOR,
        "Professor distante",
    )
    outro_vinculo = Vinculo.objects.create(
        professor=professor, turma=turma, disciplina=disciplina
    )
    client.force_login(contexto["aluno"])

    response = client.get(reverse("aluno_avaliar", args=[outro_vinculo.pk]))

    assert response.status_code == 404
    assert not Avaliacao.objects.exists()


def test_admin_conteudo_anonimo_e_somente_leitura():
    site = AdminSite()
    request = RequestFactory().get("/admin/")
    request.user = object()
    for admin_class, model in (
        (AvaliacaoAdmin, Avaliacao),
        (RespostaEscalaAdmin, RespostaEscala),
        (RespostaTextoAdmin, RespostaTexto),
    ):
        admin_obj = admin_class(model, site)
        assert admin_obj.has_add_permission(request) is False
        assert admin_obj.has_delete_permission(request) is False
        assert admin_obj.has_change_permission(request) is False
        assert admin_obj.get_actions(request) == {}


def criar_avaliacoes_agregadas(contexto, quantidade=5, status_texto=None):
    perguntas = list(Pergunta.objects.filter(ciclo=contexto["ciclo"]))
    for indice in range(quantidade):
        avaliacao = Avaliacao.objects.create(
            ciclo=contexto["ciclo"], vinculo=contexto["vinculo"].pk
        )
        for pergunta in perguntas:
            if pergunta.tipo == Pergunta.Tipo.ESCALA_1_5:
                RespostaEscala.objects.create(
                    avaliacao=avaliacao, pergunta=pergunta, valor=4
                )
            else:
                RespostaTexto.objects.create(
                    avaliacao=avaliacao,
                    pergunta=pergunta,
                    texto=(f"Comentário {indice}" if indice == 0 else ""),
                    **(
                        {"status_moderacao": status_texto}
                        if status_texto
                        else {}
                    ),
                )


def publicar_com_resultado(contexto):
    criar_avaliacoes_agregadas(contexto)
    gerar_resumos(contexto["ciclo"])
    contexto["ciclo"].status = CicloAvaliacao.Status.PUBLICADO
    contexto["ciclo"].save(update_fields=("status",))


def test_coordenacao_encerrar_exibe_adesao_agregada_sem_nomes(client, contexto):
    Participacao.objects.create(
        aluno=contexto["aluno"], ciclo=contexto["ciclo"], vinculo=contexto["vinculo"]
    )
    client.force_login(contexto["coord"])
    response = client.get(reverse("coordenacao_ciclos"))
    content = response.content.decode()

    assert "1 / 1" in content
    assert ">Aluno<" not in content
    assert contexto["aluno"].email not in content
    assert "Encerrar" in content

    encerramento = client.post(
        reverse("coordenacao_encerrar_ciclo", args=[contexto["ciclo"].pk])
    )
    assert encerramento.status_code == 302
    contexto["ciclo"].refresh_from_db()
    assert contexto["ciclo"].status == CicloAvaliacao.Status.FECHADO


def test_publicacao_e_bloqueada_com_moderacao_pendente(client, contexto):
    avaliacao = Avaliacao.objects.create(
        ciclo=contexto["ciclo"], vinculo=contexto["vinculo"].pk
    )
    pergunta = Pergunta.objects.filter(ciclo=contexto["ciclo"], tipo=Pergunta.Tipo.TEXTO).first()
    pendente = RespostaTexto.objects.create(
        avaliacao=avaliacao, pergunta=pergunta, texto="Comentário para moderar"
    )
    contexto["ciclo"].status = CicloAvaliacao.Status.FECHADO
    contexto["ciclo"].save(update_fields=("status",))
    client.force_login(contexto["coord"])

    bloqueio = client.post(
        reverse("coordenacao_publicar_ciclo", args=[contexto["ciclo"].pk])
    )

    assert bloqueio.status_code == 302
    contexto["ciclo"].refresh_from_db()
    assert contexto["ciclo"].status == CicloAvaliacao.Status.FECHADO
    assert not ResumoVinculo.objects.exists()
    assert "Comentários para escutar" in client.get(reverse("coordenacao_ciclos")).content.decode()

    moderacao = client.post(
        reverse("coordenacao_moderar_resposta", args=[pendente.pk]),
        {"acao": "aprovar"},
    )
    assert moderacao.status_code == 302
    pendente.refresh_from_db()
    assert pendente.status_moderacao == RespostaTexto.StatusModeracao.APROVADO


def test_resultado_abaixo_do_limiar_nao_aparece_para_professor(client, contexto):
    criar_avaliacoes_agregadas(contexto, quantidade=4)
    gerar_resumos(contexto["ciclo"])
    contexto["ciclo"].status = CicloAvaliacao.Status.PUBLICADO
    contexto["ciclo"].save(update_fields=("status",))
    client.force_login(contexto["professor"])

    response = client.get(reverse("professor"))

    assert response.status_code == 200
    assert not ResumoVinculo.objects.exists()
    assert "participação suficiente" in response.content.decode()
    assert "Comentário 0" not in response.content.decode()


def test_professor_ve_apenas_proprio_vinculo_e_comentarios_aprovados(client, contexto):
    publicar_com_resultado(contexto)
    resposta = RespostaTexto.objects.filter(avaliacao__ciclo=contexto["ciclo"]).exclude(texto="").first()
    resposta.status_moderacao = RespostaTexto.StatusModeracao.APROVADO
    resposta.save(update_fields=("status_moderacao",))
    outro_professor = criar_usuario(
        contexto["escola"], "outro@escuta.example", Usuario.Role.PROFESSOR, "Outro professor"
    )
    outro_vinculo = Vinculo.objects.create(
        professor=outro_professor,
        turma=contexto["turma"],
        disciplina=Disciplina.objects.create(escola=contexto["escola"], nome="História"),
    )
    ResumoVinculo.objects.create(
        ciclo=contexto["ciclo"], vinculo_id=outro_vinculo.pk, n_avaliacoes=5,
        medias_por_dimensao={"clareza": 2.0},
    )
    client.force_login(contexto["professor"])

    response = client.get(reverse("professor"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Matemática" in content
    assert "Comentário 0" in content
    assert "História" not in content
    assert "Outro professor" not in content
    assert 'order_by("?")' in Path("apps/contas/views.py").read_text()


def test_ciclo_aberto_ou_fechado_nao_mostra_resultados(client, contexto):
    criar_avaliacoes_agregadas(contexto)
    gerar_resumos(contexto["ciclo"])
    client.force_login(contexto["professor"])

    aberto = client.get(reverse("professor"))
    assert "Matemática" not in aberto.content.decode()

    contexto["ciclo"].status = CicloAvaliacao.Status.FECHADO
    contexto["ciclo"].save(update_fields=("status",))
    fechado = client.get(reverse("professor"))
    assert "Matemática" not in fechado.content.decode()


def test_escola_diferente_nao_acessa_ciclo_nem_resultado(client, contexto):
    outra_escola = Escola.objects.create(nome="Escola Distante")
    outra_coord = criar_usuario(
        outra_escola, "coord@distante.example", Usuario.Role.COORDENACAO, "Outra coordenação"
    )
    client.force_login(outra_coord)

    response = client.post(
        reverse("coordenacao_encerrar_ciclo", args=[contexto["ciclo"].pk])
    )

    assert response.status_code == 404
    contexto["ciclo"].refresh_from_db()
    assert contexto["ciclo"].status == CicloAvaliacao.Status.ABERTO


def test_admin_resumo_e_somente_leitura():
    from apps.avaliacoes.admin import ResumoVinculoAdmin

    site = AdminSite()
    request = RequestFactory().get("/admin/")
    request.user = object()
    admin_obj = ResumoVinculoAdmin(ResumoVinculo, site)
    assert admin_obj.has_add_permission(request) is False
    assert admin_obj.has_delete_permission(request) is False
    assert admin_obj.has_change_permission(request) is False
    assert admin_obj.get_actions(request) == {}
