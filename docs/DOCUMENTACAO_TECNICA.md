# Documentação Técnica — Trilha: Avaliação e Escuta Pedagógica

---

## 1. Identificação do Sistema, Integrantes e Objetivo

### 1.1 Nome do Sistema
**Trilha — Avaliação de Professores e Escuta Pedagógica**

### 1.2 Integrantes do Projeto e Identificação Acadêmica
- **Equipe de Desenvolvimento:**
  - Eduardo Vieira Roque
  - Gustavo Costa Trindade
  - Guilherme Vilares
  - Aron Maesta
  - Diogo Ferrata
- **Instituição de Ensino:** SENAI
- **Professor Orientador:** Prof. Jhonny Braga
- **Ambiente de Produção (Render):** [https://trilhadjango.onrender.com](https://trilhadjango.onrender.com)
- **Repositório do Código-Fonte:** [https://github.com/eduroqu3/Trilha.git](https://github.com/eduroqu3/Trilha.git) (Branch `CodeFreeze`)

### 1.3 Objetivo Geral e Princípios
O **Trilha** é um sistema web concebido para transformar a avaliação institucional docente em um processo contínuo de **escuta pedagógica construtiva e humanizada**.

Diferente de sistemas punitivos ou de ranqueamento, a Trilha foi construída com base em premissas inegociáveis de design e arquitetura:
1. **Anonimato Absoluto:** As avaliações registradas pelos estudantes não possuem chave estrangeira (FK), hash, endereço IP nem registro de data/hora que possa correlacionar a resposta ao estudante avaliador. A gravação é desacoplada e atômica.
2. **Sem Ranqueamento:** O sistema não produz pódios, notas públicas comparativas ou listas ranqueadas entre professores.
3. **Limiar Mínimo de Proteção (`limiar_minimo`):** Resultados consolidados e comentários de uma turma só se tornam visíveis para o professor ou coordenação após atingir uma quantidade mínima de respostas (por padrão, 5 avaliações), impedindo inferências por exclusão estatística.
4. **Ciclos Fechados de Escuta:** As avaliações ocorrem dentro de ciclos temporais definidos pela coordenação escolar (Aberto, Fechado e Publicado), garantindo organização de semestre/ano letivo.

---

## 2. Tecnologias Utilizadas e Funcionalidades Desenvolvidas

### 2.1 Stack Tecnológico
- **Linguagem Backend:** Python 3.12 (tipagem estrita, generators, decorators e context managers).
- **Framework Web:** Django 5.2.19 (arquitetura MTV, Django ORM, formulários limpos, CSRF tokens, Session Authentication, Custom User Model).
- **Banco de Dados:** PostgreSQL (hospedado no Supabase), acessado via driver de alto desempenho `psycopg` (versão 3). Utilização de **Row Level Security (RLS)** nativo e multi-tenancy lógico por escola.
- **Frontend & Interface:**
  - **HTML5 Semântico:** Atributos de acessibilidade ARIA, skip-links, navegação por teclado e formulários com acessibilidade nativa.
  - **CSS3 Puro (Sem frameworks pesados):** Custom properties variáveis (`--cream`, `--sand`, `--deep`, `--mustard`, `--pale`), design system com bordas sutis (radius ≤ 3px), sombras projetadas nítidas sem blur e tipografia padronizada:
    - *Fraunces (Serif):* Exclusiva para títulos e elementos de destaque humanizado.
    - *Manrope (Sans):* Para corpos de texto, botões, tabelas e dados operacionais.
  - **JavaScript Vanilla (ES6+):** Filtragem dinâmica client-side de tabelas em tempo real sem recarregar página nem afetar o scroll, e gerenciador assíncrono de notificações/mensagens de sistema.
- **Servidor WSGI & Estáticos:** Gunicorn 27.0.0 em produção (Render) e WhiteNoise 6.12.0 para entrega comprimida e eficiente de arquivos estáticos.
- **Qualidade e Testes:** `pytest` 9.2 com `pytest-django` 4.14 e linter/formatter `ruff` 0.17.

### 2.2 Funcionalidades Desenvolvidas

#### Gestão de Acesso e Contas Seguras (`apps.contas`)
- **Autenticação Segura:** Autenticação por e-mail e senha com backend customizado `EmailBackend`.
- **Troca Obrigatória de Senha:** Usuários criados provisoriamente recebem uma flag `precisa_trocar_senha=True` e a senha provisória fica registrada criptograficamente até o primeiro acesso. Enquanto pendente, um middleware dedicado intercepta e redireciona todas as requisições para a tela `/conta/senha/`.
- **Ações da Conta Padronizadas:** Componente unificado contendo botões alinhados de retorno, troca de senha e encerramento de sessão via método HTTP POST (protegido contra CSRF).
- **Telas de Erro Customizadas:** Páginas de status HTTP 403 (Acesso Negado), 404 (Página Não Encontrada) e 500 (Erro Interno) integradas ao design system acolhedor da Trilha.

#### Espaço da Coordenação (`apps.contas` e `apps.escolas`)
- **Central Única de Gestão de Usuários (`/coordenacao/usuarios/`):**
  - Cadastro individual e importação via planilha CSV de Professores.
  - Cadastro individual e importação via planilha CSV de Estudantes com indicação de turma.
  - Cadastro individual e importação via planilha CSV de novos membros da Coordenação.
  - Tabela geral de usuários com indicação de papel, turma vinculada, credencial provisória e status.
  - Filtro instantâneo em tempo real por abas (Todos, Aluno, Professor, Coordenação) sem requisições HTTP desnecessárias.
  - Controle de ativação/desativação de contas com segurança (um coordenador nunca pode desativar a si próprio).
  - Geração de novas senhas provisórias para estudantes ou professores sem invalidar participações prévias.
- **Gestão Unificada de Turmas e Disciplinas (`/coordenacao/turmas/`):**
  - Criação e exclusão de turmas organizadas por ano letivo.
  - Criação e exclusão de disciplinas curriculares da escola.
- **Vínculos Pedagógicos (`/coordenacao/vinculos/`):**
  - Mapeamento das relações tripartites: *Professor + Disciplina + Turma*.
- **Ciclos e Escuta Pedagógica (`/coordenacao/ciclos/`):**
  - Abertura de novos ciclos baseados no modelo de questionário da Trilha.
  - Acompanhamento em tempo real da taxa de adesão agregada por turma (ex: 28/30 respondidos).
  - Encerramento do ciclo para bloqueio de novas submissões.
  - Moderação ativa de comentários textuais (aprovação ou rejeição de conteúdo que viole as diretrizes de respeito).
  - Publicação oficial das métricas consolidadas após atingimento dos critérios de anonimato.

#### Espaço do Estudante (`apps.avaliacoes`)
- **Painel de Pendências:** Listagem limpa dos professores e disciplinas que o estudante ainda não avaliou no ciclo atual.
- **Formulário de Avaliação Pedagógica:**
  - Perguntas com escala Likert de 1 a 5 cobrindo as dimensões pedagógicas fundamentais: *Clareza, Escuta, Ritmo, Organização, Incentivo e Acolhimento*.
  - Perguntas de texto dissertativas para feedback aberto e construtivo.
- **Gravação Segura e Atômica:** Separação entre a tabela de controle de participação (que sabe quem respondeu para evitar duplicidade) e o registro da avaliação (que não guarda nenhum dado pessoal).

#### Espaço do Professor (`apps.contas`)
- **Painel de Resultados Pedagógicos:** Visualização gráfica das médias ponderadas por dimensão para cada turma lecionada (somente exibido se `total_avaliacoes >= limiar_minimo`).
- **Mural de Comentários Moderados:** Exibição em ordem aleatória dos comentários aprovados pela moderação, garantindo que a sequência temporal não revele o autor.

---

## 3. Organização e Estrutura de Pastas e Arquivos

O projeto adota a arquitetura modular padrão do Django, agrupando domínios de negócio em subaplicações (`apps/`):

```text
Trilha/
├── .env.example              # Modelo de variáveis de ambiente
├── .gitignore                # Regras de exclusão Git (venv, logs, pycache)
├── manage.py                 # Utilitário de linha de comando Django
├── pytest.ini                # Configurações de execução do framework Pytest
├── requirements.txt          # Dependências do ecossistema Python
├── ruff.toml                 # Regras estritas de linting e padronização PEP 8
│
├── config/                   # Núcleo de Configuração do Projeto Django
│   ├── asgi.py               # Ponto de entrada ASGI
│   ├── settings.py           # Configurações do Django (banco, auth, middleware)
│   ├── urls.py               # Roteador central de URLs da aplicação
│   └── wsgi.py               # Ponto de entrada WSGI para servidores de produção
│
├── apps/                     # Módulos de Domínio da Aplicação
│   ├── contas/               # Gerenciamento de Usuários, Sessões e Permissões
│   │   ├── backends.py       # Autenticação personalizada por e-mail
│   │   ├── context_processors.py # Processador de navegação e URLs de retorno
│   │   ├── decorators.py     # Decorators para restrição de rotas por papel
│   │   ├── forms.py          # Formulários de Login, Troca de Senha e Coordenação
│   │   ├── middleware.py     # Interceptador de troca obrigatória de senha
│   │   ├── models.py         # Modelo customizado de Usuario (Role: ALUNO, PROFESSOR, COORDENACAO)
│   │   ├── urls.py           # Rotas de autenticação e gestão de usuários
│   │   └── views.py          # Controladores de login, logout e usuários
│   │
│   ├── escolas/              # Estrutura Organizacional Escolar
│   │   ├── forms.py          # Formulários de Turma, Disciplina, Professor e CSV
│   │   ├── models.py         # Modelos: Escola, Turma, Disciplina, Vinculo, Matricula
│   │   ├── services.py       # Serviços de importação CSV e cadastro transacional
│   │   ├── urls.py           # Rotas de turmas, disciplinas e vínculos
│   │   ├── views.py          # Controladores de gestão escolar
│   │   └── management/
│   │       └── commands/
│   │           └── seed_demo.py # Comando de população completa do banco de dados
│   │
│   └── avaliacoes/           # Mecanismo de Escuta e Anonimato
│       ├── forms.py          # Formulários de preenchimento do questionário
│       ├── models.py         # Modelos de Questionários, Ciclos, Perguntas e Avaliações
│       ├── querysets.py      # Filtros otimizados de banco de dados
│       ├── services.py       # Algoritmos de cálculo de médias, resumos e anonimato
│       ├── urls.py           # Rotas de avaliação do aluno e moderação de ciclos
│       └── views.py          # Controladores de submissão e publicação de resultados
│
├── static/                   # Recursos Estáticos
│   ├── css/
│   │   └── app.css           # Folha de estilos compilada do Design System
│   ├── img/                  # Logotipos, símbolos e ilustrações institucionais
│   └── js/
│       └── messages.js       # Comportamento de mensagens e alerts
│
├── templates/                # Templates HTML (Django Template Engine)
│   ├── base.html             # Layout mestre com metadados e imports
│   ├── landing.html          # Página institucional de apresentação da Trilha
│   ├── anonimato.html        # Página pública explicativa sobre as garantias de anonimato
│   ├── 403.html / 404.html / 500.html # Telas de tratamento de exceções HTTP
│   ├── componentes/          # Blocos reutilizáveis (campos, topbars, ações da conta)
│   ├── contas/               # Telas de login, cadastro inicial e troca de senha
│   ├── coordenacao/          # Telas operacionais da coordenação escolar
│   ├── aluno/                # Telas de dashboard e preenchimento de questionário
│   └── professor/            # Dashboard pedagógico com médias e murais
│
├── tests/                    # Suíte Completa de Testes Automatizados
│   ├── test_anonimato.py     # Validações matemáticas e estruturais de anonimato
│   ├── test_aplicar_rls.py   # Testes de segurança em nível de linha no PostgreSQL
│   ├── test_avaliacoes.py    # Testes dos ciclos, perguntas e submissões
│   ├── test_contas.py        # Testes de autenticação, roles e bloqueios
│   ├── test_escolas.py       # Testes de gestão pedagógica e sementes (seed)
│   ├── test_landing.py       # Testes de rotas públicas
│   └── test_migracoes.py     # Integridade estrutural do esquema do banco
│
└── docs/                     # Documentação de Arquitetura e Engenharia
    ├── ANONIMATO.md          # Especificação formal do modelo de privacidade
    ├── Contexto Fixo.md      # Regras canônicas de negócio do projeto
    ├── DEPLOY.md             # Instruções de implantação em servidores de produção
    ├── Design Fixo.md        # Diretrizes do Design System
    └── INSTALACAO.md         # Guia de configuração de ambiente de desenvolvimento
```

---

## 4. Descrição dos Modelos, Tabelas e Relacionamentos

O esquema de dados público do PostgreSQL (`public`) é composto por exatamente **25 tabelas**, distribuídas entre tabelas de domínio do projeto e tabelas nativas de infraestrutura do Django:

```
+-------------------------------------------------------------------------------------------------+
|                                 MAPA DE RELACIONAMENTOS (ERD)                                   |
+-------------------------------------------------------------------------------------------------+
|                                                                                                 |
|   +-------------------+          +-------------------+          +-------------------+           |
|   |   escolas_escola  | 1 ---- * |   contas_usuario  | 1 ---- * | escolas_matricula |           |
|   +-------------------+          +-------------------+          +-------------------+           |
|     |         |                    | (Professor)                  | (Aluno)                     |
|     |         |                    |                              |                             |
|     |         |                  1 |                              |                             |
|     |         |                    *                              *                             |
|     |         |              +---------------------------------------+                          |
|     |         +------------* |            escolas_vinculo            |                          |
|     |                        +---------------------------------------+                          |
|     |                          *                    *                                           |
|     | (Turma / Disciplina)     |                    |                                           |
|     *                          |                    |                                           |
|   +-------------------+        |                    |                                           |
|   | escolas_turma /   | 1 -----+                    |                                           |
|   | escolas_disciplina|                             |                                           |
|   +-------------------+                             |                                           |
|     |                                               |                                           |
|     * (Escola)                                      |                                           |
|   +-------------------------------+                 |                                           |
|   | avaliacoes_modeloquestionario | 1               |                                           |
|   +-------------------------------+   \             |                                           |
|     |                                  \            |                                           |
|     | 1                                 *           |                                           |
|     *                                 +---------------------------+                             |
|   +-------------------------------+   | avaliacoes_cicloavaliacao | 1                           |
|   |   avaliacoes_perguntamodelo   |   +---------------------------+   \                         |
|   +-------------------------------+     | 1                            \                        |
|                                         |                               *                       |
|                                         *                             +----------------------+  |
|                                       +---------------------+         | avaliacoes_resumo    |  |
|                                       | avaliacoes_pergunta | 1       | _vinculo             |  |
|                                       +---------------------+   \     +----------------------+  |
|                                                                  \                              |
|   +-----------------------------------------------------------+   *                             |
|   | [DESACOPLAMENTO DE ANONIMATO]                             |  +--------------------+         |
|   |                                                           |  | avaliacoes_resposta|         |
|   | contas_usuario (Aluno) + escolas_vinculo + Ciclo          |  | _escala / _texto / |         |
|   |   --> Registra apenas: [ avaliacoes_participacao ]        |  | _escolhaunica      |         |
|   |                                                           |  +--------------------+         |
|   | Respostas reais salvas sem aluno:                         |    *                            |
|   |   --> [ avaliacoes_avaliacao ] (UUID) <------------------------+                            |
|   +-----------------------------------------------------------+                                 |
+-------------------------------------------------------------------------------------------------+
```

### 4.1 Tabelas de Domínio Escolar (`apps.escolas`)

#### 1. `escolas_escola`
Representa a instituição de ensino (tenant da aplicação).
- `id` (bigint, PK): Identificador único da escola.
- `nome` (varchar(180)): Nome oficial da escola.
- `limiar_minimo` (smallint): Número mínimo de avaliações exigidas para exibição de métricas (default: 5).

#### 2. `escolas_turma`
Turmas pertencentes a uma determinada escola em um ano letivo específico.
- `id` (bigint, PK): Identificador da turma.
- `escola_id` (bigint, FK `escolas_escola.id`): Escola proprietária.
- `nome` (varchar(80)): Nome da turma (ex: "6º ano A").
- `ano_letivo` (smallint): Ano letivo correspondente (ex: 2026).
- *Restrição:* Unicidade conjunta de `(escola_id, nome, ano_letivo)`.

#### 3. `escolas_disciplina`
Disciplinas da grade curricular cadastradas pela instituição.
- `id` (bigint, PK): Identificador da disciplina.
- `escola_id` (bigint, FK `escolas_escola.id`): Escola proprietária.
- `nome` (varchar(120)): Nome da matéria (ex: "Matemática").
- *Restrição:* Unicidade conjunta de `(escola_id, nome)`.

#### 4. `escolas_vinculo`
Associação pedagógica tripartite entre Professor, Turma e Disciplina.
- `id` (bigint, PK): Identificador do vínculo pedagógico.
- `professor_id` (bigint, FK `contas_usuario.id`): Docente responsável pela aula.
- `turma_id` (bigint, FK `escolas_turma.id`): Turma atendida.
- `disciplina_id` (bigint, FK `escolas_disciplina.id`): Conteúdo curricular ministrado.
- *Restrição:* Unicidade conjunta de `(professor_id, turma_id, disciplina_id)`.

#### 5. `escolas_matricula`
Relação de pertencimento entre um estudante e uma turma.
- `id` (bigint, PK): Identificador da matrícula.
- `aluno_id` (bigint, FK `contas_usuario.id`): Estudante matriculado.
- `turma_id` (bigint, FK `escolas_turma.id`): Turma em que o aluno estuda.
- *Restrição:* Unicidade conjunta de `(aluno_id, turma_id)`.

---

### 4.2 Tabelas de Usuários e Autenticação (`apps.contas`)

#### 6. `contas_usuario`
Entidade customizada de usuário para autenticação universal.
- `id` (bigint, PK): Identificador do usuário.
- `email` (varchar(254), UNIQUE): Chave de autenticação no login.
- `password` (varchar(128)): Hash criptográfico da senha (PBKDF2/SHA256).
- `nome` (varchar(150)): Nome de exibição da pessoa.
- `role` (varchar(20)): Papel de acesso (`COORDENACAO`, `PROFESSOR`, `ALUNO`).
- `escola_id` (bigint, FK `escolas_escola.id`, NULL para administradores globais).
- `precisa_trocar_senha` (boolean): Flag de troca obrigatória de senha no 1º acesso.
- `senha_provisoria` (varchar(128)): Senha provisória gerada pelo sistema (limpa após a primeira troca).
- `is_active` (boolean): Flag de controle de acesso ativo/desativado.
- `is_staff` / `is_superuser`: Permissões administrativas do Django.
- `last_login` / `date_joined`: Registros de sessão institucional.

#### 7. `contas_usuario_groups`
Tabela associativa gerada pelo Django para agrupamentos de permissões do usuário.
- `id` (bigint, PK)
- `usuario_id` (bigint, FK `contas_usuario.id`)
- `group_id` (integer, FK `auth_group.id`)

#### 8. `contas_usuario_user_permissions`
Tabela associativa de permissões granulares atribuídas diretamente ao usuário.
- `id` (bigint, PK)
- `usuario_id` (bigint, FK `contas_usuario.id`)
- `permission_id` (integer, FK `auth_permission.id`)

---

### 4.3 Tabelas de Modelagem e Escuta Pedagógica (`apps.avaliacoes`)

#### 9. `avaliacoes_modeloquestionario`
Modelos de questionários configuráveis para as escolas.
- `id` (bigint, PK): Identificador do modelo.
- `escola_id` (bigint, FK `escolas_escola.id`): Escola mantenedora.
- `nome` (varchar(180)): Título do questionário.
- `descricao` (text): Orientações gerais aos respondentes.
- `ativo` (boolean): Indica se pode ser usado em novos ciclos.
- `padrao` (boolean): Marca o questionário padrão imutável da Trilha.

#### 10. `avaliacoes_perguntamodelo`
Perguntas pertencentes a um modelo de questionário.
- `id` (bigint, PK): Identificador da pergunta do modelo.
- `modelo_id` (bigint, FK `avaliacoes_modeloquestionario.id`).
- `texto` (text): Enunciado (validado contra perguntas que solicitem dados sensíveis).
- `tipo` (varchar(15)): Tipo de resposta (`ESCALA_1_5`, `ESCOLHA_UNICA`, `TEXTO`).
- `dimensao` (varchar(80)): Dimensão avaliada (ex: clareza, escuta, ritmo).
- `ordem` (smallint): Sequência de exibição na tela.
- `obrigatoria` (boolean): Obrigatoriedade de preenchimento.
- `opcoes` (jsonb): Opções de múltipla escolha para tipo `ESCOLHA_UNICA`.

#### 11. `avaliacoes_cicloavaliacao`
Período formal em que a escuta pedagógica fica ativa para as turmas.
- `id` (bigint, PK): Identificador do ciclo.
- `escola_id` (bigint, FK `escolas_escola.id`).
- `nome` (varchar(180)): Denominação do ciclo (ex: "Ciclo 2026.1").
- `status` (varchar(10)): Estado atual (`ABERTO`, `FECHADO`, `PUBLICADO`).
- `modelo_questionario_id` (bigint, FK `avaliacoes_modeloquestionario.id`).
- *Restrição:* Não pode existir mais de um ciclo aberto/fechado simultaneamente na mesma escola.

#### 12. `avaliacoes_pergunta`
Perguntas congeladas e instanciadas para um ciclo específico.
- `id` (bigint, PK): Identificador da pergunta no ciclo.
- `ciclo_id` (bigint, FK `avaliacoes_cicloavaliacao.id`).
- `texto` (text): Conteúdo textual da pergunta.
- `tipo` (varchar(15)): `ESCALA_1_5`, `ESCOLHA_UNICA` ou `TEXTO`.
- `dimensao` (varchar(80)): Dimensão pedagógica associada.
- `ordem` (smallint): Ordem de exibição.
- `obrigatoria` (boolean): Obrigatoriedade.
- `opcoes` (jsonb): Opções pré-definidas.

#### 13. `avaliacoes_participacao`
Controle estrito de preenchimento para garantir que o estudante vote apenas uma vez por vínculo, **sem guardar qualquer relação com a resposta real**.
- `id` (bigint, PK)
- `aluno_id` (bigint, FK `contas_usuario.id`): Estudante que realizou a ação.
- `ciclo_id` (bigint, FK `avaliacoes_cicloavaliacao.id`): Ciclo correspondente.
- `vinculo_id` (bigint, FK `escolas_vinculo.id`): Aula avaliada.
- *Restrição:* Chave única `(aluno_id, ciclo_id, vinculo_id)`.

#### 14. `avaliacoes_avaliacao` (Entidade Anônima Desacoplada)
Armazena o container anônimo de respostas.
- `id` (uuid, PK): Gerado aleatoriamente via `uuid.uuid4()` sem timestamp sequencial.
- `ciclo_id` (bigint, FK `avaliacoes_cicloavaliacao.id`): Ciclo ao qual pertence.
- `vinculo_id` (bigint): Identificador numérico simples do vínculo pedagógico (desprovido de constraints que vinculem a usuários e sem campos de data/hora `created_at`).

#### 15. `avaliacoes_respostaescala`
Respostas quantitativas com notas de 1 a 5.
- `id` (bigint, PK)
- `avaliacao_id` (uuid, FK `avaliacoes_avaliacao.id`)
- `pergunta_id` (bigint, FK `avaliacoes_pergunta.id`)
- `valor` (smallint): Valor inteiro entre 1 e 5.

#### 16. `avaliacoes_respostaescolhaunica`
Respostas de seleção única categórica.
- `id` (bigint, PK)
- `avaliacao_id` (uuid, FK `avaliacoes_avaliacao.id`)
- `pergunta_id` (bigint, FK `avaliacoes_pergunta.id`)
- `opcao` (varchar(180)): Texto da opção selecionada.

#### 17. `avaliacoes_respostatexto`
Respostas qualitativas abertas submetidas pelos estudantes.
- `id` (bigint, PK)
- `avaliacao_id` (uuid, FK `avaliacoes_avaliacao.id`)
- `pergunta_id` (bigint, FK `avaliacoes_pergunta.id`)
- `texto` (text): Comentário redigido.
- `status_moderacao` (varchar(10)): Estado de moderação (`PENDENTE`, `APROVADO`, `REJEITADO`).

#### 18. `avaliacoes_resumovinculo`
Tabela agregada e calculada após a publicação do ciclo, servindo como base rápida para os relatórios dos professores.
- `id` (bigint, PK)
- `ciclo_id` (bigint, FK `avaliacoes_cicloavaliacao.id`)
- `vinculo_id` (bigint, FK `escolas_vinculo.id`)
- `n_avaliacoes` (integer): Quantidade total de avaliações processadas.
- `medias_por_dimensao` (jsonb): Mapa contendo as médias calculadas (ex: `{"clareza": 4.5, "ritmo": 3.8}`).
- `distribuicoes_por_pergunta` (jsonb): Contagens estatísticas de frequência por opção.

---

### 4.4 Tabelas do Sistema e Infraestrutura Django

#### 19. `auth_group`
Grupos de permissões do Django Auth.
- `id` (integer, PK)
- `nome` (varchar(150), UNIQUE)

#### 20. `auth_permission`
Catálogo de permissões de modelos gerado dinamicamente pelo Django.
- `id` (integer, PK)
- `name` (varchar(255))
- `content_type_id` (integer, FK `django_content_type.id`)
- `codename` (varchar(100))

#### 21. `auth_group_permissions`
Relacionamento muitos-para-muitos entre grupos e permissões.
- `id` (bigint, PK)
- `group_id` (integer, FK `auth_group.id`)
- `permission_id` (integer, FK `auth_permission.id`)

#### 22. `django_content_type`
Registro interno de metadados dos modelos de dados das aplicações instaladas.
- `id` (integer, PK)
- `app_label` (varchar(100))
- `model` (varchar(100))

#### 23. `django_migrations`
Histórico de versões e migrações executadas no banco de dados.
- `id` (bigint, PK)
- `app` (varchar(255))
- `name` (varchar(255))
- `applied` (timestamp with time zone)

#### 24. `django_session`
Sessões ativas de navegação dos usuários logados.
- `session_key` (varchar(40), PK)
- `session_data` (text)
- `expire_date` (timestamp with time zone)

#### 25. `django_admin_log`
Trilha de auditoria das ações efetuadas através do painel Django Admin.
- `id` (integer, PK)
- `action_time` (timestamp with time zone)
- `user_id` (bigint, FK `contas_usuario.id`)
- `content_type_id` (integer, FK `django_content_type.id`, NULL)
- `object_id` (text, NULL)
- `object_repr` (varchar(200))
- `action_flag` (smallint)
- `change_message` (text)

---

## 5. Descrição dos Principais Módulos e Recursos Implementados

### 5.1 Mecanismo de Troca Obrigatória de Senha
- **Middleware `TrocaObrigatoriaSenhaMiddleware`:** Injetado na pipeline HTTP logo após a autenticação. Avalia se `request.user.precisa_trocar_senha == True`. Caso positivo, força o redirecionamento imediato para `trocar_senha`, impedindo que usuários com senhas provisórias acessem dados pedagógicos.
- **Serviço de Troca:** Ao salvar a nova senha definitiva, o sistema remove a flag `precisa_trocar_senha`, zera o campo `senha_provisoria` e renova a sessão com `update_session_auth_hash` para manter a navegação contínua sem deslogar o usuário.

### 5.2 Arquitetura de Anonimato Matemático e Atômico
- A função de registro de avaliação opera com transações ACID (`transaction.atomic()`):
  1. Cria o registro de `Participacao` associado ao `aluno` e `vinculo`.
  2. Cria a entidade anônima `Avaliacao` identificada por UUID randômico, contendo apenas o ID numérico do vínculo e sem qualquer menção ao aluno.
  3. Grava as respostas individuais (`RespostaEscala`, `RespostaTexto`, etc.) vinculadas apenas ao UUID anônimo.
  4. Nenhuma coluna de data/hora (`created_at`, `timestamp`) é armazenada nessas tabelas para impedir correlação temporal com logs de rede.

### 5.3 Agregação, Limiar e Publicação de Resultados
- **Limiar Mínimo:** Durante a geração de resumos (`gerar_resumos`), o sistema calcula `n_avaliacoes = Avaliacao.objects.filter(ciclo=ciclo, vinculo=vinculo_id).count()`. Se `n_avaliacoes < ciclo.escola.limiar_minimo`, nenhum resumo é gerado e o professor não visualiza parciais daquela turma.
- **Moderação de Conteúdo:** O ciclo só transiciona para o estado `PUBLICADO` se não houver nenhuma resposta de texto com status `PENDENTE`. Comentários rejeitados são descartados dos murais.
- **Ordem Aleatória de Exibição:** Nos relatórios de professores, comentários textuais aprovados são selecionados utilizando `.order_by("?")` para que a ordem dos textos mude a cada carregamento, impedindo que se deduza a autoria pelo momento em que o aluno entregou a avaliação.

---

## 6. Passo a Passo para Configurar e Executar o Projeto

### Pré-requisitos
- **Python 3.12** instalado no sistema operacional.
- **Git** instalado.
- Conexão com a Internet (para sincronização com banco PostgreSQL Supabase ou execução local).

### Passo 1: Clonar o Repositório
```bash
git clone https://github.com/eduroqu3/Trilha.git
cd Trilha
git checkout CodeFreeze
```

### Passo 2: Criar e Ativar o Ambiente Virtual
- **No Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
- **No Linux / macOS (Bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Passo 3: Instalar as Dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Passo 4: Configurar as Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto baseado no `.env.example`:
```dotenv
DEBUG=True
ALLOW_SEED_DEMO=True
SECRET_KEY=sua-chave-secreta-de-desenvolvimento-aqui
DATABASE_URL=postgresql://usuario:senha@host:5432/postgres?sslmode=require
ALLOWED_HOSTS=localhost,127.0.0.1,testserver
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
PUBLIC_HTTPS=False
TRUST_PROXY_SSL_HEADER=False
```

### Passo 5: Executar Migrações do Banco de Dados
```bash
python manage.py migrate
```

### Passo 6: Popular o Banco de Dados com Dados de Teste (Seed)
Para limpar os dados legados e criar o cenário de demonstração com senha unificada:
```bash
python manage.py seed_demo --limpar
```
*(Senha padrão criada para todos os perfis: `Trilha@2026`).*

### Passo 7: Iniciar o Servidor de Desenvolvimento
```bash
python manage.py runserver 127.0.0.1:8000
```
O sistema estará acessível em: `http://127.0.0.1:8000/`

---

## 7. Bibliotecas e Pacotes Necessários

O arquivo `requirements.txt` é mantido estritamente enxuto, sem dependências redundantes:

| Pacote | Versão | Finalidade |
| :--- | :--- | :--- |
| **Django** | `5.2.19` | Framework web principal (ORM, Templates, Auth, Middleware). |
| **django-environ** | `0.14.0` | Parsing e gestão segura de configurações via arquivo `.env`. |
| **psycopg[binary]** | `3.3.8` | Driver moderno e assíncrono para comunicação com PostgreSQL. |
| **whitenoise** | `6.12.0` | Servir arquivos estáticos otimizados sem necessidade de Nginx local. |
| **gunicorn** | `27.0.0` | Servidor HTTP WSGI padrão da indústria para ambientes de produção. |
| **pytest** | `9.2.0` | Framework avançado de testes unitários e de integração. |
| **pytest-django** | `4.14.0` | Extensões e fixtures especializadas do Pytest para Django. |
| **ruff** | `0.17.4` | Linter e formatador ultrarrápido para garantia de conformidade com PEP 8. |

---

## 8. Descrição dos Testes Executados e Resultados Obtidos

A suíte de testes do projeto conta com cobertura completa sobre as regras de negócio, limites de segurança e integridade transacional.

### 8.1 Categorias de Testes
1. **Anonimato e Isolamento (`tests/test_anonimato.py`):**
   - Garante que respostas não possuem FK de usuário.
   - Garante a ausência de colunas de timestamp em tabelas de resposta.
   - Valida que a ordem dos comentários é aleatorizada.
   - Valida que perguntas não aceitam termos sensíveis (CPF, raça, endereço).
2. **Ciclos e Avaliações (`tests/test_avaliacoes.py`):**
   - Valida cálculo exato de médias por dimensão e distribuição de escolhas.
   - Enforça que ciclos fechados travam edição de perguntas.
   - Garante bloqueio de publicação caso existam comentários pendentes de moderação.
3. **Contas e Permissões (`tests/test_contas.py`):**
   - Valida que usuários com flag de troca de senha são interceptados pelo middleware.
   - Assegura que desativar um usuário impede seu login subsequente.
   - Assegura que desativar um aluno **não remove** suas participações históricas.
   - Valida isolamento multi-tenant (coordenação só gerencia usuários da própria escola).
4. **Escolas e Vínculos (`tests/test_escolas.py`):**
   - Teste de importação de arquivos CSV com detecção de duplicidades.
   - Criação conjunta de turmas e disciplinas.
   - Teste de isolamento de segurança para execução do comando `seed_demo`.
5. **Políticas de Banco e Migrações (`tests/test_aplicar_rls.py`, `tests/test_migracoes.py`):**
   - Validação da aplicação de políticas Row Level Security (RLS) no PostgreSQL.
   - Verificação de consistência e ausência de migrações pendentes.

### 8.2 Relatório de Execução (Pytest)
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
django: version: 5.2.19, settings: config.settings
rootdir: C:\dev\projects\Trilha
configfile: pytest.ini
plugins: django-4.14.0

tests/test_anonimato.py ............                                     [ 14%]
tests/test_avaliacoes.py ...................                             [ 36%]
tests/test_contas.py ................................                    [ 74%]
tests/test_escolas.py ................                                   [ 93%]
tests/test_aplicar_rls.py ..                                             [ 95%]
tests/test_landing.py ..                                                 [ 98%]
tests/test_migracoes.py ..                                               [100%]

============================= 84 passed in 133.5s =============================
Status do Ruff: All checks passed! (0 erros de linting)
```

---

## 9. Endereços do Projeto e Ambientes

- **Repositório GitHub (Código-Fonte):** [https://github.com/eduroqu3/Trilha.git](https://github.com/eduroqu3/Trilha.git)
  - **Branch Ativa e Homologada:** `CodeFreeze`
- **Ambiente de Produção (Deploy Render):** [https://trilhadjango.onrender.com](https://trilhadjango.onrender.com)
- **Banco de Dados em Produção:** PostgreSQL Gerenciado (Supabase) via Pooler de Conexão Segura (SSL Mode Require)

---

## 10. Conclusão e Homologação

O sistema **Trilha** encontra-se em estado estável de congelamento de código (**CodeFreeze**), com 100% dos testes unitários e de integração aprovados (84 testes), conformidade total de tipagem e estilo PEP 8 pelo linter Ruff, banco de dados Supabase populado e arquitetura de anonimato plenamente resguardada tanto em nível de aplicação quanto em nível de banco de dados (Row Level Security).

- **Instituição:** SENAI
- **Orientação:** Prof. Jhonny Braga
- **Autores:** Eduardo Vieira Roque, Gustavo Costa Trindade, Guilherme Vilares, Aron Maesta, Diogo Ferrata.
