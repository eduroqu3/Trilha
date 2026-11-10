from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password

from apps.escolas.models import Escola

from .models import Usuario


class CadastroEscolaForm(forms.Form):
    nome_escola = forms.CharField(label="Nome da escola", max_length=180)
    nome_responsavel = forms.CharField(label="Seu nome", max_length=180)
    email = forms.EmailField(label="Seu e-mail")
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput)
    confirmar_senha = forms.CharField(
        label="Confirme a senha", widget=forms.PasswordInput
    )
    website = forms.CharField(required=False, label="Não preencher")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Não foi possível concluir o cadastro com esses dados."
            )
        return email

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")
        if senha and confirmar_senha and senha != confirmar_senha:
            self.add_error("confirmar_senha", "As senhas precisam ser iguais.")
        if senha and not self.errors.get("senha"):
            validate_password(senha)
        return cleaned_data

    def save(self):
        escola = Escola.objects.create(nome=self.cleaned_data["nome_escola"].strip())
        usuario = Usuario.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["senha"],
            nome=self.cleaned_data["nome_responsavel"].strip(),
            role=Usuario.Role.COORDENACAO,
            escola=escola,
        )
        return usuario


class LoginForm(forms.Form):
    email = forms.EmailField(label="E-mail")
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput)


class ContaPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label="Senha atual", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="Nova senha", widget=forms.PasswordInput)
    new_password2 = forms.CharField(
        label="Confirme a nova senha", widget=forms.PasswordInput
    )
