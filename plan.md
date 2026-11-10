# Plano de implementação — TRILHA

## Escopo e abordagem

Construir uma landing page única, em português brasileiro, para apresentar a proposta TRILHA a estudantes, docentes e escolas. O briefing anexado é a referência de conteúdo e direção visual; a Blueprint aprovada confirma página estática e demonstrativa, sem banco de dados, APIs, busca funcional ou dados reais.

A aplicação será uma view Django 5 renderizada no servidor, com um template semântico e estáticos locais. O servidor usará Python 3.12 e a porta 3000. Tailwind CSS será carregado pelo Play CDN para manter o uso de classes utilitárias sem instalar Node; o CSS local complementará paleta, composição editorial, ilustrações e responsividade. JavaScript de negócio não será necessário: menu móvel e FAQ usarão elementos nativos acessíveis (`details`/`summary`). Não haverá DRF, JWT, React, TypeScript, banco de dados ou endpoints extras. Fontes Fraunces e Manrope serão carregadas do Google Fonts; ilustração original do hero será um asset da página.

## Arquitetura e estrutura

- `manage.py`: comandos Django.
- `trilha_site/settings.py`: configuração compacta, host liberado para Preview, templates e arquivos estáticos.
- `trilha_site/urls.py`: raiz da página e rota estática `/manus-routes.json` quando servida pela app.
- `trilha_site/views.py`: view simples da landing page, sem dependência de dados.
- `templates/landing.html`: header, hero, princípio, experiência do estudante, perfis demonstrativos, citação, escolas, percurso, FAQ, CTA e footer.
- `static/css/site.css`: tokens de cor, tipografia, motivos decorativos, ajustes responsivos e foco acessível.
- `static/images/trilha-hero.png`: ilustração editorial exclusiva do hero.
- `requirements.txt`: dependências Python fixadas na família Django 5.2.
- `manus-routes.json`: declaração da única rota HTML, `/`.

## Direção visual e verbal

**Design Movement:** editorial contemporâneo de educação, com referências de revistas independentes e papelaria ilustrada.

**Princípios centrais:** escuta sem julgamento; hierarquia tipográfica acolhedora; espaço e separadores delicados; exemplos sempre identificados como fictícios.

**Filosofia de cor:** creme e areia dão calor e leitura confortável; verde profundo representa confiança e progresso compartilhado; sálvia e verde pálido suavizam cartões e diagramas; mostarda destaca decisões e detalhes sem tom de alerta.

**Paradigma de layout:** narrativa editorial em faixas alternadas, usando pares descentrados de texto/demonstração no desktop e fluxo empilhado por ordem de leitura no mobile.

**Motivos de assinatura:** traços mostarda junto aos rótulos; sombras planas deslocadas; círculos/arcos que sugerem percurso e continuidade.

**Interação:** âncoras conduzem entre as seções reais; menu compacto e FAQ funcionam nativamente por teclado; a busca permanece uma demonstração não submetível e não simula resultados.

**Animação:** movimento mínimo; transições curtas de cor/sombra em links e botões, sem animação automática ou essencial para compreensão; respeitar `prefers-reduced-motion`.

**Sistema tipográfico:** Fraunces para títulos, números e citação; Manrope para navegação, corpo, botões e microtexto. Títulos fluidos em `clamp()`, entrelinha compacta e largura controlada.

**Essência:** uma proposta de escuta das experiências de aprendizagem para estudantes, docentes e escolas, transformando percepções contextualizadas em conversas pedagógicas; personalidade: acolhedora, cuidadosa, reflexiva.

**Voz:** clara, respeitosa e orientada a caminhos, não a julgamentos. Exemplos: “O contexto faz parte da conversa.” / “Uma nota é uma pergunta para aprofundar.”

**Marca:** wordmark serifado minúsculo “trilha”, acompanhado de um símbolo circular autoral formado por linhas/ramo em movimento; sem simular disponibilidade comercial.

**Cor de marca:** verde profundo `#216B58`.
