# Instalação local

A TRILHA requer Python 3.12, Git, acesso a um PostgreSQL do Supabase e o CLI standalone do Tailwind CSS v4.3.5. Node.js não faz parte da stack. O banco do sistema é PostgreSQL; SQLite só deve ser usado como banco descartável de validação local.

## 1. Criar o projeto no Supabase

1. Crie um projeto separado para desenvolvimento ou demonstração no painel do Supabase.
2. Abra **Connect** e selecione o **Session pooler**.
3. Copie apenas a URL PostgreSQL do pooler e acrescente `sslmode=require` se ela ainda não estiver presente.
4. Não coloque no projeto as chaves `anon`, `publishable` ou `service_role`; a aplicação Django usa somente `DATABASE_URL`.
5. Mantenha um projeto Supabase separado para demonstração e produção. Nunca use `seed_demo` no banco de produção.

A URL tem este formato conceitual, com os valores reais preenchidos apenas no `.env` local:

```text
postgresql://postgres.<project-ref>:<senha>@<session-pooler-host>:5432/postgres?sslmode=require
```

## 2. Linux e macOS

```bash
git clone --branch passo7 https://github.com/eduroqu3/trilhaDjango.git
cd trilhaDjango
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

## 3. Windows PowerShell

```powershell
git clone --branch passo7 https://github.com/eduroqu3/trilhaDjango.git
Set-Location trilhaDjango
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Se a política do PowerShell impedir a ativação, use uma sessão autorizada ou execute diretamente `.\.venv\Scripts\python.exe` e `.\.venv\Scripts\pip.exe`; não altere a política global sem necessidade.

## 4. Configurar `.env`

Edite `.env` localmente. Nunca faça commit, upload ou copie o conteúdo desse arquivo para logs ou mensagens.

```dotenv
SECRET_KEY=uma-chave-local-longa-e-aleatoria
DEBUG=True
ALLOW_SEED_DEMO=False
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
DATABASE_URL=postgresql://postgres.<project-ref>:<senha>@<session-pooler-host>:5432/postgres?sslmode=require
PUBLIC_HTTPS=False
TRUST_PROXY_SSL_HEADER=False
```

`DATABASE_URL` é obrigatória. Se estiver ausente ou inválida, a aplicação deve falhar; ela não troca para SQLite automaticamente.

## 5. Migrar e habilitar RLS

```bash
python manage.py check --database default
python manage.py migrate
python manage.py aplicar_rls
```

Depois de cada `migrate` no PostgreSQL, execute novamente `python manage.py aplicar_rls`. O comando habilita Row Level Security nas tabelas públicas e não cria policies. Confirme no SQL Editor:

```sql
SELECT count(*) AS public_tables,
       count(*) FILTER (WHERE rowsecurity) AS protected_tables,
       bool_and(rowsecurity) AS all_rowsecurity_true
FROM pg_catalog.pg_tables
WHERE schemaname = 'public';
```

O resultado esperado é que `public_tables` e `protected_tables` sejam iguais e `all_rowsecurity_true` seja `true`.

## 6. Dados de demonstração e execução

Em um banco de desenvolvimento ou demonstração:

```bash
python manage.py seed_demo
python manage.py runserver
```

O comando cria dados fictícios e mostra credenciais temporárias no terminal. Não redirecione essa saída para logs públicos. Ele é bloqueado quando `DEBUG=False` e `ALLOW_SEED_DEMO` não está habilitado.

Abra `http://127.0.0.1:8000/`. Para testar sem seed, use `/cadastrar-escola/` e siga o fluxo de criação de turmas, professores, alunos, vínculos e ciclos.

## 7. Compilar e verificar o CSS

Baixe o CLI standalone v4.3.5 apropriado ao sistema. Em Linux x86_64:

```bash
curl -fL https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.5/tailwindcss-linux-x64 -o /tmp/tailwindcss
chmod +x /tmp/tailwindcss
/tmp/tailwindcss -i tailwind/input.css -o static/css/app.css --minify
```

Depois rode as verificações reais:

```bash
python manage.py check
python -m pytest
python -m ruff check .
```

## Problemas comuns

- **`DATABASE_URL` ausente:** copie `.env.example` para `.env` e preencha a URL do Session pooler com `sslmode=require`.
- **`password authentication failed`:** gere novamente a senha do banco no Supabase e confirme host, usuário, porta e project ref; não cole a senha em issues ou logs.
- **`SSL connection required`:** acrescente `?sslmode=require` à URL, preservando parâmetros existentes com `&`.
- **RLS não aparece ativo:** rode `python manage.py aplicar_rls` com a conexão correta e confira `pg_catalog.pg_tables`.
- **CSS desatualizado:** recompile de `tailwind/input.css` para `static/css/app.css` e confirme o arquivo versionado.
- **Erro de `collectstatic` com fonte Tailwind:** não mova a fonte para `static/`; ela fica em `tailwind/input.css` para não ser processada como asset público.
- **Cookies ou CSRF em HTTPS:** configure `PUBLIC_HTTPS=True`, `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` com os domínios reais; use `TRUST_PROXY_SSL_HEADER=True` somente atrás de proxy confiável.
