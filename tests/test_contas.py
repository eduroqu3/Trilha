from pathlib import Path

import pytest
from django.core.cache import cache
from django.urls import reverse

from apps.contas.models import Usuario
from apps.escolas.models import Escola


@pytest.fixture
def escola(db):
    return Escola.objects.create(nome="Escola Horizonte")


@pytest.fixture
def usuario(escola):
    return Usuario.objects.create_user(
        email="coord@example.com",
        password="Senha-forte-123!",
        nome="Coordenação",
        role=Usuario.Role.COORDENACAO,
        escola=escola,
    )


def dados_cadastro(email="responsavel@example.com"):
    return {
        "nome_escola": "Escola Caminhos",
        "nome_responsavel": "Ana Responsável",
        "email": email,
        "senha": "Senha-forte-123!",
        "confirmar_senha": "Senha-forte-123!",
        "website": "",
    }


def test_cadastro_cria_escola_e_coordenacao_e_autentica(client, db):
    response = client.post(reverse("cadastro_escola"), dados_cadastro())

    assert response.status_code == 302
    assert response.url == reverse("coordenacao")
    escola = Escola.objects.get(nome="Escola Caminhos")
    usuario = Usuario.objects.get(email="responsavel@example.com")
    assert usuario.role == Usuario.Role.COORDENACAO
    assert usuario.escola == escola
    assert escola.limiar_minimo == 5
    assert client.session.get("_auth_user_id") == str(usuario.pk)


def test_cadastro_rejeita_email_duplicado(client, usuario, db):
    response = client.post(
        reverse("cadastro_escola"), dados_cadastro("COORD@EXAMPLE.COM")
    )

    assert response.status_code == 200
    assert "Não foi possível concluir o cadastro" in response.content.decode()
    assert Escola.objects.count() == 1


def test_login_correto_redireciona_coordenacao(client, usuario):
    response = client.post(
        reverse("entrar"), {"email": usuario.email, "senha": "Senha-forte-123!"}
    )

    assert response.status_code == 302
    assert response.url == reverse("coordenacao")


def test_login_incorreto_nao_revela_se_email_existe(client, usuario):
    response = client.post(
        reverse("entrar"), {"email": usuario.email, "senha": "errada"}
    )

    assert response.status_code == 200
    assert "Não foi possível entrar com esses dados" in response.content.decode()
    assert "senha incorreta" not in response.content.decode().lower()


@pytest.mark.parametrize(
    ("role", "url_name"),
    [
        (Usuario.Role.ALUNO, "aluno"),
        (Usuario.Role.PROFESSOR, "professor"),
        (Usuario.Role.COORDENACAO, "coordenacao"),
    ],
)
def test_login_redireciona_por_papel(client, escola, role, url_name):
    user = Usuario.objects.create_user(
        email=f"{role.lower()}@example.com",
        password="Senha-forte-123!",
        nome="Pessoa da escola",
        role=role,
        escola=escola,
    )

    response = client.post(
        reverse("entrar"), {"email": user.email, "senha": "Senha-forte-123!"}
    )

    assert response.url == reverse(url_name)


def test_next_externo_e_ignorado(client, usuario):
    response = client.post(
        reverse("entrar") + "?next=https://malicioso.example/",
        {"email": usuario.email, "senha": "Senha-forte-123!"},
    )

    assert response.url == reverse("coordenacao")


def test_next_interno_e_aceito(client, usuario):
    response = client.post(
        reverse("entrar") + "?next=/conta/senha/",
        {"email": usuario.email, "senha": "Senha-forte-123!"},
    )

    assert response.url == "/conta/senha/"


