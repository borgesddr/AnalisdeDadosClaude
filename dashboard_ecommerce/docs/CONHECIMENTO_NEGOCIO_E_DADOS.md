# Conhecimento de Negócio e Dados — Dashboard E-commerce

Documento de referência consolidado para reuso em outros projetos. Reúne o modelo de
dados (Supabase/Postgres), as regras de negócio, os KPIs validados e as convenções de
cálculo usadas no dashboard de e-commerce da Keyrus.

---

## 1. Visão geral do negócio

- **Domínio:** e-commerce com venda também em loja física (modelo omnichannel).
- **Período dos dados de venda:** 13/dez/2025 a 11/jan/2026 (~30 dias).
- **Receita total no período:** ~R$ 969.837,27.
- **Canais de venda (2):** `ecommerce` e `loja_fisica`.
- **Categorias de produto (11):** Casa, Acessórios, Moda, Informática, Cozinha,
  Esporte, Games, Áudio, Tênis, Eletrônicos, Beleza.
- **Base de clientes:** 50 clientes, 22 estados brasileiros, país único (Brasil).
- **Catálogo:** 215 produtos.
- **Monitoramento de concorrência:** 4 concorrentes (`Shopee`, `Amazon`, `Magalu`,
  `Mercado Livre`), com coleta de preços em snapshot único (11/jan/2026 — sem série
  temporal de preço de concorrente).
- **Acesso a dados:** somente leitura. Toda a aplicação usa a **chave anônima/pública**
  do Supabase (RLS libera `SELECT` anônimo nas 4 tabelas). Nunca usar `DATABASE_URL`
  ou credenciais diretas de Postgres em código client-side.

## 2. Stack técnica e arquitetura de dados

| Camada | Escolha | Observação |
|---|---|---|
| Banco | **Supabase (Postgres)**, schema `public` | RLS habilitado, policies de `SELECT` para `anon`/`authenticated` |
| Frontend web | Vite + React 18 + TypeScript estrito | SPA estática, `react-router-dom` |
| Alternativa/PoC | **Streamlit** (Python) | `streamlit_app/`, mesmo banco, mesma chave anon |
| Cliente de dados | `@supabase/supabase-js` (web) / `supabase-py` (Python) | Cliente único e compartilhado — nunca duplicar/instanciar outro |
| Gráficos | Recharts (web) | — |
| Paginação | `.range()` em lotes de **1000 linhas** (limite padrão do PostgREST) | Necessário em `vendas` (3.000 linhas) e ao cruzar com `clientes`/`produtos` |
| Agregação | No cliente (browser/Python), não em SQL agregado pela app | Fetch cru + `pandas`/`useMemo` para somar/agrupar |
| Cache | `st.cache_data(ttl=300)` (Streamlit) / `useMemo` (React) | Evita refetch a cada render |

**Padrão de fetch paginado (essencial para replicar em outro projeto):**
```python
PAGE = 1000
def fetch_all(table, columns, order_by=None):
    rows, frm = [], 0
    while True:
        q = client.table(table).select(columns)
        if order_by: q = q.order(order_by)
        res = q.range(frm, frm + PAGE - 1).execute()
        batch = res.data or []
        rows.extend(batch)
        if len(batch) < PAGE:
            break
        frm += PAGE
    return rows
```

## 3. Schema do banco (Supabase/Postgres, schema `public`)

Todas as 4 tabelas têm **RLS habilitado** com policy de `SELECT` liberada para `anon`.

### `clientes` (50 linhas)
| Coluna | Tipo | Notas |
|---|---|---|
| `id_cliente` | text | PK |
| `nome_cliente` | text | |
| `estado` | varchar | UF do cliente (22 valores distintos) |
| `pais` | text | valor único: Brasil |
| `data_cadastro` | timestamptz | |

### `produtos` (215 linhas)
| Coluna | Tipo | Notas |
|---|---|---|
| `id_produto` | text | PK |
| `nome_produto` | text | |
| `categoria` | text | 11 categorias |
| `marca` | text | |
| `preco_atual` | numeric | preço de referência/venda atual |
| `data_criacao` | timestamptz | |

### `preco_competidores` (728 linhas)
| Coluna | Tipo | Notas |
|---|---|---|
| `id` | bigint | PK (identity) |
| `id_produto` | text | FK → `produtos.id_produto` |
| `nome_concorrente` | text | 4 valores: Shopee, Amazon, Magalu, Mercado Livre |
| `preco_concorrente` | numeric | preço coletado do concorrente |
| `data_coleta` | timestamptz | todas as linhas com a mesma data (snapshot único) |

