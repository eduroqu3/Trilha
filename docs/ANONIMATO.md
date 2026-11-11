# Anonimato na trilha

A trilha foi desenhada para separar **quem participou** de **o que foi dito**. O registro `Participacao` confirma que um estudante já respondeu a um vínculo em um ciclo. O registro `Avaliacao` guarda o conteúdo da escuta, mas não tem relação, hash ou chave comum com o estudante. As respostas apontam apenas para a avaliação, a pergunta e o ciclo.

Essa separação acontece na arquitetura e na mesma transação do envio. A aplicação não grava IP junto da avaliação, não registra `created_at` nas avaliações ou respostas e não imprime o corpo de requisições nos logs. A tela de agradecimento não recebe identificador da avaliação e não o coloca na URL ou na sessão.

Os resultados têm uma proteção adicional: só são gerados quando o ciclo está publicado e o vínculo atinge o limiar mínimo configurado pela escola. O limiar padrão é cinco avaliações. Antes da publicação, comentários preenchidos passam por moderação sem autoria, data ou contexto individual.

## Limites que precisam ser conhecidos

Anonimato não significa que nenhuma pessoa possa suspeitar da autoria. Em uma turma pequena, o contexto pode tornar uma resposta reconhecível mesmo quando o banco não permite ligá-la tecnicamente a um estudante. O estilo de escrita, uma expressão muito particular ou um fato específico também podem revelar quem escreveu.

Por isso, não escreva seu nome, detalhes que identifiquem você ou informações que só uma pessoa poderia conhecer. A coordenação deve respeitar a separação feita pelo sistema e não tentar reconstituir a autoria a partir de contexto, estilo ou comparação entre respostas.

O anonimato reduz riscos por arquitetura; ele não elimina os riscos sociais de um grupo pequeno nem substitui uma cultura de escuta respeitosa. A explicação para estudantes está disponível em `/anonimato/`.
