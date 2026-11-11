from django.db import transaction
from django.db.models import Avg

from .models import (
    Avaliacao,
    CicloAvaliacao,
    Pergunta,
    RespostaEscala,
    RespostaTexto,
    ResumoVinculo,
)

PERGUNTAS_PADRAO = (
    (
        "A clareza das explicações ajuda você a acompanhar a aula?",
        "clareza",
        Pergunta.Tipo.ESCALA_1_5,
    ),
    (
        "Você sente que sua participação é escutada durante a aula?",
        "escuta",
        Pergunta.Tipo.ESCALA_1_5,
    ),
    ("O ritmo da aula favorece sua aprendizagem?", "ritmo", Pergunta.Tipo.ESCALA_1_5),
    (
        "A organização da aula ajuda você a aprender?",
        "organização",
        Pergunta.Tipo.ESCALA_1_5,
    ),
    (
        "As propostas da aula incentivam sua aprendizagem?",
        "incentivo",
        Pergunta.Tipo.ESCALA_1_5,
    ),
    (
        "Você se sente acolhido ou acolhida durante a aula?",
        "acolhimento",
        Pergunta.Tipo.ESCALA_1_5,
    ),
    ("O que ajuda você a aprender nessa aula?", "", Pergunta.Tipo.TEXTO),
    ("O que poderia mudar para a aprendizagem fluir melhor?", "", Pergunta.Tipo.TEXTO),
)


@transaction.atomic
def criar_ciclo_com_questionario(escola, nome):
    ciclo = CicloAvaliacao.objects.create(
        escola=escola,
        nome=nome,
        status=CicloAvaliacao.Status.ABERTO,
    )
    Pergunta.objects.bulk_create(
        [
            Pergunta(
                ciclo=ciclo,
                texto=texto,
                dimensao=dimensao,
                tipo=tipo,
                ordem=ordem,
            )
            for ordem, (texto, dimensao, tipo) in enumerate(PERGUNTAS_PADRAO, 1)
        ]
    )
    return ciclo


def respostas_pendentes(ciclo):
    return RespostaTexto.objects.filter(
        avaliacao__ciclo=ciclo,
        status_moderacao=RespostaTexto.StatusModeracao.PENDENTE,
    ).exclude(texto="")


@transaction.atomic
def gerar_resumos(ciclo):
    ResumoVinculo.objects.filter(ciclo=ciclo).delete()
    limiar = ciclo.escola.limiar_minimo
    vinculo_ids = (
        Avaliacao.objects.filter(ciclo=ciclo)
        .values_list("vinculo", flat=True)
        .distinct()
    )
    resumos = []
    for vinculo_id in vinculo_ids:
        avaliacoes = Avaliacao.objects.filter(ciclo=ciclo, vinculo=vinculo_id)
        n_avaliacoes = avaliacoes.count()
        if n_avaliacoes < limiar:
            continue
        medias = {}
        for dimensao in (
            Pergunta.objects.filter(
                ciclo=ciclo, tipo=Pergunta.Tipo.ESCALA_1_5
            )
            .values_list("dimensao", flat=True)
            .distinct()
        ):
            media = RespostaEscala.objects.filter(
                avaliacao__in=avaliacoes,
                pergunta__dimensao=dimensao,
            ).aggregate(media=Avg("valor"))["media"]
            if media is not None:
                medias[dimensao] = round(float(media), 2)
        resumos.append(
            ResumoVinculo(
                ciclo=ciclo,
                vinculo_id=vinculo_id,
                n_avaliacoes=n_avaliacoes,
                medias_por_dimensao=medias,
            )
        )
    return ResumoVinculo.objects.bulk_create(resumos)


@transaction.atomic
def publicar_ciclo(ciclo):
    if ciclo.status != CicloAvaliacao.Status.FECHADO:
        return False
    if respostas_pendentes(ciclo).exists():
        return False
    gerar_resumos(ciclo)
    ciclo.status = CicloAvaliacao.Status.PUBLICADO
    ciclo.save(update_fields=("status",))
    return True
