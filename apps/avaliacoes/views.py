from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.contas.decorators import papel_requerido
from apps.contas.models import Usuario
from apps.escolas.models import Matricula, Turma, Vinculo

from .forms import AvaliacaoForm, CicloAvaliacaoForm
from .models import (
    Avaliacao,
    CicloAvaliacao,
    ModeloQuestionario,
    Participacao,
    Pergunta,
    PerguntaModelo,
    RespostaEscala,
    RespostaEscolhaUnica,
    RespostaTexto,
)
from .services import (
    criar_ciclo_com_questionario,
    duplicar_modelo,
    publicar_ciclo,
    respostas_pendentes,
)

COORDENACAO = Usuario.Role.COORDENACAO
ALUNO = Usuario.Role.ALUNO


def _ciclo_aberto(user):
    return CicloAvaliacao.objects.para_usuario(user).filter(status=CicloAvaliacao.Status.ABERTO).first()


def _adesao_por_turma(ciclo, user):
    turmas = Turma.objects.para_usuario(user).prefetch_related("matriculas")
    return [{"turma": turma, "total": turma.matriculas.count(), "respondidos": Participacao.objects.filter(ciclo=ciclo, vinculo__turma=turma).values("aluno_id").distinct().count()} for turma in turmas]


def _contexto_ciclos(user):
    ciclos = list(CicloAvaliacao.objects.para_usuario(user).select_related("modelo_questionario"))
    pendentes = RespostaTexto.objects.filter(avaliacao__ciclo__escola_id=user.escola_id, status_moderacao=RespostaTexto.StatusModeracao.PENDENTE).exclude(texto="").order_by("?")
    for ciclo in ciclos:
        ciclo.adesao_por_turma = _adesao_por_turma(ciclo, user)
        ciclo.pendentes_moderacao = pendentes.filter(avaliacao__ciclo=ciclo)
    return ciclos, pendentes


