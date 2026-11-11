# Passo 7 — Teste de tudo, correção e documentação

## Escopo

O Passo 7 verificou a aplicação da instalação ao fluxo interno, sem alterar o conteúdo dos documentos dos Passos 1 a 6. A implementação foi trabalhada na branch `passo7`.

## O que passou

- Instalação do zero em ambiente virtual temporário com `requirements.txt` e `pip check`.
- `python manage.py check`: passou sem problemas.
- `python -m pytest`: **79 testes passaram**.
- `python -m ruff check .`: passou.
- Build do Tailwind v4.3.5 comparado byte a byte com `static/css/app.css`: passou.
- `collectstatic --noinput`: passou após a correção do caminho da fonte Tailwind.
- Gunicorn em porta temporária: respondeu HTTP.
- `migrate` no PostgreSQL real do Supabase: sem migrações pendentes.
- `aplicar_rls`: passou.
- Consulta final ao Supabase: 22 tabelas públicas, 22 com `rowsecurity=true`, `all_rowsecurity_true=true`.
- `seed_demo`: criou 16 usuários, 2 turmas e 3 vínculos em banco de demonstração; os dados foram removidos ao final.
- Fluxo integrado real no PostgreSQL, com rollback dos dados sintéticos:
  - cadastro em `/cadastrar-escola/`;
  - turma, disciplina, professor, alunos, matrícula e vínculo;
  - ciclo e questionário padrão;
  - cinco alunos avaliando;
  - duplicata bloqueada;
  - coordenação encerrando, moderando e publicando;
  - professor vendo o resultado agregado;
  - logout;
  - ciclo abaixo do limiar sem resumo publicado;
  - permissões por papel e isolamento entre escolas.
- Auditoria do banco após o fluxo: zero colunas de timestamp nas tabelas de conteúdo anônimo e zero FKs dessas tabelas para `contas_usuario`.
- Auditoria de segredos: nenhum arquivo `.env` real versionado, nenhuma chave privada encontrada; os únicos marcadores de chaves Supabase são menções documentais, não valores.
- Acessibilidade básica: skip link, foco visível, `:focus-visible`, `:focus-within`, logo local e contraste calculado de 11,30:1 para texto escuro e 5,89:1 para verde profundo sobre creme.

## Falhas encontradas e corrigidas

1. O primeiro script de fluxo usou um host não permitido, depois foi executado com `ALLOWED_HOSTS` temporário apenas no processo de teste.
2. O teste temporário de sessão iterava valores em vez de chaves; foi corrigido no próprio script de validação.
3. A expectativa inicial da fila de moderação considerava uma resposta aberta por avaliação, mas o questionário tem duas; a validação foi corrigida para dez comentários em cinco avaliações.
4. A primeira limpeza do `seed_demo` encontrou a proteção `PROTECT` do modelo; a limpeza foi refeita respeitando a ordem das relações e terminou sem dados sintéticos.
5. `collectstatic` falhou porque `static/src/input.css` era tratado como asset CSS pelo WhiteNoise e a diretiva `@import "tailwindcss"` era processada pelo manifest. A fonte foi movida para `tailwind/input.css`; somente `static/css/app.css` é coletado.
6. O primeiro teste de acessibilidade procurava uma string textual incorreta e foi ajustado para os seletores CSS reais.

## Avisos e limitações

- `pytest` foi executado em SQLite descartável local; o fluxo integrado e as auditorias foram executados no PostgreSQL real do Supabase. As migrações e o RLS também foram verificados no Supabase.
- A suíte apresentou 62 avisos sobre o diretório `staticfiles/` ausente durante os testes locais. Isso não causou falhas; `collectstatic` foi executado separadamente com sucesso.
- `python manage.py check --deploy` emitiu um aviso sobre `SECURE_HSTS_PRELOAD=False`. Não foi ativado automaticamente porque preload exige domínio HTTPS estável e uma decisão operacional permanente.
- Não foi feito deploy externo real em Render ou Railway, nem teste manual com leitor de tela, teclado físico em navegador ou Windows PowerShell. Foram executadas verificações automatizadas equivalentes no ambiente Linux.
- A saída do `seed_demo` contém credenciais temporárias; ela foi redirecionada durante o teste e não foi incluída em logs, commits ou documentação.

## Riscos restantes

- Comentários podem revelar uma pessoa pelo estilo ou contexto, mesmo sem ligação técnica com usuário.
- Planos gratuitos de hospedagem podem dormir e aumentar a latência do primeiro acesso.
- O pooler, número de workers e `CONN_MAX_AGE` devem ser dimensionados para a conta real do Supabase.
- Policies de RLS continuam sendo uma responsabilidade de configuração do banco; o comando da aplicação apenas habilita `rowsecurity`.
