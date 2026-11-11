# TRILHA

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?logo=postgresql&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.3.5-06B6D4?logo=tailwindcss&logoColor=white)

![Logo da TRILHA](static/img/logo-completo.png)

## Sobre o projeto

A TRILHA é uma plataforma Django de escuta pedagógica. Escolas organizam ciclos de avaliação, estudantes compartilham percepções sobre suas aulas e professores recebem sinais agregados para orientar conversas e melhorias, sem rankings punitivos e sem identificar autores de respostas.

O projeto usa templates Django, sessões nativas, PostgreSQL no Supabase e assets locais. As regras de anonimato e a identidade visual estão definidas em [`docs/Contexto Fixo.md`](docs/Contexto%20Fixo.md) e [`docs/Design Fixo.md`](docs/Design%20Fixo.md).

## Funcionalidades

- [x] Cadastro público de uma escola e primeiro acesso da coordenação.
- [x] Login por e-mail, logout somente por `POST` e troca de senha.
- [x] Gestão de turmas, disciplinas, professores, estudantes, matrículas e vínculos.
- [x] Importação CSV de professores e estudantes com relatório de erros.
- [x] Ciclos com questionário fixo de seis escalas e duas perguntas abertas.
- [x] Respostas anônimas por arquitetura, moderação de comentários e limiar mínimo.
- [x] Resultados agregados somente após publicação e participação suficiente.
- [x] Página pública explicando a proteção e os limites do anonimato.
- [x] RLS habilitado nas tabelas públicas do Supabase, sem policies criadas pela aplicação.
- [x] Testes de instalação, fluxo integrado, permissões, isolamento, anonimato, acessibilidade e produção local.
- [ ] Editor customizável de perguntas — fora do escopo atual.
- [ ] Ranking ou comparação entre professores — não será implementado.

## Tecnologias utilizadas

| Categoria | Tecnologia |
| --- | --- |
| Linguagem | Python 3.12 |
| Framework | Django 5.2 |
| Banco | PostgreSQL no Supabase |
| Configuração | django-environ |
| Sessões e autenticação | Django Auth e sessões nativas |
| CSS | Tailwind CSS v4.3.5 via CLI standalone |
| Servidor | Gunicorn e WhiteNoise |
| Testes | pytest, pytest-django |
| Qualidade | Ruff |

Não há React, Node.js, Django REST Framework, JWT ou dependência de infraestrutura específica da plataforma no código da aplicação.

## Pré-requisitos e instalação rápida

Instale Python 3.12, Git, acesso a um PostgreSQL do Supabase e o CLI standalone do Tailwind CSS v4.3.5. Node.js não é necessário.

```bash
git clone --branch passo7 https://github.com/eduroqu3/trilhaDjango.git
cd trilhaDjango
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

No Windows PowerShell, use:

```powershell
git clone --branch passo7 https://github.com/eduroqu3/trilhaDjango.git
Set-Location trilhaDjango
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Preencha `.env` localmente com uma `SECRET_KEY` longa, `DATABASE_URL`, `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`. `DATABASE_URL` é obrigatória; não existe fallback para SQLite. Use o Session pooler do Supabase com `sslmode=require`. A aplicação não usa chaves `anon`, `publishable` ou `service_role`.

Para o passo a passo completo, incluindo criação do projeto Supabase, consulte [`docs/INSTALACAO.md`](docs/INSTALACAO.md). Para produção, consulte [`docs/DEPLOY.md`](docs/DEPLOY.md).

## Comandos principais

```bash
python manage.py check
python manage.py migrate
python manage.py aplicar_rls
python manage.py runserver
```

Em desenvolvimento autorizado, `python manage.py seed_demo` cria dados fictícios. O comando é bloqueado quando `DEBUG=False` e `ALLOW_SEED_DEMO` não está habilitado; nunca o use em um banco de produção com dados reais.

## Compilar o CSS

Baixe o CLI standalone v4.3.5 apropriado ao seu sistema na [página oficial de releases](https://github.com/tailwindlabs/tailwindcss/releases/tag/v4.3.5). Exemplo Linux x86_64:

```bash
curl -fL https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.5/tailwindcss-linux-x64 -o /tmp/tailwindcss
chmod +x /tmp/tailwindcss
/tmp/tailwindcss -i tailwind/input.css -o static/css/app.css --minify
```

A fonte fica em `tailwind/input.css`, fora da árvore pública de assets. O arquivo compilado `static/css/app.css` é versionado e é o único CSS coletado para produção.

## Como usar

O fluxo principal começa em `/cadastrar-escola/`. A coordenação cria turmas, disciplinas, professores, alunos, matrículas e vínculos; abre um ciclo; estudantes avaliam apenas aulas de suas turmas; a coordenação encerra, modera comentários e publica; professores veem somente resultados agregados elegíveis dos próprios vínculos.

Rotas principais:

| Rota | Uso |
| --- | --- |
| `/` | Landing institucional |
| `/anonimato/` | Explicação pública sobre anonimato |
| `/cadastrar-escola/` | Cadastro da escola e primeiro acesso |
| `/entrar/` | Login por e-mail |
| `/coordenacao/` | Painel da coordenação |
| `/aluno/` | Pendências do estudante |
| `/professor/` | Resultados agregados do professor |
| `/admin/` | Administração Django, quando habilitada |

## Verificações

```bash
python manage.py check
python -m pytest
python -m ruff check .
```

A rodada do Passo 7 também verificou instalação em ambiente virtual novo, migrações no Supabase, RLS nas 22 tabelas públicas, `seed_demo`, fluxo integrado completo, limiar abaixo do mínimo, isolamento entre escolas, auditoria de anonimato, `collectstatic`, Gunicorn, build do Tailwind e acessibilidade básica. O relatório detalhado está em [`docs/Passos/Passo 7.md`](docs/Passos/Passo%207.md).

## Estrutura de pastas

```text
trilhaDjango/
├── manage.py
├── requirements.txt
├── .env.example / .gitignore / README.md
├── config/                  # settings, URLs, WSGI e comandos
├── apps/
│   ├── contas/              # usuário, login, papéis e autenticação
│   ├── escolas/             # escola, turma, disciplina, matrícula e vínculo
│   └── avaliacoes/          # ciclos, perguntas, respostas e resultados
├── tailwind/input.css       # fonte do Tailwind, não servida diretamente
├── templates/               # base, contas, aluno, professor e coordenação
├── static/
│   ├── css/app.css          # CSS compilado e versionado
│   ├── js/                  # scripts de interface
│   └── img/                 # logo e ilustrações locais
├── tests/                   # pytest-django
└── docs/                    # contexto, design, passos, instalação e deploy
```

## Documentação

- [`docs/Contexto Fixo.md`](docs/Contexto%20Fixo.md): regras de stack, anonimato e escopo.
- [`docs/Design Fixo.md`](docs/Design%20Fixo.md): identidade visual e acessibilidade.
- [`docs/ANONIMATO.md`](docs/ANONIMATO.md): proteção e limites honestos.
- [`docs/INSTALACAO.md`](docs/INSTALACAO.md): instalação local detalhada.
- [`docs/DEPLOY.md`](docs/DEPLOY.md): deploy em um único Web Service Python.
- [`docs/Passos/`](docs/Passos/): histórico dos passos concluídos.
