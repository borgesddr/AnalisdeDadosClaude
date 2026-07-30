# Design System — Dashboard E-commerce Keyrus

Guia prático para os agentes que constroem as seções. Todos os tokens abaixo já
estão espelhados em `tailwind.config.js` — **use as classes Tailwind, não hex cru**.

## 1. Domínios de dados

| Domínio | Tabelas | Seção / pasta |
|---|---|---|
| Vendas & Receita | `vendas` (+ join `produtos`, `clientes`) | `src/sections/vendas` |
| Pricing & Margem | `produtos`, `preco_competidores` | `src/sections/pricing` |
| Clientes & Comportamento | `clientes`, `vendas` | `src/sections/clientes` |

Fatos do dataset (validados): 3000 vendas de 13/dez/2025 a 11/jan/2026, receita
~R$969.837; 2 canais (`ecommerce`, `loja_fisica`); 11 categorias de produto;
22 estados; 4 concorrentes em `preco_competidores`.

## 2. Paleta de cores

### Marca (base Keyrus)
| Token Tailwind | Hex | Uso |
|---|---|---|
| `brand-navy` | `#0B2265` | Topbar, headers, texto de título forte |
| `brand-navy-800` | `#0A1F5C` | Hover/variação escura da navy |
| `brand-cyan` | `#29ABE2` | Cor primária de ação, links ativos |
| `brand-cyan-400` | `#38BDF8` | Destaque claro, hover de botões |
| `brand-orange` | `#F5A623` | Destaque/CTA secundário, séries de ênfase |

### Neutros (UI)
| Token | Hex | Uso |
|---|---|---|
| `bg` | `#F7F8FA` | Fundo da aplicação |
| `surface` | `#FFFFFF` | Cards, painéis |
| `border` | `#E4E7EC` | Bordas sutis, divisórias |
| `text` | `#1A1A1A` | Título/valor de KPI |
| `text-muted` | `#667085` | Legendas, labels, eixos |

### Cores semânticas (para métricas e gráficos)
| Token | Hex | Significado |
|---|---|---|
| `success` | `#16A34A` | Crescimento, positivo, "estamos mais baratos" |
| `warning` | `#F5A623` | Atenção, meta em risco |
| `danger` | `#DC2626` | Queda, negativo, "estamos mais caros" |
| `neutral` | `#94A3B8` | Séries de referência/baseline |

Regra de sinal: **verde = bom para o negócio, vermelho = ruim** — cuidado com
pricing (preço menor que o concorrente é `success`, não `danger`).

### Paleta categórica (11 categorias de produto)
Ordem fixa — use sempre o mesmo índice para a mesma categoria em todas as seções,
exportada em `src/lib/theme.ts` como `CATEGORY_COLORS`:

```
Casa         #0B2265   Acessórios   #29ABE2   Moda        #38BDF8
Informática  #16A34A   Cozinha      #F5A623   Esporte     #DC2626
Games        #7C3AED   Áudio        #EC4899   Tênis       #0EA5A4
Eletrônicos  #F97316   Beleza       #64748B
```

Canais: `ecommerce` = `brand-cyan` (#29ABE2), `loja_fisica` = `brand-navy` (#0B2265).

## 3. Tipografia

- Fonte: **Inter** (fallback system-ui/sans-serif). Carregada via `@fontsource`? Não
  — para SPA estática usamos `font-family` do sistema + Inter se disponível. Sem CDN.
- Pesos: 400 (corpo), 500 (labels), 600 (títulos de card), 700 (KPI/valores).
- Escala:
  | Nível | Classe | Tamanho |
  |---|---|---|
  | Título de página | `text-2xl font-bold` | 24px |
  | Título de seção/card | `text-lg font-semibold` | 18px |
  | Valor de KPI | `text-3xl font-bold` | 30px |
  | Corpo | `text-sm` | 14px |
  | Label/eixo/legenda | `text-xs text-text-muted` | 12px |
- Altura de linha confortável (`leading-relaxed` em blocos de texto).

## 4. Espaçamento, grid e layout

- Escala base 4px (Tailwind default). Espaçamentos usuais: `gap-4`, `gap-6`, `p-6`.
- Grid de KPIs: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4`.
- Grid de gráficos: `grid grid-cols-1 lg:grid-cols-2 gap-6`.
- Container da seção: `max-w-7xl mx-auto px-4 sm:px-6 py-6`.
- Respiro generoso entre blocos (`space-y-6`).

## 5. Cards e componentes

- Card: `bg-surface rounded-2xl border border-border shadow-sm p-6`.
  (raio 16px = `rounded-2xl`, sombra suave.)
- KPI card: título em `text-xs text-text-muted uppercase tracking-wide`, valor em
  `text-3xl font-bold text-text`, delta em `success`/`danger` com seta.
- Botões primários: `bg-brand-cyan text-white rounded-full px-4 py-2 font-semibold`.
- Estados: sempre trate `loading` (skeleton/placeholder) e `error` (mensagem curta)
  nos componentes que buscam dados.

## 6. Gráficos — Recharts (biblioteca oficial)

Todos os gráficos usam **Recharts**. Diretrizes:

- Sempre com `<Tooltip>`, `<Legend>` (quando houver mais de 1 série) e eixos rotulados.
- Use `ResponsiveContainer` com `width="100%"` e altura fixa (ex: 300px).
- Cores sempre vindas dos tokens (`CATEGORY_COLORS`, semânticas), nunca hex aleatório.
- Formate valores monetários em pt-BR (`R$`) via helper `formatBRL` em `src/lib/format.ts`.
- **Proibido:** 3D, gráfico de pizza com mais de ~5 fatias (use barras para as 11
  categorias), eixos truncados que distorçam a leitura.
- Recomendado por caso: tendência temporal = linha/área; comparação categórica =
  barra; participação (poucas fatias) = pizza/donut; correlação = scatter.
- Grid sutil (`stroke` = `border`), sem bordas pesadas.
