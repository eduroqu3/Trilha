# TRILHA

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?logo=postgresql&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.3.5-06B6D4?logo=tailwindcss&logoColor=white)

![Logo da TRILHA](static/img/logo-completo.png)

## Sobre o projeto

A TRILHA é uma plataforma Django de escuta pedagógica. Ela permite que escolas organizem ciclos de avaliação, estudantes compartilhem percepções sobre suas aulas e professores recebam sinais agregados para orientar conversas e melhorias, sem rankings punitivos e sem identificar autores de respostas.

O projeto é 100% Django com templates, sessão nativa, PostgreSQL no Supabase e assets locais. As regras de anonimato por arquitetura e a identidade visual estão definidas, respectivamente, em [`docs/Contexto Fixo.md`](docs/Contexto%20Fixo.md) e [`docs/Design Fixo.md`](docs/Design%20Fixo.md).

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
- [x] Validações locais com Ruff, pytest e verificação do CSS compilado.
- [ ] Editor customizável de perguntas — fora do escopo atual.
- [ ] Ranking ou comparação entre professores — não será implementado.

## Tecnologias utilizadas

| Categoria | Tecnologia |
| --- | --- |
| Linguagem | Python 3.12 |
| Framework | Django 5.2 |
| Banco | PostgreSQL 17 no Supabase |
| Configuração | django-environ |
| Sessões e autenticação | Django Auth e sessões nativas |
| CSS | Tailwind CSS v4.3.5 via CLI standalone |
| Servidor | Gunicorn e WhiteNoise |
| Testes | pytest, pytest-django |
| Qualidade | Ruff |

Não há React, Node.js, Django REST Framework, JWT ou dependência da infraestrutura da Manus no código da aplicação.

## Pré-requisitos e instalação

Instale Python 3.12, Git, PostgreSQL acessível pelo Supabase e o CLI standalone do Tailwind CSS v4.3.5. Node.js não é necessário. Para executar os testes em CI, o workflow também utiliza um serviço PostgreSQL temporário.

```bash
# Clone o repositório e selecione a branch atual
$ git clone --branch passo6 https://github.com/eduroqu3/trilhaDjango.git
$ cd trilhaDjango

# Crie e ative o ambiente virtual
$ python3.12 -m venv .venv
$ source .venv/bin/activate

# Instale as dependências fixadas
$ python -m pip install -r requirements.txt

# Crie a configuração local, sem versioná-la
$ cp .env.example .env
```

Edite `.env` localmente com `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`. `DATABASE_URL` é obrigatória e deve apontar para o PostgreSQL do projeto `trilha-dev`, com `sslmode=require`. Nunca cole o conteúdo de `.env` em commits, issues, logs ou mensagens.

Para o ambiente de referência, siga `docs/Contexto Fixo.md` e use o Session pooler do Supabase. Em uma implantação web com muitos workers, o Transaction pooler pode ser preferível; nesse caso, valide o comportamento do Psycopg, prepared statements e o valor de `CONN_MAX_AGE` antes da publicação.

```bash
# Valide a configuração e aplique as migrações
$ python manage.py check --database default
$ python manage.py migrate
$ python manage.py aplicar_rls

# Inicie o servidor de desenvolvimento
$ python manage.py runserver
```

Depois de qualquer `migrate` em um banco PostgreSQL, execute novamente `python manage.py aplicar_rls`. O comando habilita Row Level Security em todas as tabelas públicas e não cria policies. A Data API do Supabase e as chaves `anon`, `publishable` e `service_role` não são usadas pela aplicação.

### Compilar o CSS

Baixe o CLI standalone v4.3.5 apropriado ao seu sistema na [página oficial de releases](https://github.com/tailwindlabs/tailwindcss/releases/tag/v4.3.5). No Linux x86_64:

```bash
$ curl -fL https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.5/tailwindcss-linux-x64 -o /tmp/tailwindcss
$ chmod +x /tmp/tailwindcss
$ /tmp/tailwindcss -i static/src/input.css -o static/css/app.css --minify
```

O arquivo compilado `static/css/app.css` é versionado. Antes de publicar, confirme que ele corresponde à fonte `static/src/input.css`.

## Como usar

O fluxo principal começa com o cadastro da escola. A coordenação cria a estrutura escolar, cadastra ou importa pessoas, cria vínculos e abre um ciclo. Estudantes respondem somente sobre aulas de suas turmas; a tela de agradecimento não transporta identificadores da avaliação. Depois do encerramento e da moderação, a coordenação publica o ciclo. Professores veem apenas resultados agregados elegíveis dos próprios vínculos.

Rotas principais para testar manualmente:

| Rota | Uso |
| --- | --- |
| `/` | Landing institucional |
| `/anonimato/` | Explicação pública sobre anonimato |
| `/cadastrar-escola/` | Cadastro do primeiro acesso da escola |
| `/entrar/` | Login por e-mail |
| `/coordenacao/` | Painel e navegação da coordenação |
| `/aluno/` | Pendências do estudante |
| `/professor/` | Resultados agregados do professor |
| `/admin/` | Administração Django, quando habilitada |

Em desenvolvimento autorizado, `python manage.py seed_demo` cria dados fictícios para testar o fluxo. O comando só funciona com `DEBUG=True` ou `ALLOW_SEED_DEMO=true` e não deve ser habilitado em produção.

## Verificações

```bash
$ python manage.py check
$ python -m pytest
$ python -m ruff check .
```

Execute a suíte localmente contra PostgreSQL sempre que possível. SQLite pode ser usado apenas como banco descartável de validação local rápida; não existe fallback para SQLite nas configurações da aplicação.

## Estrutura de pastas

```text
trilha/
├── manage.py
├── requirements.txt
├── .env.example / .gitignore / README.md
├── config/                  # settings, URLs, WSGI e comandos
├── apps/
│   ├── contas/              # usuário, login, papéis e autenticação
│   ├── escolas/             # escola, turma, disciplina, matrícula e vínculo
│   └── avaliacoes/          # ciclos, perguntas, respostas e resultados
├── templates/
│   ├── base.html / landing.html / anonimato.html
│   ├── componentes/         # componentes efetivamente reutilizados
│   ├── contas/              # cadastro, login e troca de senha
│   ├── aluno/               # dashboard, pendências, avaliação e agradecimento
│   ├── professor/           # dashboard com resultados agregados
│   └── coordenacao/         # dashboard e gestão escolar
├── static/
│   ├── src/input.css        # fonte do Tailwind, não servida diretamente
│   ├── css/app.css          # CSS compilado e versionado
│   ├── js/                  # scripts pequenos de interface
│   └── img/                 # logo oficial e ilustração local
├── tests/                   # pytest-django
└── docs/                    # contexto, design, passos, instalação e deploy
```

## Documentação

- [`docs/Contexto Fixo.md`](docs/Contexto%20Fixo.md): regras de stack, anonimato e escopo.
- [`docs/Design Fixo.md`](docs/Design%20Fixo.md): identidade visual e acessibilidade.
- [`docs/ANONIMATO.md`](docs/ANONIMATO.md): proteção e limites honestos.
- [`docs/INSTALACAO.md`](docs/INSTALACAO.md): instalação local detalhada.
- [`docs/DEPLOY.md`](docs/DEPLOY.md): checklist de produção e Supabase.
- [`docs/Passos/`](docs/Passos/): histórico dos passos concluídos.
