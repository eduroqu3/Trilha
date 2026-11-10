# TRILHA — landing page

Landing page em português brasileiro renderizada por Django 5 com templates. Projeto deliberadamente estático: não usa banco de dados, API, DRF, JWT, React, Node ou TypeScript.

## Executar

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:3000
```

## Compilar o CSS

O CSS compilado `static/css/app.css` já está versionado. Para recompilá-lo sem Node, baixe o CLI standalone Tailwind v3.4.17 e execute:

```bash
curl -fsSL https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64 -o /tmp/tailwindcss
chmod +x /tmp/tailwindcss
/tmp/tailwindcss -i static/css/tailwind.input.css -o static/css/app.css --content 'templates/**/*.html' --minify
```

O logo e a ilustração do hero são arquivos locais em `static/img/`. Fraunces e Manrope vêm do Google Fonts. O menu móvel e as perguntas do FAQ usam HTML nativo (`details`/`summary`) e não precisam de JavaScript de interação.
