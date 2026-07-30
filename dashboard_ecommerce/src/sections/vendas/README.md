# Seção Vendas & Receita

Painel do domínio comercial. Fonte única: tabela `vendas` (3000 linhas, 13/dez/2025
a 11/jan/2026) com join em `produtos` (`categoria`, `nome_produto`). Todo o acesso é
via o cliente compartilhado `src/lib/supabase.ts` (SELECT/RLS anon). A busca é feita
uma vez em `hooks/useVendas.ts` (paginação de 1000 linhas via `.range`) e a agregação
acontece no cliente com `useMemo`.

Convenção de "receita": em todos os KPIs, **receita = `quantidade * preco_unitario`**
somado nas linhas do escopo.

## KPIs

| KPI | Fórmula | Valor validado |
|---|---|---|
| Receita total | `SUM(quantidade * preco_unitario)` | R$ 969.837,27 |
| Ticket médio | `receita_total / COUNT(vendas)` | R$ 323,28 |
| Total de vendas | `COUNT(*)` | 3.000 |
| Itens vendidos | `SUM(quantidade)` | 4.297 |
| Clientes ativos | `COUNT(DISTINCT id_cliente)` | 50 |
| Receita e-commerce (%) | `receita(ecommerce) / receita_total` | 72,5% |
| Categoria líder | `argmax_categoria SUM(receita)` | Moda (R$ 248.124 · 25,6%) |

## Visualizações (a história)

1. **Cards-resumo** — visão de topo (receita, ticket, volume, clientes, mix de canal).
2. **Evolução diária da receita** (área) — tendência no tempo; faturamento estável em
   torno de ~R$ 32k/dia.
3. **Receita por canal** (donut + ticket médio) — e-commerce = 72,5% da receita e
   ticket médio maior (R$ 327,95 vs R$ 311,57 da loja física).
4. **Receita por categoria** (barras horizontais) — Moda lidera, seguida de Áudio e
   Acessórios.
5. **Top 5 produtos por receita** (barras de progresso) — concentração em poucos SKUs
   (Fone de Ouvido Esportivo, Camisa Social ...).

## Queries de referência (validação via MCP Supabase)

```sql
-- Totais
SELECT COUNT(*), SUM(quantidade*preco_unitario) AS receita,
       SUM(quantidade*preco_unitario)/COUNT(*) AS ticket_medio,
       SUM(quantidade) AS itens, COUNT(DISTINCT id_cliente) AS clientes
FROM vendas;

-- Por canal
SELECT canal_venda, COUNT(*), SUM(quantidade*preco_unitario) AS receita,
       SUM(quantidade*preco_unitario)/COUNT(*) AS ticket_medio
FROM vendas GROUP BY canal_venda;

-- Receita por categoria
SELECT p.categoria, SUM(v.quantidade*v.preco_unitario) AS receita
FROM vendas v JOIN produtos p ON p.id_produto = v.id_produto
GROUP BY p.categoria ORDER BY receita DESC;

-- Top produtos
SELECT p.nome_produto, SUM(v.quantidade*v.preco_unitario) AS receita
FROM vendas v JOIN produtos p ON p.id_produto = v.id_produto
GROUP BY p.nome_produto ORDER BY receita DESC LIMIT 5;

-- Evolução diária
SELECT date_trunc('day', data_venda)::date AS dia,
       SUM(quantidade*preco_unitario) AS receita
FROM vendas GROUP BY 1 ORDER BY 1;
```

## Arquivos

- `index.tsx` — composição da seção, narrativa e estados loading/error.
- `hooks/useVendas.ts` — fetch paginado + agregação (KPIs, série diária, rankings).
- `components/` — `KpiCard`, `ChartCard`, `RevenueTrendChart`, `ChannelComparison`,
  `CategoryRanking`, `TopProducts`.
