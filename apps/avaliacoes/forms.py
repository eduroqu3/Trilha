from django import forms

from .models import CicloAvaliacao, Pergunta


class CicloAvaliacaoForm(forms.ModelForm):
    class Meta:
        model = CicloAvaliacao
        fields = ("nome",)
        labels = {"nome": "Nome do ciclo"}  # noqa: RUF012
        widgets = {  # noqa: RUF012
            "nome": forms.TextInput(
                attrs={"placeholder": "Ex.: Escuta do primeiro semestre"}
            )
        }


class AvaliacaoForm(forms.Form):
    confirmacao = forms.BooleanField(
        label=(
            "Entendo que esta avaliação é anônima e que não devo incluir meu nome "
            "ou detalhes que revelem quem sou."
        ),
        required=True,
    )

    def __init__(self, perguntas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.perguntas = tuple(perguntas)
        for pergunta in self.perguntas:
            field_name = f"pergunta_{pergunta.pk}"
            if pergunta.tipo == Pergunta.Tipo.ESCALA_1_5:
                self.fields[field_name] = forms.TypedChoiceField(
                    label=pergunta.texto,
                    choices=((valor, str(valor)) for valor in range(1, 6)),
                    coerce=int,
                    empty_value=None,
                    required=True,
                    widget=forms.RadioSelect,
                )
            else:
                self.fields[field_name] = forms.CharField(
                    label=pergunta.texto,
                    required=False,
                    widget=forms.Textarea(attrs={"rows": 4}),
                )

    def respostas(self):
        for pergunta in self.perguntas:
            valor = self.cleaned_data.get(f"pergunta_{pergunta.pk}")
            yield pergunta, valor
