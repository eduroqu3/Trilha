# Instalação local

A TRILHA requer Python 3.12, Git, acesso a um PostgreSQL do Supabase e o CLI standalone do Tailwind CSS v4.3.5. Node.js não faz parte da stack.

Clone a branch desejada, crie um ambiente virtual e instale as dependências:

```bash
git clone --branch passo6 https://github.com/eduroqu3/trilhaDjango.git
cd trilhaDjango
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Preencha `.env` localmente com `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`. A aplicação falha de propósito quando `DATABASE_URL` está ausente; ela nunca troca o PostgreSQL por SQLite automaticamente.

```bash
python manage.py check --database default
python manage.py migrate
python manage.py aplicar_rls
python manage.py runserver
```

Depois de cada `migrate` no PostgreSQL, rode novamente `python manage.py aplicar_rls`. Para verificar o código sem banco compartilhado, SQLite pode ser usado somente em um arquivo descartável fora do repositório.

O CSS compilado é versionado. Recompile-o com o CLI standalone:

```bash
/tmp/tailwindcss -i static/src/input.css -o static/css/app.css --minify
```

As verificações da aplicação são:

```bash
python manage.py check
python -m pytest
python -m ruff check .
```
