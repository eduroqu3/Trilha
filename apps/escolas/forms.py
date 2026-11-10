import csv
import io

from django import forms
from django.core.exceptions import ValidationError

from apps.contas.models import Usuario

from .models import Disciplina, Matricula, Turma, Vinculo


class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ("nome", "ano_letivo")
        widgets = {  # noqa: RUF012
            "ano_letivo": forms.NumberInput(attrs={"min": 2000, "max": 2100})
        }

    def clean_ano_letivo(self):
        ano = self.cleaned_data["ano_letivo"]
        if not 2000 <= ano <= 2100:
            raise forms.ValidationError("Informe um ano letivo entre 2000 e 2100.")
        return ano


class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ("nome",)


class ProfessorForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ("nome", "email")

    def clean_email(self):
        return _email_normalizado(self.cleaned_data["email"])


class AlunoForm(forms.ModelForm):
    turma = forms.ModelChoiceField(queryset=Turma.objects.none(), label="Turma")

    class Meta:
        model = Usuario
        fields = ("nome", "email")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["turma"].queryset = Turma.objects.para_usuario(user)

    def clean_email(self):
        return _email_normalizado(self.cleaned_data["email"])


class VinculoForm(forms.ModelForm):
    professor = forms.ModelChoiceField(
        queryset=Usuario.objects.none(), label="Professor"
    )
    turma = forms.ModelChoiceField(queryset=Turma.objects.none(), label="Turma")
    disciplina = forms.ModelChoiceField(
        queryset=Disciplina.objects.none(), label="Disciplina"
    )

    class Meta:
        model = Vinculo
        fields = ("professor", "turma", "disciplina")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["professor"].queryset = Usuario.objects.da_escola(
            user, role=Usuario.Role.PROFESSOR
        )
        self.fields["turma"].queryset = Turma.objects.para_usuario(user)
        self.fields["disciplina"].queryset = Disciplina.objects.para_usuario(user)

    def clean(self):
        cleaned = super().clean()
        professor = cleaned.get("professor")
        turma = cleaned.get("turma")
        disciplina = cleaned.get("disciplina")
        if professor and turma and professor.escola_id != turma.escola_id:
            raise ValidationError(
                "Professor e turma precisam pertencer à mesma escola."
            )
        if turma and disciplina and turma.escola_id != disciplina.escola_id:
            raise ValidationError(
                "Turma e disciplina precisam pertencer à mesma escola."
            )
        return cleaned


class CSVImportForm(forms.Form):
    arquivo = forms.FileField(label="Arquivo CSV", required=True)

    def __init__(self, cabecalho, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cabecalho = tuple(cabecalho)

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        try:
            conteudo = arquivo.read().decode("utf-8-sig")
        except (UnicodeDecodeError, AttributeError) as exc:
            raise forms.ValidationError(
                "O CSV precisa estar codificado em UTF-8."
            ) from exc
        if not conteudo.strip():
            raise forms.ValidationError("O arquivo CSV está vazio.")
        arquivo.seek(0)
        try:
            leitor = csv.DictReader(io.StringIO(conteudo))
            if tuple(leitor.fieldnames or ()) != self.cabecalho:
                esperado = ",".join(self.cabecalho)
                raise forms.ValidationError(
                    f"O cabeçalho precisa ser exatamente: {esperado}."
                )
            linhas = list(leitor)
        except csv.Error as exc:
            raise forms.ValidationError("Não foi possível ler o CSV.") from exc
        if not linhas:
            raise forms.ValidationError("O arquivo CSV não possui linhas de dados.")
        arquivo.linhas_csv = linhas
        return arquivo


def _email_normalizado(email):
    email = email.strip().lower()
    if Usuario.objects.filter(email__iexact=email).exists():
        raise forms.ValidationError("Já existe uma conta com este e-mail.")
    return email


def validar_linha_csv(linha, numero, campos):
    erros = []
    valores = {campo: (linha.get(campo) or "").strip() for campo in campos}
    if not valores["nome"]:
        erros.append("nome obrigatório")
    email = valores["email"].lower()
    try:
        forms.EmailField().clean(email)
    except forms.ValidationError:
        erros.append("e-mail inválido")
    valores["email"] = email
    return valores, [f"Linha {numero}: {erro}." for erro in erros]


def validar_matricula(aluno, turma):
    if Matricula.objects.filter(aluno=aluno, turma=turma).exists():
        raise ValidationError("Este aluno já está matriculado nesta turma.")
