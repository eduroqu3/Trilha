# Deploy e operação

A aplicação deve ser publicada como um único serviço Python Django, atrás de HTTPS, com `DEBUG=False` e `DATABASE_URL` fornecida pelo ambiente de execução. Não versione `.env`, senhas ou chaves do Supabase.

## Banco e conexão

Use o PostgreSQL do projeto `trilha-dev`. A conexão de referência documentada em `Contexto Fixo.md` é o Session pooler com `sslmode=require`. Para múltiplos workers web, o Transaction pooler pode reduzir a pressão sobre o limite de conexões; valide o comportamento do Psycopg e os prepared statements antes de adotá-lo.

Execute migrações em uma janela controlada e, depois de cada `migrate`, execute:

```bash
python manage.py aplicar_rls
```

A operação deve ser conferida em `pg_catalog.pg_tables`, garantindo `rowsecurity = true` em todas as tabelas públicas. A aplicação não cria policies e não usa a Data API, `anon`, `publishable` ou `service_role`.

## Configuração mínima

- `SECRET_KEY`: longa, aleatória e exclusiva do ambiente.
- `DEBUG=False`.
- `DATABASE_URL`: PostgreSQL do Supabase com SSL.
- `ALLOWED_HOSTS`: somente domínios reais da aplicação.
- `CSRF_TRUSTED_ORIGINS`: somente origens HTTPS reais.
- `PUBLIC_HTTPS=True` quando o TLS termina em proxy confiável.
- `TRUST_PROXY_SSL_HEADER=True` somente quando o proxy sobrescreve `X-Forwarded-Proto`.

## Servidor e segurança

Use Gunicorn ou um servidor WSGI/ASGI equivalente; não use `runserver` em produção. Execute `collectstatic --noinput` antes de publicar. Confirme cookies Secure/HttpOnly, redirecionamento HTTPS, HSTS, headers de segurança, CSRF nos formulários e proteção contra open redirect.

Monitore limite de conexões, erros de pool, latência, logs de erro e espaço de armazenamento. Faça backup e teste a restauração antes de considerar o ambiente pronto.

## Anonimato

Antes de publicar, confirme a suíte de testes, o limiar mínimo de resultados, a ausência de identificadores nas avaliações e o RLS no banco real. Os comentários podem revelar uma pessoa pelo contexto ou estilo de escrita; a documentação pública em `/anonimato/` deve permanecer acessível.
