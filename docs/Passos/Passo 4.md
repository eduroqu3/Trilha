# Passo 4: Avaliação anônima

- [x] Criar `apps/avaliacoes` com `CicloAvaliacao`, `Pergunta`, `Participacao`, `Avaliacao`, `RespostaEscala` e `RespostaTexto`. O ciclo possui status `ABERTO`, `FECHADO` e `PUBLICADO`; perguntas possuem escala ou texto; respostas de texto possuem moderação `PENDENTE`, `APROVADO` e `REJEITADO`.
- [x] Manter a separação estrutural de anonimato: `Participacao` registra o aluno que já respondeu, enquanto `Avaliacao` e suas respostas não têm aluno, timestamp, IP, user agent, hash ou chave compartilhada com o aluno. O vínculo da avaliação é armazenado como identificador escalar para não criar uma relação ORM transitiva com `Usuario` por meio do professor.
- [x] Permitir um único ciclo não publicado por escola e gerar automaticamente seis perguntas de escala nas dimensões clareza, escuta, ritmo, organização, incentivo e acolhimento, além das duas perguntas de texto fixas. O ciclo nasce aberto.
- [x] Criar `/coordenacao/ciclos/` para coordenação abrir ciclos e listar os ciclos da própria escola.
- [x] Criar `/aluno/` com pendências somente dos vínculos das turmas matriculadas no ciclo aberto, incluindo estado vazio acolhedor.
- [x] Criar `/aluno/avaliar/<vinculo_id>/` com aviso de anonimato visível, confirmação obrigatória e questionário padrão.
- [x] Criar `/aluno/obrigado/` sem nome, e-mail, ID ou qualquer outro dado identificador no contexto ou no template.
- [x] Validar matrícula, escola, ciclo aberto e duplicidade antes do envio. Persistir `Participacao`, `Avaliacao` e respostas em uma única `transaction.atomic`; duplicatas exibem mensagem clara e não geram novo conteúdo.
- [x] Registrar `Avaliacao` e respostas no Admin como somente leitura, sem exclusão em massa.
- [x] Escrever o teste estrutural obrigatório de introspecção: falha se `Avaliacao`, `RespostaEscala` ou `RespostaTexto` alcançar `Usuario` por relações forward ou possuir campo de data/hora.
- [x] Testar envio válido, duplicado, ciclo fechado, aluno de outra turma, aluno de outra escola, questionário padrão, limite de ciclo e permissões do Admin.
- [x] Aplicar a migração do app e habilitar RLS no PostgreSQL de desenvolvimento. A verificação confirmou as seis tabelas de avaliações com `rowsecurity=true`, migração registrada e nenhuma policy criada.

## Validação local registrada

- `python manage.py check`: passou.
- `python manage.py makemigrations --check --dry-run`: nenhuma migração pendente.
- `python -m pytest`: 39 testes passaram.
- `python -m ruff check .`: passou na rodada final.
- `python manage.py migrate --noinput`: aplicado em banco SQLite temporário.
- `python manage.py aplicar_rls`: recusado no SQLite com a mensagem esperada de que o comando requer PostgreSQL; a etapa PostgreSQL foi executada e verificada no Supabase.
