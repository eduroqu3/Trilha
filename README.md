# TRILHA

Landing institucional em português brasileiro e aplicação Django 5.2, servida por templates. O sistema usa sessões nativas do Django, PostgreSQL e arquivos estáticos locais. O Passo 2 adiciona contas, escolas, autenticação por e-mail e painéis provisórios por papel.

## Requisitos

- Python 3.12
- PostgreSQL no Supabase, via Session pooler (porta 5432 e `sslmode=require`)
- CLI standalone do Tailwind CSS v4 apenas para recompilar o CSS; Node.js não é necessário

## Configurar e executar localmente

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edite `.env` localmente e informe `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`. A URL do banco deve ser a do Session pooler copiada do painel Supabase Connect, com `sslmode=require`. Não versione nem imprima `.env`.

```bash
python manage.py check --database default
python manage.py migrate
python manage.py aplicar_rls
python manage.py runserver
```

**Depois de todo `migrate`, rode novamente `python manage.py aplicar_rls`.** O comando habilita Row Level Security em cada tabela do schema `public` e não cria policies. O projeto não usa chaves `anon`/`publishable` nem `service_role`; a aplicação conecta diretamente ao PostgreSQL pelo Django. A Data API do projeto Supabase atual está desativada; não a reative sem revisar o acesso.

A landing fica em `http://127.0.0.1:8000/`; o admin padrão do Django fica em `/admin/`. Para gerar um usuário administrativo, use `python manage.py createsuperuser`.

## Segurança e configuração

As configurações vêm de variáveis de ambiente lidas por `django-environ`: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, `PUBLIC_HTTPS` e `TRUST_PROXY_SSL_HEADER`. Com `DEBUG=False`, cookies ficam `Secure`, o redirecionamento HTTPS, HSTS e os cabeçalhos de segurança são habilitados. Atrás de um proxy TLS, habilite `TRUST_PROXY_SSL_HEADER` apenas se o proxy confiável remover e definir `X-Forwarded-Proto`.

WhiteNoise serve estáticos comprimidos usando nomes versionados. Antes de publicar, compile o CSS e execute `python manage.py collectstatic --noinput`.

## Tailwind CSS v4

`static/src/input.css` contém `@import "tailwindcss"`, as fontes de templates e os tokens da paleta fixa. O build `static/css/app.css` é versionado. Baixe o CLI standalone v4.3.5 apropriado ao seu sistema na [página oficial de releases](https://github.com/tailwindlabs/tailwindcss/releases/tag/v4.3.5). Exemplo Linux x86_64:

```bash
curl -fL https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.5/tailwindcss-linux-x64 -o /tmp/tailwindcss
chmod +x /tmp/tailwindcss
/tmp/tailwindcss -i static/src/input.css -o static/css/app.css --minify
```

Para observar mudanças em desenvolvimento e recompilar automaticamente:

```bash
/tmp/tailwindcss -i static/src/input.css -o static/css/app.css --watch
```

A landing carrega `app.css` local; não usa o Play CDN. As fontes Fraunces e Manrope são servidas pelo Google Fonts.

## Verificações

```bash
python manage.py check
python -m pytest
python -m ruff check .
```

## Estrutura

```text
manage.py                         comandos Django
config/                            settings, URLs, views, WSGI e comandos
  management/commands/aplicar_rls.py
templates/base.html                metadados, fontes, CSS e estrutura comum
templates/landing.html             conteúdo institucional
templates/componentes/              componentes de formulário e identidade visual
templates/contas/                   cadastro, login e troca de senha
templates/painel/                   painel provisório por papel
apps/contas/                        usuário, autenticação e papéis
apps/escolas/                       escola e vínculo do usuário
static/src/input.css               fonte Tailwind v4
static/css/app.css                 build compilado e versionado
static/img/                        imagens locais da landing
tests/                             testes pytest-django
.env.example                       exemplo sem credenciais
docs/Contexto Fixo.md              stack, anonimato e decisões do MVP
docs/Design Fixo.md                identidade visual e diretrizes
requirements.txt                   dependências Python fixadas
```