def test_acesso_sem_login_redireciona_para_entrar(client):
    response = client.get(reverse("coordenacao"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("entrar"))


def test_papel_errado_e_bloqueado(client, usuario):
    client.force_login(usuario)

    response = client.get(reverse("aluno"))

    assert response.status_code == 302
    assert response.url == reverse("home")


def test_logout_somente_via_post(client, usuario):
    client.force_login(usuario)

    get_response = client.get(reverse("sair"))
    assert get_response.status_code == 302
    assert client.get(reverse("coordenacao_usuarios")).status_code == 200

    post_response = client.post(reverse("sair"))
    assert post_response.status_code == 302
    assert post_response.url == reverse("entrar")
    assert client.get(reverse("coordenacao_usuarios")).status_code == 302


def test_cadastro_honeypot_nao_cria_conta(client, db):
    cache.clear()
    response = client.post(
        reverse("cadastro_escola"), {**dados_cadastro(), "website": "bot"}
    )

    assert response.status_code == 200
    assert Escola.objects.count() == 0
    assert Usuario.objects.count() == 0


@pytest.mark.parametrize("url_name", ["entrar", "cadastro_escola"])
def test_telas_publicas_de_autenticacao_usam_logo_oficial(client, url_name):
    response = client.get(reverse(url_name))

    assert response.status_code == 200
    assert b"/static/img/logo-completo.png" in response.content


def test_troca_de_senha_usa_logo_oficial(client, usuario):
    client.force_login(usuario)

    response = client.get(reverse("trocar_senha"))

    assert response.status_code == 200
    assert b"/static/img/logo-completo.png" in response.content


def test_coordenacao_redireciona_para_usuarios(client, usuario):
    client.force_login(usuario)

    response = client.get(reverse("coordenacao"))

    assert response.status_code == 302
    assert response.url == reverse("coordenacao_usuarios")


def test_templates_de_painel_seguem_a_estrutura_por_papel():
    assert Path("templates/aluno/dashboard.html").exists()
    assert Path("templates/professor/dashboard.html").exists()
    assert not Path("templates/painel").exists()


@pytest.mark.parametrize(
    ("role", "url_name"),
    [
        (Usuario.Role.ALUNO, "aluno"),
        (Usuario.Role.PROFESSOR, "professor"),
    ],
)
def test_paineis_das_tres_contas_exibem_retorno_e_logout(
    client, escola, role, url_name
):
    user = Usuario.objects.create_user(
        email=f"{role.lower()}-acoes@example.com",
        password="Senha-forte-123!",
        nome="Pessoa das ações",
        role=role,
        escola=escola,
    )
    client.force_login(user)

    response = client.get(reverse(url_name))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'action="/sair/"' in content
    assert "Voltar" in content


def test_retorno_externo_e_ignorado_no_painel(client, escola):
    user = Usuario.objects.create_user(
        email="aluno-externo@example.com",
        password="Senha-forte-123!",
        nome="Aluno Teste",
        role=Usuario.Role.ALUNO,
        escola=escola,
    )
    client.force_login(user)

    response = client.get(
        reverse("aluno"),
        HTTP_REFERER="https://fora-do-sistema.example/conta/",
    )

    assert response.status_code == 200
    assert 'href="/aluno/"' in response.content.decode()


def test_troca_de_senha_tem_acoes_da_conta_sem_voltar_ao_inicio(client, usuario):
    client.force_login(usuario)

    response = client.get(reverse("trocar_senha"))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'action="/sair/"' in content
    assert "Voltar ao início" not in content


@pytest.mark.parametrize("role", [Usuario.Role.ALUNO, Usuario.Role.PROFESSOR])
def test_aluno_e_professor_podem_trocar_senha(client, escola, role):
    user = Usuario.objects.create_user(
        email=f"{role.lower()}-senha@example.com",
        password="Senha-forte-123!",
        nome="Pessoa que troca senha",
        role=role,
        escola=escola,
    )
    client.force_login(user)

    page = client.get(reverse("trocar_senha"))
    response = client.post(
        reverse("trocar_senha"),
        {
            "old_password": "Senha-forte-123!",
            "new_password1": "Outra-senha-forte-456!",
            "new_password2": "Outra-senha-forte-456!",
        },
    )

    assert page.status_code == 200
    assert b"Trocar senha" in page.content
    assert response.status_code == 302
    assert response.url == reverse(
        "aluno" if role == Usuario.Role.ALUNO else "professor"
    )
    assert client.session.get("_auth_user_id") == str(user.pk)


def test_login_do_aluno_mostra_acesso_a_troca_de_senha(client, escola):
    user = Usuario.objects.create_user(
        email="aluno-primeiro-acesso@example.com",
        password="Senha-forte-123!",
        nome="Aluno primeiro acesso",
        role=Usuario.Role.ALUNO,
        escola=escola,
    )

    login_response = client.post(
        reverse("entrar"),
        {"email": user.email, "senha": "Senha-forte-123!"},
    )
    page = client.get(login_response.url)

    assert login_response.url == reverse("aluno")
    assert page.status_code == 200
    assert "Trocar senha" in page.content.decode()


def test_avisos_globais_tem_dismiss_automatico():
    script = Path("static/js/messages.js").read_text()

    assert "site-messages" in script
    assert "3500" in script
    assert "is-hidden" in script


def test_troca_obrigatoria_de_senha_bloqueia_outras_rotas(client, escola):
    user = Usuario.objects.create_user(
        email="pendente-troca@example.com",
        password="Provisoria-123!",
        nome="Pendente Troca",
        role=Usuario.Role.ALUNO,
        escola=escola,
        precisa_trocar_senha=True,
        senha_provisoria="Provisoria-123!",
    )
    client.force_login(user)

    # Qualquer rota interna deve redirecionar para /conta/senha/
    for rota in [reverse("home"), reverse("aluno"), reverse("coordenacao")]:
        resp = client.get(rota)
        assert resp.status_code == 302
        assert resp.url == reverse("trocar_senha")

    # /conta/senha/ deve responder normalmente (200)
    page = client.get(reverse("trocar_senha"))
    assert page.status_code == 200

    # Ao atualizar a senha com sucesso, o bloqueio deve ser removido
    post_resp = client.post(
        reverse("trocar_senha"),
        {
            "old_password": "Provisoria-123!",
            "new_password1": "NovaSenhaSegura-456!",
            "new_password2": "NovaSenhaSegura-456!",
        },
    )
    assert post_resp.status_code == 302
    user.refresh_from_db()
    assert user.precisa_trocar_senha is False
    assert user.senha_provisoria == ""

    # Agora o acesso a outras rotas é liberado
    resp_liberado = client.get(reverse("aluno"))
    assert resp_liberado.status_code == 200


def test_coordenacao_so_gerencia_usuarios_da_propria_escola(client, escola, usuario):
    outra_escola = Escola.objects.create(nome="Outra Escola")
    outro_usuario = Usuario.objects.create_user(
        email="outro-aluno@example.com",
        password="Senha-forte-123!",
        nome="Outro Aluno",
        role=Usuario.Role.ALUNO,
        escola=outra_escola,
    )
    client.force_login(usuario)

    # Listagem de usuários só mostra membros da própria escola
    response = client.get(reverse("coordenacao_usuarios"))
    assert response.status_code == 200
    assert usuario.email in response.content.decode()
    assert outro_usuario.email not in response.content.decode()

    # Tentativa de alterar status ou resetar senha de usuário de outra escola retorna 404
    resp_status = client.post(
        reverse("coordenacao_usuario_status", args=[outro_usuario.pk])
    )
    assert resp_status.status_code == 404

    resp_reset = client.post(
        reverse("coordenacao_usuario_resetar_senha", args=[outro_usuario.pk])
    )
    assert resp_reset.status_code == 404


def test_usuario_desativado_nao_loga(client, escola):
    user = Usuario.objects.create_user(
        email="desativado@example.com",
        password="Senha-forte-123!",
        nome="Usuario Inativo",
        role=Usuario.Role.PROFESSOR,
        escola=escola,
        is_active=False,
    )
    response = client.post(
        reverse("entrar"),
        {"email": user.email, "senha": "Senha-forte-123!"},
    )
    assert response.status_code == 200
    assert "Não foi possível entrar com esses dados" in response.content.decode()
    assert client.session.get("_auth_user_id") is None


def test_desativar_aluno_nao_apaga_participacao(client, escola, usuario):
    from apps.avaliacoes.models import CicloAvaliacao, Participacao
    from apps.escolas.models import Disciplina, Turma, Vinculo

    turma = Turma.objects.create(escola=escola, nome="9º B", ano_letivo=2026)
    disciplina = Disciplina.objects.create(escola=escola, nome="História")
    professor = Usuario.objects.create_user(
        email="prof-hist@example.com",
        password="Senha-forte-123!",
        nome="Prof História",
        role=Usuario.Role.PROFESSOR,
        escola=escola,
    )
    aluno = Usuario.objects.create_user(
        email="aluno-hist@example.com",
        password="Senha-forte-123!",
        nome="Aluno Hist",
        role=Usuario.Role.ALUNO,
        escola=escola,
    )
    vinculo = Vinculo.objects.create(
        professor=professor, turma=turma, disciplina=disciplina
    )
    ciclo = CicloAvaliacao.objects.create(
        escola=escola, nome="Ciclo Teste", status=CicloAvaliacao.Status.ABERTO
    )
    participacao = Participacao.objects.create(aluno=aluno, ciclo=ciclo, vinculo=vinculo)

    client.force_login(usuario)
    # Desativa o aluno pela interface de gestão
    post_resp = client.post(reverse("coordenacao_usuario_status", args=[aluno.pk]))
    assert post_resp.status_code == 302
    aluno.refresh_from_db()
    assert aluno.is_active is False

    # Confirma que o registro de participação permanece intacto no banco
    assert Participacao.objects.filter(pk=participacao.pk).exists()
    assert Participacao.objects.get(pk=participacao.pk).aluno == aluno


def test_coordenacao_pode_convidar_outro_coordenador(client, escola, usuario):
    client.force_login(usuario)

    resp = client.post(
        reverse("coordenacao_usuarios"),
        {
            "convidar_coordenador": "1",
            "nome": "Novo Coordenador",
            "email": "novo.coord@example.com",
        },
    )
    assert resp.status_code == 302
    novo_coord = Usuario.objects.get(email="novo.coord@example.com")
    assert novo_coord.role == Usuario.Role.COORDENACAO
    assert novo_coord.escola == escola
    assert novo_coord.precisa_trocar_senha is True
    assert novo_coord.senha_provisoria != ""


def test_paginas_de_erro_customizadas_404_403_500():
    for template_name in ["404.html", "403.html", "500.html"]:
        template_file = Path("templates") / template_name
        assert template_file.exists()
        conteudo = template_file.read_text(encoding="utf-8")
        assert "favicon.svg" in Path("templates/base.html").read_text(encoding="utf-8")
        assert "{% extends \"base.html\" %}" in conteudo

