# Dashboard E-commerce — Keyrus

Dashboard analítico de e-commerce que consolida vendas, pricing e comportamento de
clientes a partir de uma base Supabase (Postgres). A interface é uma SPA estática em
React, organizada em três seções independentes (Vendas & Receita, Pricing & Margem,
Clientes & Comportamento), cada uma com seus próprios KPIs e gráficos.

Os dados são somente leitura: o dashboard executa apenas `SELECT` contra o Supabase
usando a chave pública/anônima (RLS libera leitura anônima).

## Visão geral

- Base de dados: 3.000 vendas entre 13/dez/2025 e 11/jan/2026, receita ~R$ 969.837.
- 2 canais de venda (`ecommerce`, `loja_fisica`), 11 categorias de produto, 22 estados.
- 4 concorrentes acompanhados na tabela de preços (`preco_competidores`).

## Stack e motivação

| Camada | Escolha | Por quê |
|---|---|---|
| Build/dev | **Vite** | Dev server rápido e build estático simples para uma SPA. |
| UI | **React 18 + TypeScript** (estrito) | Componentização por seção; segurança de tipos. |
| Roteamento | **react-router-dom** | Rotas por seção (`/vendas`, `/pricing`, `/clientes`). |
| Estilo | **Tailwind CSS** | Tokens de design centralizados; sem CSS de cor solto. |
| Gráficos | **Recharts** | Biblioteca oficial do projeto; responsiva e declarativa. |
| Dados | **@supabase/supabase-js** | Cliente único compartilhado, apenas leitura (anon key). |
| Testes | **Vitest + Testing Library** (jsdom) | Testes rápidos de unidade/componentes. |

Convenções de código e propriedade de arquivos estão em [CONVENTIONS.md](CONVENTIONS.md);
o guia visual (paleta, tipografia, componentes, regras de gráficos) em
[DESIGN_SYSTEM.md](DESIGN_SYSTEM.md). As decisões de projeto estão registradas em
[docs/DECISOES.md](docs/DECISOES.md), os KPIs por seção em [docs/KPIS.md](docs/KPIS.md)
e o resumo de QA em [docs/QA.md](docs/QA.md).

## Schema resumido (4 tabelas)

Todas as tabelas ficam no schema `public` e têm RLS habilitado (SELECT anônimo).

### `clientes` (50 linhas)
| Coluna | Tipo | Notas |
|---|---|---|
| `id_cliente` | text | PK |
| `nome_cliente` | text | |
| `estado` | varchar | UF do cliente |
| `pais` | text | |
| `data_cadastro` | timestamptz | Data de cadastro |

### `produtos` (215 linhas)
| Coluna | Tipo | Notas |
|---|---|---|
| `id_produto` | text | PK |
| `nome_produto` | text | |
| `categoria` | text | 11 categorias |
| `marca` | text | |
| `preco_atual` | numeric | Preço de referência atual |
| `data_criacao` | timestamptz | |

### `preco_competidores` (728 linhas)
| Coluna | Tipo | Notas |
|---|---|---|
| `id` | bigint | PK (identity) |
| `id_produto` | text | FK → `produtos.id_produto` |
| `nome_concorrente` | text | 4 concorrentes |
| `preco_concorrente` | numeric | Preço coletado do concorrente |
| `data_coleta` | timestamptz | Data da coleta |

### `vendas` (3.000 linhas)
| Coluna | Tipo | Notas |
|---|---|---|
| `id_venda` | text | PK |
| `data_venda` | timestamptz | |
| `id_cliente` | text | FK → `clientes.id_cliente` |
| `id_produto` | text | FK → `produtos.id_produto` |
| `canal_venda` | text | `ecommerce` \| `loja_fisica` (check constraint) |
| `quantidade` | integer | |
| `preco_unitario` | numeric | Preço unitário da venda |

**Relacionamentos:** `vendas.id_cliente → clientes`, `vendas.id_produto → produtos`,
`preco_competidores.id_produto → produtos`. Receita de uma venda =
`quantidade * preco_unitario`.

## Estrutura do projeto

```
src/
  App.tsx            # rotas e layout (dono: líder)
  lib/               # recursos compartilhados (dono: líder)
    supabase.ts      # cliente @supabase/supabase-js (env VITE_)
    format.ts        # formatBRL, formatNumber, formatPercent, formatDate (pt-BR)
    theme.ts         # CATEGORY_COLORS e cores de canal/semânticas
  sections/
    vendas/          # Vendas & Receita
    pricing/         # Pricing & Margem
    clientes/        # Clientes & Comportamento
tests/               # testes (Vitest) — dono: QA
docs/                # documentação do projeto
```

Cada seção segue a estrutura `index.tsx` + `components/` + `hooks/` + `README.md`
descrita em [CONVENTIONS.md](CONVENTIONS.md).

## Setup

Pré-requisitos: Node.js 18+ e npm.

1. **Variáveis de ambiente.** Crie um arquivo `.env` na raiz com as credenciais do
   Supabase (o `.env` está no `.gitignore` — nunca versione credenciais):

   ```
   VITE_SUPABASE_URL=<url-do-projeto-supabase>
   VITE_SUPABASE_ANON_KEY=<chave-publica-anon>
   ```

   Use apenas a chave pública/anônima. Não coloque `DATABASE_URL` nem senhas no bundle
   client-side.

2. **Instalar dependências:**

   ```
   npm install
   ```

3. **Rodar em desenvolvimento** (Vite dev server):

   ```
   npm run dev
   ```

4. **Build de produção** (type-check + bundle estático em `dist/`):

   ```
   npm run build
   ```

5. **Testes** (Vitest):

   ```
   npm run test
   ```

   Use `npm run test:watch` para o modo interativo e `npm run preview` para servir o
   build de produção localmente.
