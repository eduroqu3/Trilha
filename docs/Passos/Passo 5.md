# Passo 5: Encerrar, moderar, publicar e ver resultados

- [x] Adicionar à coordenação as transições `ABERTO → FECHADO` e `FECHADO → PUBLICADO`, sempre por POST e isoladas pela escola do usuário.
- [x] Exibir adesão agregada por turma durante cada ciclo, somente como quantidade de participações sobre o total de matrículas, sem nomes de quem respondeu ou não.
- [x] Criar fila de moderação para comentários de texto pendentes, em ordem aleatória, mostrando somente o texto e as ações Aprovar/Rejeitar; a fila não exibe vínculo, data ou autoria.
- [x] Impedir publicação enquanto houver comentário preenchido com status `PENDENTE`.
- [x] Criar `ResumoVinculo` com ciclo, vínculo, número de avaliações e médias por dimensão em JSON. Gerar resumos somente na publicação e somente quando o vínculo atingir `escola.limiar_minimo`.
- [x] Criar o painel do professor com apenas seus próprios vínculos, somente para ciclos `PUBLICADO` com limiar atingido, médias em barras HTML/CSS e comentários `APROVADO` embaralhados, sem datas, ranking, comparação ou ordenação por nota.
- [x] Exibir mensagem acolhedora sem números quando ainda não houver resultado elegível para o professor.
- [x] Registrar `ResumoVinculo` no Admin como somente leitura e sem exclusão em massa.
- [x] Testar publicação bloqueada por moderação pendente, limiar mínimo, ciclo aberto/fechado sem resultados, isolamento entre professores e escolas, ausência de nomes na coordenação, moderação e integridade do resumo.
- [x] Aplicar a migração do resumo e a relação com `Vinculo` no Supabase `trilha-dev`; habilitar RLS novamente em todas as tabelas públicas, sem policies. A verificação confirmou `avaliacoes_resumovinculo` com RLS ativo e suas FKs para ciclo e vínculo.
- [x] Tornar as migrações `0002_resumovinculo` e `0003_alter_resumovinculo_vinculo` idempotentes: em um banco novo elas criam a estrutura; em um banco que já possui a tabela e a FK, apenas reconhecem a estrutura e registram o estado Django, sem tentar recriar a relação.

## Validação local registrada

- `python manage.py check`: passou.
- `python -m pytest`: **64 testes passaram** na rodada final.
- `python -m ruff check .`: passou na rodada final.
- `python manage.py migrate --noinput`: aplicado em banco SQLite temporário.
- `python manage.py makemigrations --check --dry-run`: nenhuma migração pendente.
- Migração em banco novo e migração com `avaliacoes_resumovinculo` previamente existente: ambas concluídas sem `DuplicateTable`.
- `python manage.py aplicar_rls`: recusado no SQLite com a mensagem esperada de que requer PostgreSQL; no Supabase, a operação equivalente do comando foi executada e verificada após a migração.

## Observação de execução

Durante o desenvolvimento, uma primeira rodada do teste novo de adesão falhou porque o cenário ainda não havia criado uma participação; o teste foi corrigido para usar um registro real. Outra rodada apontou o uso de um ID inteiro em um novo `ForeignKey`; o serviço e o teste foram ajustados. A rodada final terminou sem falhas.
