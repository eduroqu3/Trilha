# TODO — Parte 0: limpeza e reorganização

- [x] Remova `manus-routes.json`, a view `route_manifest` e sua rota. Tire `__pycache__` do controle de versão. Em `.gitignore`, inclua `.env`, `.venv`, `__pycache__`, `staticfiles/` e `*.sqlite3`.
- [x] Renomeie `trilha_site` para `config` e atualize `manage.py`, `wsgi.py`, `ROOT_URLCONF` e `WSGI_APPLICATION`; mantenha `/` funcionando.
- [x] Crie `templates/base.html` para fontes, CSS e blocos de conteúdo; faça `landing.html` estendê-lo sem alterar conteúdo ou visual.
- [x] Migre o CSS para Tailwind v4 via CLI standalone: crie `static/src/input.css` com `@import "tailwindcss"`, `@source` para `templates/`, `@theme` com os tokens da paleta e o CSS de `site.css`; gere e versiona `static/css/app.css`. Compare a landing antes/depois e confirme visual equivalente antes de remover a folha antiga/CDN. Apague `static/css/tailwind.input.css`; não adicione Node.
- [x] Mantenha apenas as imagens realmente referenciadas em `static/`; não deixe URLs externas de imagens nem arquivos, rotas ou caminhos específicos da plataforma.
- [x] Mova `visuals.md` para `docs/`; reescreva `README.md` para Django, execução e estrutura sem referências à plataforma; fixe as versões das dependências reais.
- [x] Rode `manage.py check`, abra a landing para validação e faça commit na branch `tests`, mantendo `main` intacta.
