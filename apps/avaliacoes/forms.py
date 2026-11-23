from django import forms

from .models import CicloAvaliacao, ModeloQuestionario, Pergunta


class CicloAvaliacaoForm(forms.ModelForm):
    modelo_questionario = forms.ModelChoiceField(queryset=ModeloQuestionario.objects.none(), label="Modelo de questionário", required=False)

    class Meta:
        model = CicloAvaliacao
        fields = ("nome", "modelo_questionario")
        labels = {"nome": "Nome do ciclo"}  # noqa: RUF012
        widgets = {"nome": forms.TextInput(attrs={"placeholder": "Ex.: Escuta do primeiro semestre"})}  # noqa: RUF012

    def __init__(self, escola=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.escola = escola
        self.fields["modelo_questionario"].queryset = ModeloQuestionario.objects.filter(escola=escola, ativo=True).order_by("nome") if escola else ModeloQuestionario.objects.none()

    def clean_modelo_questionario(self):
        modelo = self.cleaned_data.get("modelo_questionario")
        if modelo is None and self.escola is not None:
            modelo = self.fields["modelo_questionario"].queryset.first()
        if modelo is None:
            raise forms.ValidationError("Escolha um modelo ativo desta escola.")
        if self.escola is None or modelo.escola_id != self.escola.pk:
            raise forms.ValidationError("Escolha um modelo da sua escola.")
        return modelo


class AvaliacaoForm(forms.Form):
    confirmacao = forms.BooleanField(
        label=("Entendo que esta avaliação é anônima e que não devo incluir meu nome ou detalhes que revelem quem sou."),
        required=True,
    )

    def __init__(self, perguntas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.perguntas = tuple(perguntas)
        for pergunta in self.perguntas:
            field_name = f"pergunta_{pergunta.pk}"
            if pergunta.tipo == Pergunta.Tipo.ESCALA_1_5:
                self.fields[field_name] = forms.TypedChoiceField(
                    label=pergunta.texto, choices=((valor, str(valor)) for valor in range(1, 6)),
                    coerce=int, empty_value=None, required=pergunta.obrigatoria, widget=forms.RadioSelect,
                )
            elif pergunta.tipo == Pergunta.Tipo.ESCOLHA_UNICA:
                self.fields[field_name] = forms.ChoiceField(
                    label=pergunta.texto, choices=((opcao, opcao) for opcao in pergunta.opcoes),
                    required=pergunta.obrigatoria, widget=forms.RadioSelect,
                )
            else:
                self.fields[field_name] = forms.CharField(
                    label=pergunta.texto, required=pergunta.obrigatoria,
                    help_text="Não se identifique nem identifique colegas.",
                    widget=forms.Textarea(attrs={"rows": 4}),
                )

    def respostas(self):
        for pergunta in self.perguntas:
            yield pergunta, self.cleaned_data.get(f"pergunta_{pergunta.pk}"),