@papel_requerido(COORDENACAO)
def ciclos(request):
    form = CicloAvaliacaoForm(request.user.escola, request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            criar_ciclo_com_questionario(request.user.escola, form.cleaned_data["nome"], form.cleaned_data["modelo_questionario"])
        except (IntegrityError, ValidationError) as exc:
            form.add_error(None, str(exc) if isinstance(exc, ValidationError) else "Já existe um ciclo não publicado para esta escola.")
        else:
            messages.success(request, "Ciclo aberto com o modelo escolhido.")
            return redirect("coordenacao_ciclos")
    ciclos_contexto, pendentes = _contexto_ciclos(request.user)
    return render(request, "coordenacao/ciclos.html", {"form": form, "ciclos": ciclos_contexto, "fila_moderacao": pendentes})


@papel_requerido(COORDENACAO)
def questionarios(request):
    modelos = ModeloQuestionario.objects.filter(escola=request.user.escola).prefetch_related("perguntas_modelo")
    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        descricao = request.POST.get("descricao", "").strip()
        if not nome:
            messages.error(request, "Dê um nome ao modelo antes de salvar.")
        else:
            try:
                modelo = ModeloQuestionario.objects.create(escola=request.user.escola, nome=nome, descricao=descricao)
                messages.success(request, "Modelo criado. Adicione pelo menos duas escalas e cinco perguntas.")
                return redirect("coordenacao_questionario_editar", modelo_id=modelo.pk)
            except IntegrityError:
                messages.error(request, "Já existe um modelo com esse nome.")
    return render(request, "coordenacao/questionarios.html", {"modelos": modelos})


def _mensagens_validacao(exc):
    return " ".join(exc.messages)


def _limite_para_pergunta(modelo, tipo, atual=None):
    perguntas = modelo.perguntas_modelo.all()
    if atual is not None:
        perguntas = perguntas.exclude(pk=atual.pk)
    if atual is None and perguntas.count() >= 15:
        raise ValidationError("O modelo já tem 15 perguntas, que é o limite permitido.")
    if tipo == PerguntaModelo.Tipo.TEXTO and perguntas.filter(tipo=PerguntaModelo.Tipo.TEXTO).count() >= 3:
        raise ValidationError("O modelo já tem 3 perguntas de texto, que é o limite permitido.")


@transaction.atomic
def _mover_pergunta(modelo, pergunta_id, direcao):
    perguntas = list(modelo.perguntas_modelo.select_for_update().order_by("ordem", "pk"))
    indice = next((i for i, pergunta in enumerate(perguntas) if pergunta.pk == pergunta_id), None)
    if indice is None:
        raise Http404
    destino = indice - 1 if direcao == "subir" else indice + 1
    if destino < 0 or destino >= len(perguntas):
        return
    atual = perguntas[indice]
    outra = perguntas[destino]
    ordem_atual, ordem_outra = atual.ordem, outra.ordem
    type(atual).objects.filter(pk=atual.pk).update(ordem=0)
    type(atual).objects.filter(pk=outra.pk).update(ordem=ordem_atual)
    type(atual).objects.filter(pk=atual.pk).update(ordem=ordem_outra)


@transaction.atomic
def _normalizar_ordens(modelo):
    perguntas = list(modelo.perguntas_modelo.order_by("ordem", "pk"))
    for indice, pergunta in enumerate(perguntas, 1):
        type(pergunta).objects.filter(pk=pergunta.pk).update(ordem=100 + indice)
    for indice, pergunta in enumerate(perguntas, 1):
        type(pergunta).objects.filter(pk=pergunta.pk).update(ordem=indice)


@papel_requerido(COORDENACAO)
def questionario_editar(request, modelo_id):
    modelo = get_object_or_404(ModeloQuestionario.objects.filter(escola=request.user.escola), pk=modelo_id)
    if modelo.padrao and request.method == "POST":
        messages.error(request, "O modelo padrão não pode ser editado. Duplique-o para personalizar.")
        return redirect("coordenacao_questionarios")
    if request.method == "POST":
        if "adicionar" in request.POST:
            try:
                tipo = request.POST.get("tipo", PerguntaModelo.Tipo.ESCALA_1_5)
                _limite_para_pergunta(modelo, tipo)
                opcoes = [x.strip() for x in request.POST.get("opcoes", "").splitlines() if x.strip()]
                if tipo != PerguntaModelo.Tipo.ESCOLHA_UNICA:
                    opcoes = []
                pergunta = PerguntaModelo(
                    modelo=modelo,
                    texto=request.POST.get("texto", "").strip(),
                    tipo=tipo,
                    dimensao=request.POST.get("dimensao", "").strip(),
                    ordem=modelo.perguntas_modelo.count() + 1,
                    obrigatoria="obrigatoria" in request.POST,
                    opcoes=opcoes,
                )
                pergunta.save()
                messages.success(request, "Pergunta adicionada.")
            except ValidationError as exc:
                messages.error(request, _mensagens_validacao(exc))
        elif "editar" in request.POST:
            pergunta = get_object_or_404(modelo.perguntas_modelo.all(), pk=request.POST.get("pergunta_id"))
            try:
                tipo = request.POST.get("tipo", PerguntaModelo.Tipo.ESCALA_1_5)
                _limite_para_pergunta(modelo, tipo, atual=pergunta)
                opcoes = [x.strip() for x in request.POST.get("opcoes", "").splitlines() if x.strip()]
                if tipo != PerguntaModelo.Tipo.ESCOLHA_UNICA:
                    opcoes = []
                pergunta.texto = request.POST.get("texto", "").strip()
                pergunta.tipo = tipo
                pergunta.dimensao = request.POST.get("dimensao", "").strip()
                pergunta.obrigatoria = "obrigatoria" in request.POST
                pergunta.opcoes = opcoes
                pergunta.save()
                messages.success(request, "Pergunta atualizada.")
            except ValidationError as exc:
                messages.error(request, _mensagens_validacao(exc))
        elif "remover" in request.POST:
            pergunta = get_object_or_404(modelo.perguntas_modelo.all(), pk=request.POST.get("pergunta_id"))
            pergunta.delete()
            _normalizar_ordens(modelo)
            messages.success(request, "Pergunta removida.")
        elif "arquivar" in request.POST:
            modelo.ativo = False
            modelo.save(update_fields=("ativo",))
            messages.success(request, "Modelo arquivado.")
            return redirect("coordenacao_questionarios")
        elif "excluir_modelo" in request.POST:
            try:
                modelo.delete()
            except ProtectedError:
                messages.error(request, "Este modelo já foi usado em um ciclo e não pode ser excluído. Arquive-o para não aparecer em novos ciclos.")
            except ValidationError as exc:
                messages.error(request, _mensagens_validacao(exc))
            else:
                messages.success(request, "Modelo excluído.")
            return redirect("coordenacao_questionarios")
        elif "mover" in request.POST:
            _mover_pergunta(modelo, int(request.POST["pergunta_id"]), request.POST["mover"])
    return render(request, "coordenacao/questionario_editar.html", {"modelo": modelo, "perguntas": modelo.perguntas_modelo.all()})


@papel_requerido(COORDENACAO)
@require_POST
def questionario_duplicar(request, modelo_id):
    modelo = get_object_or_404(ModeloQuestionario.objects.filter(escola=request.user.escola), pk=modelo_id)
    try:
        novo = duplicar_modelo(modelo, request.user.escola, request.POST.get("nome") or None)
    except (ValidationError, IntegrityError) as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Modelo duplicado para edição.")
        return redirect("coordenacao_questionario_editar", modelo_id=novo.pk)
    return redirect("coordenacao_questionarios")


@papel_requerido(COORDENACAO)
def questionario_preview(request, modelo_id):
    modelo = get_object_or_404(ModeloQuestionario.objects.filter(escola=request.user.escola), pk=modelo_id)
    return render(request, "aluno/questionario_preview.html", {"modelo": modelo, "perguntas": modelo.perguntas_modelo.all()})


@papel_requerido(COORDENACAO)
@require_POST
def questionario_excluir(request, modelo_id):
    modelo = get_object_or_404(ModeloQuestionario.objects.filter(escola=request.user.escola), pk=modelo_id)
    if modelo.padrao:
        messages.error(request, "O modelo padrão da Trilha não pode ser excluído.")
    else:
        try:
            modelo.delete()
        except ProtectedError:
            messages.error(request, "Este modelo já foi usado em um ciclo e não pode ser excluído. Arquive-o para não aparecer em novos ciclos.")
        else:
            messages.success(request, "Modelo excluído.")
    return redirect("coordenacao_questionarios")


@papel_requerido(COORDENACAO)
def encerrar_ciclo(request, ciclo_id):
    if request.method != "POST":
        return redirect("coordenacao_ciclos")
    ciclo = get_object_or_404(CicloAvaliacao.objects.para_usuario(request.user), pk=ciclo_id)
    if ciclo.status == CicloAvaliacao.Status.ABERTO:
        ciclo.status = CicloAvaliacao.Status.FECHADO
        ciclo.save(update_fields=("status",))
        messages.success(request, "Ciclo encerrado. A escuta está pronta para moderação.")
    return redirect("coordenacao_ciclos")


@papel_requerido(COORDENACAO)
def publicar(request, ciclo_id):
    if request.method != "POST":
        return redirect("coordenacao_ciclos")
    ciclo = get_object_or_404(CicloAvaliacao.objects.para_usuario(request.user), pk=ciclo_id)
    if publicar_ciclo(ciclo):
        messages.success(request, "Resultados publicados com cuidado e transparência.")
    elif respostas_pendentes(ciclo).exists():
        messages.error(request, "Ainda há comentários aguardando moderação antes da publicação.")
    else:
        messages.info(request, "O ciclo precisa estar fechado para ser publicado.")
    return redirect("coordenacao_ciclos")


@papel_requerido(COORDENACAO)
def moderar_resposta(request, resposta_id):
    if request.method != "POST":
        return redirect("coordenacao_ciclos")
    resposta = get_object_or_404(RespostaTexto.objects.filter(avaliacao__ciclo__escola_id=request.user.escola_id, status_moderacao=RespostaTexto.StatusModeracao.PENDENTE), pk=resposta_id)
    novo_status = {"aprovar": RespostaTexto.StatusModeracao.APROVADO, "rejeitar": RespostaTexto.StatusModeracao.REJEITADO}.get(request.POST.get("acao"))
    if novo_status:
        resposta.status_moderacao = novo_status
        resposta.save(update_fields=("status_moderacao",))
    return redirect("coordenacao_ciclos")


def _pendencias(user):
    ciclo = _ciclo_aberto(user)
    if ciclo is None:
        return None, []
    turma_ids = Matricula.objects.para_usuario(user).filter(aluno_id=user.pk).values_list("turma_id", flat=True)
    vinculos = list(Vinculo.objects.para_usuario(user).filter(turma_id__in=turma_ids).select_related("professor", "turma", "disciplina"))
    concluidos = set(Participacao.objects.para_usuario(user).filter(aluno_id=user.pk, ciclo_id=ciclo.pk).values_list("vinculo_id", flat=True))
    return ciclo, [v for v in vinculos if v.pk not in concluidos]


@papel_requerido(ALUNO)
def pendencias(request):
    ciclo, vinculos = _pendencias(request.user)
    return render(request, "aluno/pendencias.html", {"ciclo": ciclo, "vinculos": vinculos})


@papel_requerido(ALUNO)
def avaliar(request, vinculo_id):
    vinculo = get_object_or_404(Vinculo.objects.para_usuario(request.user).select_related("professor", "turma", "disciplina"), pk=vinculo_id)
    ciclo = _ciclo_aberto(request.user)
    if ciclo is None or not Matricula.objects.para_usuario(request.user).filter(aluno_id=request.user.pk, turma_id=vinculo.turma_id).exists():
        raise Http404
    ja_participou = Participacao.objects.para_usuario(request.user).filter(aluno_id=request.user.pk, ciclo_id=ciclo.pk, vinculo_id=vinculo.pk).exists()
    if ja_participou and request.method != "POST":
        messages.info(request, "Essa aula já foi registrada. Obrigado por participar da escuta.")
        return redirect("aluno")
    perguntas = list(Pergunta.objects.filter(ciclo_id=ciclo.pk).order_by("ordem"))
    form = AvaliacaoForm(perguntas, request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if Participacao.objects.filter(aluno_id=request.user.pk, ciclo_id=ciclo.pk, vinculo_id=vinculo.pk).exists():
                    raise IntegrityError("participacao_duplicada")
                Participacao.objects.create(aluno=request.user, ciclo=ciclo, vinculo=vinculo)
                avaliacao = Avaliacao.objects.create(ciclo=ciclo, vinculo=vinculo.pk)
                for pergunta, resposta in form.respostas():
                    if pergunta.tipo == Pergunta.Tipo.ESCALA_1_5:
                        RespostaEscala.objects.create(avaliacao=avaliacao, pergunta=pergunta, valor=resposta)
                    elif pergunta.tipo == Pergunta.Tipo.ESCOLHA_UNICA:
                        if resposta not in pergunta.opcoes:
                            raise ValidationError("Opção inválida para este questionário.")
                        RespostaEscolhaUnica.objects.create(avaliacao=avaliacao, pergunta=pergunta, opcao=resposta)
                    else:
                        RespostaTexto.objects.create(avaliacao=avaliacao, pergunta=pergunta, texto=(resposta or "").strip())
        except (IntegrityError, ValidationError):
            form.add_error(None, "Essa aula já foi registrada ou a resposta não é válida. Sua contribuição não foi duplicada.")
        else:
            return redirect("aluno_obrigado")
    return render(request, "aluno/avaliar.html", {"form": form, "ciclo": ciclo, "vinculo": vinculo})


@papel_requerido(ALUNO)
def obrigado(request):
    return render(request, "aluno/obrigado.html")
