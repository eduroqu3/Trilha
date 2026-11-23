from collections import Counter

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg

from .models import (
    Avaliacao,
    CicloAvaliacao,
    ModeloQuestionario,
    Pergunta,
    PerguntaModelo,
    RespostaEscala,
    RespostaEscolhaUnica,
    RespostaTexto,
    ResumoVinculo,
    validar_regras_modelo,
)

PERGUNTAS_PADRAO = (
    ("A clareza das explicações ajuda você a acompanhar a aula?", "clareza", PerguntaModelo.Tipo.ESCALA_1_5, []),
    ("Você sente que sua participação é escutada durante a aula?", "escuta", PerguntaModelo.Tipo.ESCALA_1_5, []),
    ("O ritmo da aula favorece sua aprendizagem?", "ritmo", PerguntaModelo.Tipo.ESCALA_1_5, []),
    ("A organização da aula ajuda você a aprender?", "organização", PerguntaModelo.Tipo.ESCALA_1_5, []),
    ("As propostas da aula incentivam sua aprendizagem?", "incentivo", PerguntaModelo.Tipo.ESCALA_1_5, []),
    ("Você se sente acolhido ou acolhida durante a aula?", "acolhimento", PerguntaModelo.Tipo.ESCALA_1_5, []),
    ("O que ajuda você a aprender nessa aula?", "", PerguntaModelo.Tipo.TEXTO, []),
    ("O que poderia mudar para a aprendizagem fluir melhor?", "", PerguntaModelo.Tipo.TEXTO, []),
)


def _criar_perguntas_padrao(modelo):
    PerguntaModelo.objects.bulk_create([
        PerguntaModelo(modelo=modelo, texto=texto, dimensao=dimensao, tipo=tipo, ordem=i, obrigatoria=tipo != PerguntaModelo.Tipo.TEXTO, opcoes=opcoes)
        for i, (texto, dimensao, tipo, opcoes) in enumerate(PERGUNTAS_PADRAO, 1)
    ])
    return modelo


@transaction.atomic
def criar_modelo_padrao(escola):
    modelo, criado = ModeloQuestionario.objects.get_or_create(
        escola=escola, padrao=True, defaults={"nome": "Questionário padrão da Trilha", "descricao": "Modelo base de escuta pedagógica.", "ativo": True}
    )
    if criado:
        _criar_perguntas_padrao(modelo)
    return modelo


@transaction.atomic
def duplicar_modelo(modelo, escola, nome=None):
    if modelo.escola_id != escola.pk:
        raise ValidationError("O modelo não pertence a esta escola.")
    novo = ModeloQuestionario.objects.create(escola=escola, nome=nome or f"Cópia de {modelo.nome}", descricao=modelo.descricao, ativo=True, padrao=False)
    PerguntaModelo.objects.bulk_create([
        PerguntaModelo(modelo=novo, texto=p.texto, tipo=p.tipo, dimensao=p.dimensao, ordem=p.ordem, obrigatoria=p.obrigatoria, opcoes=p.opcoes)
        for p in modelo.perguntas_modelo.all().order_by("ordem")
    ])
    return novo


@transaction.atomic
def criar_ciclo_com_questionario(escola, nome, modelo=None):
    modelo = modelo or ModeloQuestionario.objects.filter(escola=escola, ativo=True).order_by("padrao", "nome").first()
    if modelo is None:
        modelo = criar_modelo_padrao(escola)
    if modelo is None or modelo.escola_id != escola.pk:
        raise ValidationError("Escolha um modelo ativo desta escola.")
    perguntas_modelo = list(modelo.perguntas_modelo.all().order_by("ordem"))
    if not 5 <= len(perguntas_modelo) <= 15:
        raise ValidationError("O modelo precisa ter entre 5 e 15 perguntas.")
    ciclo = CicloAvaliacao.objects.create(escola=escola, nome=nome, status=CicloAvaliacao.Status.ABERTO, modelo_questionario=modelo)
    Pergunta.objects.bulk_create([
        Pergunta(ciclo=ciclo, texto=p.texto, dimensao=p.dimensao, tipo=p.tipo, ordem=p.ordem, obrigatoria=p.obrigatoria, opcoes=p.opcoes)
        for p in perguntas_modelo
    ])
    return ciclo


def validar_modelo_completo(modelo):
    validar_regras_modelo(modelo)
    for pergunta in modelo.perguntas_modelo.all():
        pergunta.full_clean()


@transaction.atomic
def gerar_resumos(ciclo):
    ResumoVinculo.objects.filter(ciclo=ciclo).delete()
    limiar = ciclo.escola.limiar_minimo
    vinculo_ids = Avaliacao.objects.filter(ciclo=ciclo).values_list("vinculo", flat=True).distinct()
    resumos = []
    for vinculo_id in vinculo_ids:
        avaliacoes = Avaliacao.objects.filter(ciclo=ciclo, vinculo=vinculo_id)
        n_avaliacoes = avaliacoes.count()
        if n_avaliacoes < limiar:
            continue
        medias = {}
        for dimensao in Pergunta.objects.filter(ciclo=ciclo, tipo=Pergunta.Tipo.ESCALA_1_5).exclude(dimensao="").values_list("dimensao", flat=True).distinct():
            media = RespostaEscala.objects.filter(avaliacao__in=avaliacoes, pergunta__dimensao=dimensao).aggregate(media=Avg("valor"))["media"]
            if media is not None:
                medias[dimensao] = round(float(media), 2)
        distribuicoes = {}
        perguntas = Pergunta.objects.filter(ciclo=ciclo, tipo=Pergunta.Tipo.ESCOLHA_UNICA).order_by("ordem")
        for pergunta in perguntas:
            contagem = Counter(RespostaEscolhaUnica.objects.filter(avaliacao__in=avaliacoes, pergunta=pergunta).values_list("opcao", flat=True))
            distribuicoes[str(pergunta.pk)] = {opcao: contagem.get(opcao, 0) for opcao in pergunta.opcoes}
        resumos.append(ResumoVinculo(ciclo=ciclo, vinculo_id=vinculo_id, n_avaliacoes=n_avaliacoes, medias_por_dimensao=medias, distribuicoes_por_pergunta=distribuicoes))
    return ResumoVinculo.objects.bulk_create(resumos)


def respostas_pendentes(ciclo):
    return RespostaTexto.objects.filter(avaliacao__ciclo=ciclo, status_moderacao=RespostaTexto.StatusModeracao.PENDENTE).exclude(texto="")


@transaction.atomic
def publicar_ciclo(ciclo):
    if ciclo.status != CicloAvaliacao.Status.FECHADO or respostas_pendentes(ciclo).exists():
        return False
    gerar_resumos(ciclo)
    ciclo.status = CicloAvaliacao.Status.PUBLICADO
    ciclo.save(update_fields=("status",))
    return True
