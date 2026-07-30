# Seção Pricing & Margem

Painel de **posicionamento competitivo de preços**: compara `produtos.preco_atual`
com os preços coletados dos concorrentes em `preco_competidores`.

## Fontes de dados

| Tabela | Colunas usadas | Linhas |
|---|---|---|
| `produtos` | `id_produto`, `nome_produto`, `categoria`, `marca`, `preco_atual` | 215 |
| `preco_competidores` | `id_produto`, `nome_concorrente`, `preco_concorrente` | 728 |

Cobertura validada via MCP (SELECT): 215/215 produtos têm ao menos 1 preço de
concorrente; 4 concorrentes (`Shopee`, `Amazon`, `Magalu`, `Mercado Livre`);
a maioria dos produtos tem 3–4 concorrentes.

> **Nota sobre tempo:** todas as coletas de `preco_competidores` são de um único
> dia (11/jan/2026). Por isso **não há série temporal de gap** — a análise é um
> retrato competitivo (snapshot), e o painel foca posicionamento, não evolução.

Todo o fetch passa pelo cliente compartilhado `src/lib/supabase.ts`. As duas
tabelas são carregadas com dois `SELECT` simples e as agregações são feitas em
JS no hook `hooks/usePricing.ts` (volume pequeno, ~950 linhas no total).

## KPIs e fórmulas

Notação: para cada produto `p`, `preco = preco_atual`;
`avg_comp(p) = média(preco_concorrente)`; `min_comp(p) = menor preco_concorrente`.

| KPI | Fórmula | Valor atual |
|---|---|---|
| **Gap médio vs mercado** | `média_p( (preco − avg_comp) / avg_comp )` | **+7,4%** |
| **Produtos acima do mercado** | `#{ p : preco > avg_comp } / N` | **59,1%** (127/215) |
| **Líderes de preço** | `#{ p : preco ≤ min_comp }` | **25** (11,6%) |
| **Categoria em alerta** | categoria com maior gap médio | **Tênis (+100%)** |

### KPIs de detalhe (nos gráficos)

- **Gap médio por categoria** = `média_p∈cat( (preco − avg_comp)/avg_comp )`.
  Verde quando negativo (somos mais baratos = bom para o negócio), vermelho quando
  positivo — conforme a regra de sinal do `DESIGN_SYSTEM.md` (para pricing, preço
  menor que o concorrente é `success`).
- **Paridade de preços** (scatter) = ponto `(avg_comp, preco)` por produto; a linha
  tracejada é a paridade `y = x`. Pontos acima = mais caros que o mercado.
- **Posição frente a cada concorrente** = por concorrente `c`, contagem de
  comparações produto-a-produto em que `preco > preco_concorrente` (mais caros) vs
  `preco < preco_concorrente` (mais baratos).
- **Sobrepreço vs menor concorrente** (ranking de risco) =
  `(preco − min_comp) / min_comp` para produtos com `preco > min_comp`, ordenado
  desc. (top 10). São os candidatos prioritários a reprecificação.

## História que o painel conta

1. **Resumo executivo** (KPIs): estamos ~7% acima do mercado, com maioria dos
   produtos mais caros que a média.
2. **Ofensor único**: a categoria **Tênis** está sistematicamente a ~2x o preço
   dos concorrentes (gap de +100% em todos os 15 SKUs) — distorce a média geral.
3. **Fora de Tênis**, o portfólio fica muito próximo da paridade (demais categorias
   entre −0,3% e +1,2%).
4. **Onde perdemos**: contra os 4 marketplaces perdemos em pouco mais da metade das
   comparações; Magalu/Shopee são onde estamos mais caros.
5. **Ação**: o ranking de risco lista os produtos a reprecificar primeiro
   (liderado pelos tênis).

## Arquivos

```
src/sections/pricing/
  index.tsx                              # orquestra KPIs + narrativa + 4 gráficos
  README.md
  hooks/
    usePricing.ts                        # fetch das 2 tabelas + agregações em JS
  components/
    KpiCard.tsx                          # card de KPI (título/valor/hint/tom)
    ChartCard.tsx                        # wrapper de card de gráfico
    CategoryPositioningChart.tsx         # barra horizontal: gap % por categoria
    PriceParityScatter.tsx               # scatter preço x média concorrentes
    CompetitorPositionChart.tsx          # barra empilhada: caros vs baratos por concorrente
    RiskRankingChart.tsx                 # barra horizontal: top 10 sobrepreço
```
