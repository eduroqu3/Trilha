from django.db import transaction

from .models import CicloAvaliacao, Pergunta

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
