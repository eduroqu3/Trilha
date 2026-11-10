import secrets

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.contas.models import Usuario
from apps.escolas.models import Disciplina, Escola, Matricula, Turma, Vinculo


class Command(BaseCommand):
    help = "Cria dados fictícios de demonstração para uma escola."

    def handle(self, *args, **options):
        if not settings.DEBUG and not settings.ALLOW_SEED_DEMO:
            raise CommandError(
                "seed_demo bloqueado: use DEBUG=True ou ALLOW_SEED_DEMO=true."
            )
        with transaction.atomic():
            escola = self._escola()
            credenciais = [self._usuario(escola, "Coordenação", "coord-demo")]
            turmas = [
                self._turma(escola, "6º ano A", 2026),
                self._turma(escola, "7º ano A", 2026),
            ]
            disciplinas = [
                self._disciplina(escola, "Língua Portuguesa"),
                self._disciplina(escola, "Matemática"),
                self._disciplina(escola, "Ciências"),
            ]
            professores_com_credencial = [
                self._usuario(escola, "Professora Ana Demo", "ana-demo"),
                self._usuario(escola, "Professor Bruno Demo", "bruno-demo"),
                self._usuario(escola, "Professora Carla Demo", "carla-demo"),
            ]
            credenciais.extend(professores_com_credencial)
            professores = [professor for professor, _ in professores_com_credencial]
            for indice, turma in enumerate(turmas):
                for numero in range(1, 7):
                    credenciais.append(
                        self._aluno(
                            escola,
                            turma,
                            f"Aluno {indice + 1}-{numero}",
                            f"aluno-{indice + 1}-{numero}-demo",
                        )
                    )
            for professor, disciplina in zip(professores, disciplinas, strict=True):
                Vinculo.objects.get_or_create(
                    professor=professor,
                    turma=turmas[0],
                    disciplina=disciplina,
                )
        self.stdout.write(self.style.SUCCESS("Dados de demonstração criados."))
        self.stdout.write(f"Escola: {escola.nome}")
        self.stdout.write("Credenciais de teste:")
        for usuario, senha in credenciais:
            self.stdout.write(f"- {usuario.email}: {senha}")

    def _escola(self):
        escola, _ = Escola.objects.get_or_create(
            nome="Escola Horizonte Demo", defaults={"limiar_minimo": 5}
        )
        return escola

    def _turma(self, escola, nome, ano_letivo):
        turma, _ = Turma.objects.get_or_create(
            escola=escola, nome=nome, ano_letivo=ano_letivo
        )
        return turma

    def _disciplina(self, escola, nome):
        disciplina, _ = Disciplina.objects.get_or_create(escola=escola, nome=nome)
        return disciplina

    def _usuario(self, escola, nome, identificador, role=None):
        role = role or (
            Usuario.Role.COORDENACAO
            if identificador == "coord-demo"
            else Usuario.Role.PROFESSOR
        )
        email = f"{identificador}@demo.trilha.local"
        usuario, _ = Usuario.objects.get_or_create(
            email=email,
            defaults={"nome": nome, "role": role, "escola": escola},
        )
        senha = secrets.token_urlsafe(10)
        usuario.nome = nome
        usuario.role = role
        usuario.escola = escola
        usuario.set_password(senha)
        usuario.save(update_fields=("nome", "role", "escola", "password"))
        return usuario, senha

    def _aluno(self, escola, turma, nome, identificador):
        usuario, senha = self._usuario(
            escola, nome, identificador, role=Usuario.Role.ALUNO
        )
        Matricula.objects.get_or_create(aluno=usuario, turma=turma)
        return usuario, senha
