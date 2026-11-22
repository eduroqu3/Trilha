import secrets

from django.db import transaction

from apps.contas.models import Usuario

from .forms import validar_linha_csv
from .models import Matricula, Turma


def gerar_senha_temporaria():
    return secrets.token_urlsafe(9)


def criar_professor(escola, nome, email):
    senha = gerar_senha_temporaria()
    professor = Usuario.objects.create_user(
        email=email,
        password=senha,
        nome=nome,
        role=Usuario.Role.PROFESSOR,
        escola=escola,
        precisa_trocar_senha=True,
        senha_provisoria=senha,
    )
    return professor, senha


def criar_aluno(escola, nome, email, turma):
    senha = gerar_senha_temporaria()
    with transaction.atomic():
        aluno = Usuario.objects.create_user(
            email=email,
            password=senha,
            nome=nome,
            role=Usuario.Role.ALUNO,
            escola=escola,
            precisa_trocar_senha=True,
            senha_provisoria=senha,
        )
        Matricula.objects.create(aluno=aluno, turma=turma)
    return aluno, senha


def importar_professores(user, linhas):
    resultado = {"criados": [], "erros": []}
    emails_do_arquivo = set()
    for numero, linha in enumerate(linhas, start=2):
        valores, erros = validar_linha_csv(linha, numero, ("nome", "email"))
        if valores["email"] in emails_do_arquivo:
            erros.append(f"Linha {numero}: e-mail repetido no arquivo.")
        if Usuario.objects.filter(email__iexact=valores["email"]).exists():
            erros.append(f"Linha {numero}: e-mail já cadastrado.")
        if erros:
            resultado["erros"].extend(erros)
            continue
        emails_do_arquivo.add(valores["email"])
        with transaction.atomic():
            professor, senha = criar_professor(
                user.escola, valores["nome"], valores["email"]
            )
        resultado["criados"].append(
            {"nome": professor.nome, "email": professor.email, "senha": senha}
        )
    return resultado


def importar_alunos(user, linhas):
    resultado = {"criados": [], "erros": []}
    emails_do_arquivo = set()
    turmas = list(Turma.objects.para_usuario(user))
    for numero, linha in enumerate(linhas, start=2):
        valores, erros = validar_linha_csv(linha, numero, ("nome", "email", "turma"))
        if valores["email"] in emails_do_arquivo:
            erros.append(f"Linha {numero}: e-mail repetido no arquivo.")
        if Usuario.objects.filter(email__iexact=valores["email"]).exists():
            erros.append(f"Linha {numero}: e-mail já cadastrado.")
        turmas_encontradas = [
            turma
            for turma in turmas
            if turma.nome.casefold() == valores["turma"].casefold()
        ]
        if not valores["turma"]:
            erros.append(f"Linha {numero}: turma obrigatória.")
        elif len(turmas_encontradas) == 0:
            erros.append(f"Linha {numero}: turma não encontrada nesta escola.")
        elif len(turmas_encontradas) > 1:
            erros.append(f"Linha {numero}: turma ambígua; informe uma turma única.")
        if erros:
            resultado["erros"].extend(erros)
            continue
        emails_do_arquivo.add(valores["email"])
        aluno, senha = criar_aluno(
            user.escola,
            valores["nome"],
            valores["email"],
            turmas_encontradas[0],
        )
        resultado["criados"].append(
            {
                "nome": aluno.nome,
                "email": aluno.email,
                "senha": senha,
                "turma": turmas_encontradas[0].nome,
            }
        )
    return resultado
