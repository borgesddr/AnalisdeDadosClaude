# Seção — Clientes & Comportamento

Painel sobre **quem são, quanto valem e como compram** os clientes.
Fontes: tabelas `clientes` (50 linhas) e `vendas` (3000 linhas, FK `id_cliente`).
Período dos dados de venda: **13/dez/2025 a 11/jan/2026**.

Todo o acesso é somente leitura via cliente compartilhado `src/lib/supabase.ts`.
A agregação é feita no browser (hook `hooks/useClientes.ts`), que pagina `vendas`
em blocos de 1000 linhas (`.range`) por causa do limite padrão do PostgREST.

## KPIs

| KPI | Fórmula | Fonte | Valor (validado via MCP) |
|---|---|---|---|
| **Clientes ativos** | `count(distinct id_cliente em vendas)` sobre `count(*) em clientes` | `vendas`, `clientes` | 50 / 50 (100%) |
| **Receita média por cliente** | `receita_total / total_clientes`, onde `receita = Σ(quantidade × preco_unitario)` | `vendas` | R$ 19.396,75 |
| **Ticket médio** | média por cliente de `receita_cliente / nº_compras_cliente` | `vendas` | R$ 324,53 |
| **Frequência média** | `Σ nº_compras / total_clientes` (uma venda = uma compra) | `vendas` | 60 compras/cliente (mín 36, máx 81) |
| **Concentração Top 10** | `Σ receita dos 10 maiores / receita_total` | `vendas` | 27,0% |
| **Canal preferido** | por cliente, canal com maior `Σ receita`; contagem de clientes por canal | `vendas` | 49 e-commerce / 1 loja física |

## Gráficos

1. **Distribuição geográfica** — barra horizontal de receita por estado (UF).
   22 estados, todos no Brasil (`pais` único). Barra de maior receita destacada em navy.
2. **Top 10 clientes por receita** — barra horizontal; maior cliente destacado em laranja.
3. **Comportamento de compra** — scatter frequência (nº de compras) × ticket médio,
   tamanho do ponto = receita. Pontos acima da média nas duas dimensões em verde
   (clientes de alto valor: alta frequência e alto ticket).
4. **Mix de canal** — donut de receita por canal (`ecommerce` cyan, `loja_fisica` navy).
   E-commerce = R$ 703.445,79 (72,5%) vs loja física R$ 266.391,48 (27,5%).

## Narrativa / insight principal

A base é pequena, **100% ativa** e com receita **pouco concentrada** (Top 10 = 27%),
sinal de carteira saudável e distribuída. O **e-commerce domina** tanto em receita
(72,5%) quanto em preferência de canal (49 de 50 clientes).

## Queries de validação (MCP Supabase, SELECT)

```sql
-- Ativos, receita, cobertura geográfica
SELECT (SELECT count(*) FROM clientes) total_clientes,
       (SELECT count(DISTINCT id_cliente) FROM vendas) ativos,
       (SELECT sum(quantidade*preco_unitario) FROM vendas) receita_total,
       (SELECT count(DISTINCT estado) FROM clientes) estados;

-- Ticket, frequência, receita média por cliente
WITH c AS (SELECT id_cliente, sum(quantidade*preco_unitario) rec, count(*) n
           FROM vendas GROUP BY id_cliente)
SELECT avg(rec) receita_media, avg(rec/n) ticket_medio, avg(n) freq_media FROM c;

-- Concentração Top 10
WITH c AS (SELECT id_cliente, sum(quantidade*preco_unitario) rec FROM vendas GROUP BY 1),
     r AS (SELECT rec, row_number() OVER (ORDER BY rec DESC) rn FROM c)
SELECT sum(rec) FILTER (WHERE rn<=10) / sum(rec) share_top10 FROM r;

-- Mix de canal
SELECT canal_venda, sum(quantidade*preco_unitario) receita FROM vendas GROUP BY 1;
```
