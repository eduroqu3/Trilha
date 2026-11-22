import csv
import io

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.escolas.forms import (
    AlunoForm,
    CSVImportForm,
    ProfessorForm,
)
from apps.escolas.services import (
    criar_aluno,
    criar_professor,
    gerar_senha_temporaria,
)

from .decorators import papel_requerido
from .forms import (
    CadastroEscolaForm,
    ContaPasswordChangeForm,
    ConvidarCoordenadorForm,
    LoginForm,
)
from .models import Usuario

CADASTRO_LIMITE = 5
CADASTRO_JANELA = 15 * 60


def _ip(request):
    return request.META.get("REMOTE_ADDR", "unknown")


def cadastro_escola(request):
    chave = f"cadastro-escola:{_ip(request)}"
    bloqueado = cache.get(chave, 0) >= CADASTRO_LIMITE
    form = CadastroEscolaForm(request.POST or None)
    if request.method == "POST":
        if bloqueado:
            form.add_error(None, "Aguarde alguns minutos antes de tentar novamente.")
        elif form.is_valid() and not form.cleaned_data.get("website"):
            try:
                with transaction.atomic():
                    usuario = form.save()
            except IntegrityError:
                form.add_error(
                    None, "Não foi possível concluir o cadastro agora. Tente novamente."
                )
            else:
                cache.delete(chave)
                login(request, usuario, backend="apps.contas.backends.EmailBackend")
                return redirect("coordenacao")
        if not bloqueado:
            cache.set(chave, cache.get(chave, 0) + 1, CADASTRO_JANELA)
    return render(
        request, "contas/cadastro_escola.html", {"form": form, "bloqueado": bloqueado}
    )


def _next_url(request):
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return ""


def entrar(request):
    next_url = _next_url(request)
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["senha"],
        )
        if user is not None:
            login(request, user)
            return redirect(next_url or user_dashboard(user))
        form.add_error(
            None,
            "Não foi possível entrar com esses dados. Confira e-mail e senha e tente novamente.",
        )
    return render(request, "contas/entrar.html", {"form": form, "next": next_url})


def user_dashboard(user):
    return {
        Usuario.Role.ALUNO: "aluno",
        Usuario.Role.PROFESSOR: "professor",
        Usuario.Role.COORDENACAO: "coordenacao",
    }[user.role]


def sair(request):
    if request.method != "POST":
        return redirect("home")
    logout(request)
    messages.success(request, "Você saiu com segurança.")
    return redirect("entrar")


@login_required
def trocar_senha(request):
    form = ContaPasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        if user.precisa_trocar_senha or user.senha_provisoria:
            user.precisa_trocar_senha = False
            user.senha_provisoria = ""
            user.save(update_fields=("precisa_trocar_senha", "senha_provisoria"))
        messages.success(request, "Sua senha foi atualizada.")
        return redirect(user_dashboard(request.user))
    return render(request, "contas/trocar_senha.html", {"form": form})


def _painel(request, papel, titulo):
    return render(request, f"{papel}/dashboard.html", {"titulo": titulo, "papel": papel})


@papel_requerido(Usuario.Role.ALUNO)
def aluno(request):
    return _painel(request, "aluno", "Espaço do estudante")


@papel_requerido(Usuario.Role.PROFESSOR)
def professor(request):
    from apps.avaliacoes.models import CicloAvaliacao, RespostaTexto, ResumoVinculo
    from apps.escolas.models import Vinculo

    vinculo_ids = Vinculo.objects.para_usuario(request.user).filter(
        professor_id=request.user.pk
    ).values_list("pk", flat=True)
    resumos = ResumoVinculo.objects.para_usuario(request.user).select_related(
        "ciclo", "vinculo__turma", "vinculo__disciplina"
    ).filter(
        ciclo__status=CicloAvaliacao.Status.PUBLICADO,
        vinculo__in=vinculo_ids,
    )
    resultados = []
    for resumo in resumos:
        vinculo = resumo.vinculo
        comentarios = list(
            RespostaTexto.objects.filter(
                avaliacao__ciclo=resumo.ciclo,
                avaliacao__vinculo=resumo.vinculo_id,
                status_moderacao=RespostaTexto.StatusModeracao.APROVADO,
            )
            .exclude(texto="")
            .order_by("?")
            .values_list("texto", flat=True)
        )
        medias = [
            {
                "dimensao": dimensao,
                "media": media,
                "largura": round(float(media) * 20),
            }
            for dimensao, media in resumo.medias_por_dimensao.items()
        ]
        resultados.append(
            {
                "ciclo": resumo.ciclo,
                "vinculo": vinculo,
                "medias": medias,
                "comentarios": comentarios,
            }
        )
    return render(
        request,
        "professor/dashboard.html",
        {"titulo": "Espaço do professor", "papel": "professor", "resultados": resultados},
    )


@papel_requerido(Usuario.Role.COORDENACAO)
def coordenacao(request):
    return redirect("coordenacao_usuarios")


