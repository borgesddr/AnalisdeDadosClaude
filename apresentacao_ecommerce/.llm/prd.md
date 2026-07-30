## Análise completa

O objetivo desse projeto é fazer uma análise completa usando os dados da 
pasta C:\Projetos\jd_claude\AnalisedeDados_Claude\apresentacao_ecommerce\data. São dados de ecommerce. Eu quero criar os 
resultados finais dessa análise em html.

Mas não quero jogar todos os dados de uma vez só no LLM. Quero que identifique as 
joins entre as tabelas, veja os calculos de KPIs necessários, e gere 
arquivos menores com os KPIs calculados. Assim eu consigo aumentar o 
tamanho do contexto e fazer uma análise mais profunda.

## Design (identidade visual Keyrus)

Referência extraída de prints do site institucional (keyrus.com/br/pt/home).

### Cores

- **Fundo principal:** branco (`#FFFFFF`)
- **Barra superior (topbar):** azul-marinho escuro (`#0B2265` a `#0A1F5C`)
- **Azul/ciano de destaque (links ativos, botões, "com IA"):** `#29ABE2` a `#38BDF8`
- **Laranja de destaque (formas geométricas, botão flutuante):** `#F5A623` a `#F7941D`
- **Logo "keyrus" (multicolorida por letra):**
  - k: ciano (`#29ABE2`)
  - e: laranja (`#F5A623`)
  - y: magenta/rosa (`#EC4899` aprox.)
  - r: vermelho (`#E63946` aprox.)
  - u, s: preto (`#111111`)
- **Texto de título:** preto/quase-preto (`#111111` a `#1A1A1A`)
- **Texto de corpo:** cinza escuro (`#333333` a `#4A4A4A`)
- **Botões primários (pill/rounded):** fundo ciano (`#38BDF8`), texto branco
- **Botões secundários (outline):** borda ciano, texto ciano, fundo branco
- **Linhas divisórias / bordas sutis:** cinza claro (`#E0E0E0`)
- **Gradiente logo "Ai" (do material institucional):** ciano→azul (`#00D4FF` → `#2979FF`) e vermelho→laranja (`#E63946` → `#F2994A`)

### Tipografia

- **Logo:** sans-serif geométrica minúscula, sem serifa, traços uniformes
- **Títulos (H1/H2):** sans-serif geométrica, peso bold/extra-bold, levemente arredondada (estilo Poppins Bold ou similar)
- **Corpo de texto:** mesma família, peso regular, boa altura de linha (confortável para leitura, ~1.5-1.6)
- **Botões:** peso bold/semibold, texto curto e direto ("Saiba mais aqui!", "Contate-nos")
- **Navegação (menu superior):** peso medium, tamanho menor que os títulos

### Espaçamento e layout

- Header fixo com duas camadas: topbar estreita (aviso/CTA) + navbar principal com logo e menu
- Bastante whitespace geral, respiro generoso entre blocos
- Barras decorativas verticais coloridas nas laterais (ciano à esquerda, formas geométricas laranja à direita) como elementos de moldura
- Cards com cantos arredondados (raio grande, ~16-24px) e sombra suave
- Botões em formato "pill" (cantos totalmente arredondados)
- Estrutura hero em duas colunas: texto à esquerda, card/imagem à direita
- Indicadores de carrossel (dots) centralizados abaixo do card
- Ícones/badges circulares pequenos usados como marcadores de destaque
- Botão flutuante circular no canto inferior esquerdo (ex: acessibilidade/cookie)

### Observação

Cores e fontes estimadas visualmente a partir dos prints. Para hex exatos e nome real da fonte, o ideal seria inspecionar o CSS do site diretamente (DevTools → Computed Style).