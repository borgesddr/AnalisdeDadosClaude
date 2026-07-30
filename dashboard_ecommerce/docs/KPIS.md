# KPIs por seção

Catálogo dos KPIs e fórmulas de cada seção do dashboard, consolidado a partir dos
`README.md` de cada pasta em `src/sections/<seção>/`. Convenção comum de receita:
**receita = `quantidade * preco_unitario`**.

## Vendas & Receita
Fonte: `vendas` (3.000 linhas, 13/dez/2025–11/jan/2026) + join `produtos`. Fetch
paginado (`.range`, lotes de 1000) em `hooks/useVendas.ts`; agregação no cliente.

| KPI | Fórmula | Valor validado |
|---|---|---|
| Receita total | `SUM(quantidade * preco_unitario)` | R$ 969.837,27 |
| Ticket médio | `receita_total / COUNT(vendas)` | R$ 323,28 |
| Total de vendas | `COUNT(*)` | 3.000 |
| Itens vendidos | `SUM(quantidade)` | 4.297 |
| Clientes ativos | `COUNT(DISTINCT id_cliente)` | 50 |
| Receita e-commerce (%) | `receita(ecommerce) / receita_total` | 72,5% |
| Categoria líder | `argmax_categoria SUM(receita)` | Moda (R$ 248.124 · 25,6%) |

Gráficos: evolução diária da receita (área), receita por canal (donut + ticket),
receita por categoria (barras), top 5 produtos.

## Pricing & Margem
Fontes: `produtos` (215) e `preco_competidores` (728, 4 concorrentes: Shopee, Amazon,
Magalu, Mercado Livre). Snapshot de um único dia (11/jan/2026) — sem série temporal.
Por produto `p`: `preco = preco_atual`, `avg_comp` = média e `min_comp` = menor
`preco_concorrente`.

| KPI | Fórmula | Valor atual |
|---|---|---|
| Gap médio vs mercado | `média_p( (preco − avg_comp) / avg_comp )` | +7,4% |
| Produtos acima do mercado | `#{ p : preco > avg_comp } / N` | 59,1% (127/215) |
| Líderes de preço | `#{ p : preco ≤ min_comp }` | 25 (11,6%) |
| Categoria em alerta | categoria com maior gap médio | Tênis (+100%) |

KPIs de detalhe: gap médio por categoria; paridade de preços (scatter `(avg_comp,
preco)` vs linha `y=x`); posição frente a cada concorrente (mais caros vs mais
baratos); sobrepreço vs menor concorrente `((preco − min_comp)/min_comp)` — ranking de
risco de reprecificação. **Regra de sinal (pricing):** preço menor que o concorrente é
`success` (verde), maior é `danger`.

## Clientes & Comportamento
Fontes: `clientes` (50) e `vendas` (3.000). Fetch paginado em `hooks/useClientes.ts`;
agregação no browser.

| KPI | Fórmula | Valor validado |
|---|---|---|
| Clientes ativos | `COUNT(DISTINCT id_cliente)` / total de `clientes` | 50 / 50 (100%) |
| Receita média por cliente | `receita_total / total_clientes` | R$ 19.396,75 |
| Ticket médio | média por cliente de `receita_cliente / nº_compras` | R$ 324,53 |
| Frequência média | `Σ nº_compras / total_clientes` | 60 compras/cliente (36–81) |
| Concentração Top 10 | `Σ receita dos 10 maiores / receita_total` | 27,0% |
| Canal preferido | por cliente, canal de maior `Σ receita` | 49 e-commerce / 1 loja física |

Gráficos: distribuição geográfica (receita por UF, 22 estados), top 10 clientes,
comportamento de compra (scatter frequência × ticket, tamanho = receita), mix de canal
(donut). Insight: carteira 100% ativa, pouco concentrada (Top 10 = 27%), e-commerce
dominante (72,5% da receita, 49/50 clientes).
