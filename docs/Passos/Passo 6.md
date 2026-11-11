# Passo 6: Verificação de anonimato

- [x] Verificar por testes que avaliação e respostas não alcançam `Usuario`, que telas de avaliação e resultado não expõem identificação do estudante ou `created_at`, e que a tela de agradecimento não transporta identificadores.
- [x] Verificar que o corpo da requisição não aparece nos logs das rotas de avaliação.
- [x] Verificar ausência de filtros por atributo do aluno e de rotas de ranking.
- [x] Revisar a configuração de logging, headers de segurança em produção, CSRF nos formulários e proteção contra open redirect.
- [x] Criar a página pública `/anonimato/` e `docs/ANONIMATO.md`, com proteção e limites honestos.
- [x] Linkar a página pública no aviso da tela de avaliação.
- [x] Criar workflow do GitHub Actions com Ruff, pytest em PostgreSQL e verificação de compilação do Tailwind.
- [x] Confirmar no Supabase `trilha-dev`, por `pg_tables`, que todas as tabelas públicas estão com `rowsecurity = true`.
- [x] Garantir `DATABASE_URL` obrigatória, sem fallback para SQLite, e ignorar arquivos `*.sqlite3`.

## Validação

A validação local descartável pode usar SQLite apenas para feedback rápido. A suíte do workflow usa PostgreSQL por meio do serviço PostgreSQL do GitHub Actions; assim, os testes de anonimato, unicidade de `Participacao` e transação atômica rodam também contra PostgreSQL no CI.

A consulta de RLS no Supabase retornou 22 tabelas públicas e `all_rowsecurity_true = true`. Nenhum dado de usuário foi consultado.

## Pendente

A execução local desta branch depende de um `DATABASE_URL` PostgreSQL fornecido no ambiente de execução. Sem essa variável, o Django falha deliberadamente em vez de escolher SQLite. O workflow é a validação PostgreSQL reproduzível para o repositório.
