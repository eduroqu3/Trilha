# Passo 3: Estrutura escolar (somente coordenação).

- [x] Criar `Turma` (`nome`, `ano_letivo` e escola), `Disciplina` (`nome` e escola), `Matricula` (aluno ↔ turma) e `Vinculo` (professor + turma + disciplina, único por trio) em `apps/escolas`, com restrições de unicidade, validação de escola e registro no Admin.
- [x] Implementar managers/querysets isolados por escola (`para_usuario`/`da_escola`) e usá-los nas views de turmas, disciplinas, professores, alunos e vínculos. As views não recebem escola por parâmetro.
- [x] Criar telas protegidas por `COORDENACAO` para listar, cadastrar e remover turmas e disciplinas.
- [x] Criar cadastro individual e importação CSV de professores (`nome,email`) e alunos (`nome,email,turma`), com validação linha a linha, relatório de erros, senha provisória aleatória exibida no resultado e download CSV das credenciais.
- [x] Criar tela de vínculos entre professor, turma e disciplina, com prevenção de vínculo duplicado.
- [x] Criar `python manage.py seed_demo`, bloqueado em produção salvo `ALLOW_SEED_DEMO=true`, com uma escola, duas turmas, 12 alunos, três professores, uma coordenação, disciplinas e vínculos. O comando imprime as credenciais fictícias de teste quando autorizado.
- [x] Escrever testes de isolamento entre escolas, permissão por papel, cadastros individuais, importações válidas e inválidas, vínculo duplicado e bloqueio/autorização do `seed_demo`.
- [x] Rodar a migração equivalente a `migrate` e `aplicar_rls` no banco PostgreSQL do ambiente de desenvolvimento. A verificação confirmou as quatro tabelas escolares com `rowsecurity=true`, o registro da migração e nenhuma policy criada. A execução local com SQLite também foi realizada; nela `aplicar_rls` foi recusado corretamente por exigir PostgreSQL.

## Validação local registrada

- `python manage.py check`: passou.
- `python -m pytest`: 30 testes passaram.
- `python -m ruff check .`: passou.
- `python manage.py makemigrations --check --dry-run`: nenhuma migração pendente.
