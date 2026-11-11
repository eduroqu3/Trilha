# Deploy e operação

A TRILHA deve ser publicada como um único Web Service Python Django em Render ou Railway, atrás de HTTPS, com `DEBUG=False` e PostgreSQL do Supabase. Não versione `.env`, senhas ou chaves do Supabase.

## Serviço único

Use um único Web Service para a aplicação Django. Não é necessário criar um frontend separado, worker ou banco gerenciado pela plataforma de hospedagem.

**Build command:**

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py aplicar_rls
```

**Start command:**

```bash
gunicorn config.wsgi
```

O build precisa receber `DATABASE_URL`, porque `migrate` e `aplicar_rls` acessam o banco durante a preparação. Execute esse build apontando para um projeto Supabase de produção controlado e faça backup antes de migrar.

## Variáveis de ambiente

Configure no serviço, nunca no repositório:

- `SECRET_KEY`: valor longo, aleatório e exclusivo do ambiente.
- `DEBUG=False`.
- `DATABASE_URL`: URL PostgreSQL do Supabase com `sslmode=require`, preferencialmente pelo Session pooler.
- `ALLOWED_HOSTS`: somente os domínios reais do serviço.
- `CSRF_TRUSTED_ORIGINS`: somente origens HTTPS reais.
- `PUBLIC_HTTPS=True` quando o TLS termina no proxy do Render/Railway.
- `TRUST_PROXY_SSL_HEADER=True` somente quando o proxy sobrescreve `X-Forwarded-Proto` corretamente.
- `ALLOW_SEED_DEMO=False` ou ausente em produção.

Não configure chaves `anon`, `publishable` ou `service_role`: a aplicação não usa a Data API do Supabase.

## Banco e RLS

Mantenha um projeto Supabase separado para demonstração e produção. O projeto de demonstração pode receber `python manage.py seed_demo`; o projeto de produção não deve receber esse comando.

Depois de qualquer migração, confirme no SQL Editor:

```sql
SELECT count(*) AS public_tables,
       count(*) FILTER (WHERE rowsecurity) AS protected_tables,
       bool_and(rowsecurity) AS all_rowsecurity_true
FROM pg_catalog.pg_tables
WHERE schemaname = 'public';
```

Os números de tabelas públicas e protegidas devem ser iguais e `all_rowsecurity_true` deve ser `true`. A aplicação habilita RLS, mas não cria policies de negócio.

## Segurança operacional

Antes de publicar, confirme:

- HTTPS e redirecionamento SSL ativos.
- Cookies `Secure`, `HttpOnly` e `SameSite` coerentes com o proxy.
- CSRF em todos os formulários POST.
- `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` restritos.
- Logs sem corpo de requisição, senhas ou tokens.
- Backup e restauração testados.
- Limite de conexões do pooler compatível com o número de workers.
- `python manage.py check --deploy` executado e seus avisos avaliados.

Na verificação atual, `check --deploy` emitiu somente o aviso de `SECURE_HSTS_PRELOAD=False`. Não ative preload sem possuir domínio HTTPS estável, HSTS correto e intenção de manter a política para todos os subdomínios.

## Planos gratuitos

Render e Railway podem suspender ou fazer o serviço dormir em planos gratuitos ou de avaliação. O primeiro acesso depois de um período parado pode ser lento e conexões ao Supabase podem expirar. Para demonstrações, aceite esse comportamento e use um projeto Supabase separado; para produção, avalie um plano sem suspensão, monitore disponibilidade e configure backups.

## Pós-deploy

Teste `/`, `/entrar/`, `/cadastrar-escola/`, `/anonimato/` e os painéis autenticados. Faça um fluxo sintético completo em uma escola de demonstração, confirme o limiar mínimo e verifique RLS no Supabase. Nunca publique credenciais impressas pelo `seed_demo`.