### `vendas` (3.000 linhas)
| Coluna | Tipo | Notas |
|---|---|---|
| `id_venda` | text | PK |
| `data_venda` | timestamptz | 13/dez/2025 a 11/jan/2026 |
| `id_cliente` | text | FK → `clientes.id_cliente` |
| `id_produto` | text | FK → `produtos.id_produto` |
| `canal_venda` | text | check constraint: `ecommerce` \| `loja_fisica` |
| `quantidade` | integer | |
| `preco_unitario` | numeric | preço praticado **naquela venda** (pode diferir de `produtos.preco_atual`) |

### Relacionamentos
```
clientes (1) ───< (N) vendas (N) >─── (1) produtos (1) ───< (N) preco_competidores
```
- `vendas.id_cliente → clientes.id_cliente`
- `vendas.id_produto → produtos.id_produto`
- `preco_competidores.id_produto → produtos.id_produto`

### Cobertura validada
- 215/215 produtos têm ao menos 1 preço de concorrente cadastrado.
- Maioria dos produtos tem entre 3 e 4 concorrentes cotados.

## 4. Convenção fundamental de cálculo

> **Receita de uma venda = `quantidade * preco_unitario`.**

Isso é usado em 100% dos KPIs de receita do projeto — nunca usar `produtos.preco_atual`
para calcular receita histórica (o preço praticado na venda é o de `vendas.preco_unitario`,
que pode ter variado com o tempo/promoções).

Notação usada nos KPIs de pricing, por produto `p`:
- `preco(p) = produtos.preco_atual`
- `avg_comp(p)` = média de `preco_concorrente` entre os concorrentes daquele produto
- `min_comp(p)` = menor `preco_concorrente` daquele produto
- `gap_frac(p) = (preco(p) - avg_comp(p)) / avg_comp(p)`

## 5. KPIs por domínio

### 5.1 Vendas & Receita
Fonte: `vendas` + join `produtos` (para `categoria`/`nome_produto`).

| KPI | Fórmula | Valor validado |
|---|---|---|
| Receita total | `SUM(quantidade * preco_unitario)` | R$ 969.837,27 |
| Ticket médio | `receita_total / COUNT(vendas)` | R$ 323,28 |
| Total de vendas | `COUNT(*)` | 3.000 |
| Itens vendidos | `SUM(quantidade)` | 4.297 |
| Clientes ativos | `COUNT(DISTINCT id_cliente)` | 50 |
| Receita e-commerce (%) | `receita(ecommerce) / receita_total` | 72,5% |
| Categoria líder | `argmax_categoria SUM(receita)` | Moda (R$ 248.124 · 25,6%) |

Detalhe por canal: e-commerce R$ 703.445,79 (ticket médio R$ 327,95) vs loja física
R$ 266.391,48 (ticket médio R$ 311,57).

Gráficos recomendados: evolução diária da receita (área/linha — faturamento estável
em ~R$ 32k/dia), receita por canal (donut + ticket), receita por categoria (barras),
top 5 produtos por receita (concentração em poucos SKUs).

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

### 5.2 Pricing & Margem
Fontes: `produtos` (215) e `preco_competidores` (728). **Snapshot de um único dia** —
não há série temporal de gap de preço.

| KPI | Fórmula | Valor atual |
|---|---|---|
| Gap médio vs mercado | `média_p( (preco − avg_comp) / avg_comp )` | +7,4% |
| Produtos acima do mercado | `#{p : preco > avg_comp} / N` | 59,1% (127/215) |
| Líderes de preço | `#{p : preco ≤ min_comp}` | 25 (11,6%) |
| Categoria em alerta | categoria com maior gap médio | Tênis (+100%) |

KPIs de detalhe:
- **Gap médio por categoria** — média de `gap_frac` dentro da categoria.
- **Paridade de preços** (scatter) — ponto `(avg_comp, preco)` por produto vs linha
  `y = x`; pontos acima da linha = mais caros que o mercado.
- **Posição frente a cada concorrente** — por concorrente, contagem de comparações
  produto-a-produto em que somos mais caros vs mais baratos.
