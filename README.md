# TRILHA — landing page

Landing page em português brasileiro renderizada por Django 5 com templates. Projeto deliberadamente estático: não usa banco de dados, API, DRF, JWT, React, Node ou TypeScript.

## Executar

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:3000
```

Tailwind CSS é carregado pelo Play CDN; Fraunces e Manrope vêm do Google Fonts. A ilustração do hero está no armazenamento gerenciado do projeto. O menu móvel e as perguntas do FAQ usam HTML nativo (`details`/`summary`) e não precisam de JavaScript de interação.