@papel_requerido(Usuario.Role.COORDENACAO)
def coordenacao_usuarios(request):
    papel_filtro = request.GET.get("papel", "").upper()
    usuarios_qs = Usuario.objects.da_escola(request.user).order_by("nome")
    if papel_filtro in Usuario.Role.values:
        usuarios_qs = usuarios_qs.filter(role=papel_filtro)

    form_coordenador = ConvidarCoordenadorForm(request.user.escola, request.POST or None)
    form_professor = ProfessorForm(request.POST or None)
    form_aluno = AlunoForm(request.user, request.POST or None)
    csv_form_professor = CSVImportForm(("nome", "email"), prefix="csv_prof")
    csv_form_aluno = CSVImportForm(("nome", "email", "turma"), prefix="csv_aluno")
    csv_form_coordenador = CSVImportForm(("nome", "email"), prefix="csv_coord")

    if request.method == "POST":
        if "importar_coordenadores" in request.POST:
            csv_form_coordenador = CSVImportForm(
                ("nome", "email"), request.POST, request.FILES, prefix="csv_coord"
            )
            if csv_form_coordenador.is_valid():
                arquivo = csv_form_coordenador.cleaned_data["arquivo"]
                conteudo = arquivo.read().decode("utf-8-sig", errors="replace")
                reader = csv.DictReader(io.StringIO(conteudo))
                criados = 0
                erros = []
                for i, linha in enumerate(reader, start=2):
                    nome = (linha.get("nome") or "").strip()
                    email = (linha.get("email") or "").strip().lower()
                    if not nome or not email:
                        erros.append(f"Linha {i}: nome ou e-mail vazio.")
                        continue
                    try:
                        with transaction.atomic():
                            senha = gerar_senha_temporaria()
                            Usuario.objects.create_user(
                                email=email,
                                password=senha,
                                nome=nome,
                                role=Usuario.Role.COORDENACAO,
                                escola=request.user.escola,
                                precisa_trocar_senha=True,
                                senha_provisoria=senha,
                            )
                        criados += 1
                    except IntegrityError:
                        erros.append(f"Linha {i}: e-mail {email} já cadastrado.")
                if criados:
                    messages.success(request, f"{criados} coordenador(es) importado(s) com sucesso.")
                for erro in erros:
                    messages.warning(request, erro)
                return redirect("coordenacao_usuarios")

        if "convidar_coordenador" in request.POST and form_coordenador.is_valid():
            senha = gerar_senha_temporaria()
            novo_coord = Usuario.objects.create_user(
                email=form_coordenador.cleaned_data["email"],
                password=senha,
                nome=form_coordenador.cleaned_data["nome"].strip(),
                role=Usuario.Role.COORDENACAO,
                escola=request.user.escola,
                precisa_trocar_senha=True,
                senha_provisoria=senha,
            )
            messages.success(
                request,
                f"Conta da coordenação criada para {novo_coord.nome}. Senha provisória: {senha}",
            )
            return redirect("coordenacao_usuarios")

        if "cadastrar_professor" in request.POST and form_professor.is_valid():
            try:
                with transaction.atomic():
                    prof, senha = criar_professor(
                        request.user.escola,
                        form_professor.cleaned_data["nome"],
                        form_professor.cleaned_data["email"],
                    )
            except IntegrityError:
                form_professor.add_error(None, "Não foi possível criar este professor agora.")
            else:
                messages.success(
                    request,
                    f"Professor(a) {prof.nome} cadastrado(a). Senha provisória: {senha}",
                )
                return redirect("coordenacao_usuarios")

        if "cadastrar_aluno" in request.POST and form_aluno.is_valid():
            try:
                with transaction.atomic():
                    aluno_obj, senha = criar_aluno(
                        request.user.escola,
                        form_aluno.cleaned_data["nome"],
                        form_aluno.cleaned_data["email"],
                        form_aluno.cleaned_data["turma"],
                    )
            except IntegrityError:
                form_aluno.add_error(None, "Não foi possível criar este aluno agora.")
            else:
                messages.success(
                    request,
                    f"Estudante {aluno_obj.nome} cadastrado(a) na turma {form_aluno.cleaned_data['turma'].nome}. Senha provisória: {senha}",
                )
                return redirect("coordenacao_usuarios")

    return render(
        request,
        "coordenacao/usuarios.html",
        {
            "usuarios": usuarios_qs,
            "papel_filtro": papel_filtro,
            "papeis": Usuario.Role.choices,
            "form_coordenador": form_coordenador,
            "form_professor": form_professor,
            "form_aluno": form_aluno,
            "csv_form_professor": csv_form_professor,
            "csv_form_aluno": csv_form_aluno,
            "csv_form_coordenador": csv_form_coordenador,
        },
    )


@papel_requerido(Usuario.Role.COORDENACAO)
@require_POST
def alternar_status_usuario(request, pk):
    usuario_alvo = get_object_or_404(Usuario.objects.da_escola(request.user), pk=pk)
    if usuario_alvo.pk == request.user.pk:
        messages.error(request, "Você não pode desativar seu próprio acesso.")
        return redirect("coordenacao_usuarios")

    usuario_alvo.is_active = not usuario_alvo.is_active
    usuario_alvo.save(update_fields=("is_active",))
    status_str = "reativado" if usuario_alvo.is_active else "desativado"
    messages.success(request, f"Acesso de {usuario_alvo.nome} foi {status_str} com sucesso.")
    return redirect("coordenacao_usuarios")


@papel_requerido(Usuario.Role.COORDENACAO)
@require_POST
def resetar_senha_usuario(request, pk):
    usuario_alvo = get_object_or_404(Usuario.objects.da_escola(request.user), pk=pk)
    nova_senha = gerar_senha_temporaria()
    usuario_alvo.set_password(nova_senha)
    usuario_alvo.precisa_trocar_senha = True
    usuario_alvo.senha_provisoria = nova_senha
    usuario_alvo.save(update_fields=("password", "precisa_trocar_senha", "senha_provisoria"))
    messages.success(
        request,
        f"Nova senha provisória gerada para {usuario_alvo.nome}: {nova_senha}",
    )
    return redirect("coordenacao_usuarios")