- **Sobrepreço vs menor concorrente** (ranking de risco de reprecificação) —
  `(preco − min_comp) / min_comp` só para produtos com `preco > min_comp`, top 10 desc.

**Regra de sinal (importante, é uma inversão da regra geral):** preço **menor** que o
concorrente é `success` (verde, bom para o negócio); preço **maior** é `danger`
(vermelho). Isso é o oposto do "verde = crescimento" usado em receita.

Insight validado: fora da categoria **Tênis** (que sozinha está ~2x o preço dos
concorrentes em todos os 15 SKUs e distorce a média geral), o portfólio fica muito
próximo da paridade (gap entre −0,3% e +1,2%). Magalu e Shopee são os concorrentes
onde a empresa está mais cara.

### 5.3 Clientes & Comportamento
Fontes: `clientes` (50) e `vendas` (3.000, FK `id_cliente`).

| KPI | Fórmula | Valor validado |
|---|---|---|
| Clientes ativos | `COUNT(DISTINCT id_cliente em vendas)` / total `clientes` | 50/50 (100%) |
| Receita média por cliente | `receita_total / total_clientes` | R$ 19.396,75 |
| Ticket médio | média por cliente de `receita_cliente / nº_compras` | R$ 324,53 |
| Frequência média | `Σ nº_compras / total_clientes` | 60 compras/cliente (mín 36, máx 81) |
| Concentração Top 10 | `Σ receita dos 10 maiores / receita_total` | 27,0% |
| Canal preferido | por cliente, canal de maior `Σ receita` | 49 e-commerce / 1 loja física |

Gráficos: distribuição geográfica (receita por UF, 22 estados), top 10 clientes,
scatter comportamento de compra (frequência × ticket médio, tamanho = receita — cliente
de alto valor = alto nas duas dimensões), mix de canal (donut).

Insight validado: carteira **100% ativa**, **pouco concentrada** (Top 10 = 27% da
receita — sinal de carteira saudável e distribuída), **e-commerce dominante** (72,5%
da receita, 49 de 50 clientes preferem esse canal).

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

## 6. Regras de design e sinalização (para dashboards)

- **Regra geral:** verde (`success`) = bom para o negócio, vermelho (`danger`) = ruim.
- **Exceção pricing:** preço menor que concorrente = verde; preço maior = vermelho
  (inverso do que se poderia assumir por analogia com "queda de receita = ruim").
- **Paleta categórica fixa** — mesma categoria sempre usa a mesma cor em todas as
  seções/gráficos (evita que o usuário precise reaprender a legenda a cada tela).
- **Canais:** `ecommerce` = ciano, `loja_fisica` = navy (cores de marca).
- Evitar: gráfico de pizza com mais de ~5 fatias (usar barras para categorias
  numerosas), 3D, eixos truncados que distorçam a leitura.

## 7. Segurança e acesso a dados

- Acesso **somente leitura** (`SELECT`) via chave **anônima/pública** do Supabase.
- RLS habilitado nas 4 tabelas, com policies liberando apenas `SELECT` para
  `anon`/`authenticated` — nenhuma operação de escrita é exposta ao app.
- **Nunca** versionar `.env`, `DATABASE_URL` ou senha de Postgres — variáveis ficam
  em `.env` (gitignored) e a app só lê `SUPABASE_URL`/`SUPABASE_KEY` (ou os
  equivalentes `VITE_SUPABASE_URL`/`VITE_SUPABASE_ANON_KEY` no frontend web).
- Um único cliente Supabase compartilhado por app (evitar múltiplas instâncias);
  no Streamlit, `@st.cache_resource` no client e `@st.cache_data(ttl=300)` nas
  funções de carga de dados.

## 8. Resumo executivo (para pitch/negócio)

- Negócio saudável em receita (~R$ 970k/mês), com e-commerce claramente dominante
  (72,5% da receita e da preferência de clientes).
- Carteira de clientes pequena mas **bem distribuída** — baixo risco de concentração
  (Top 10 = 27%) e 100% de clientes ativos no período.
- Maior risco identificado é de **pricing**, concentrado quase inteiramente numa
  única categoria (Tênis, ~2x o preço de mercado) — ação prioritária de
  reprecificação já vem ranqueada pelo próprio painel (KPI "sobrepreço vs menor
  concorrente").
- Fora desse ofensor único, o portfólio de preços está essencialmente em paridade
  com o mercado.
