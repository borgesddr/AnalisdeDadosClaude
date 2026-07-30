# Decisões de projeto

Registro das decisões tomadas nas fases iniciais do dashboard. Os documentos-fonte
completos são [`DESIGN_SYSTEM.md`](../DESIGN_SYSTEM.md) e
[`CONVENTIONS.md`](../CONVENTIONS.md) na raiz — este arquivo resume o essencial e
aponta para eles.

## Fase 0 — Verificação inicial

- **Base de dados validada** (Supabase / Postgres, schema `public`, RLS ligado com
  SELECT anônimo). Quatro tabelas: `clientes` (50), `produtos` (215),
  `preco_competidores` (728) e `vendas` (3.000).
- **Fatos do dataset:** 3.000 vendas de 13/dez/2025 a 11/jan/2026; receita
  ~R$ 969.837; 2 canais (`ecommerce`, `loja_fisica`); 11 categorias de produto;
  22 estados; 4 concorrentes.
- **Acesso a dados:** somente leitura (SELECT). O dashboard usa a chave pública/anon
  via variáveis `VITE_`. Credenciais diretas de Postgres (`DATABASE_URL`, senhas)
  nunca entram no bundle nem no versionamento (`.env` no `.gitignore`).

## Fase 1 — Design system e convenções

### Stack (ver [README](../README.md#stack-e-motivação))
Vite + React 18 + TypeScript (estrito), react-router-dom, Tailwind CSS, Recharts,
`@supabase/supabase-js`, e Vitest + Testing Library para testes. Novas dependências só
com alinhamento do líder para manter o `package.json` coeso.

### Design system (resumo de [`DESIGN_SYSTEM.md`](../DESIGN_SYSTEM.md))
- **Tokens Tailwind, não hex cru.** Toda cor vem dos tokens espelhados em
  `tailwind.config.js` e, para gráficos, de `src/lib/theme.ts`.
- **Paleta de marca:** `brand-navy`, `brand-cyan`, `brand-orange` (+ variações).
  Neutros de UI (`bg`, `surface`, `border`, `text`, `text-muted`).
- **Cores semânticas:** `success` (verde), `warning`, `danger` (vermelho), `neutral`.
  Regra de sinal: **verde = bom para o negócio, vermelho = ruim**. Atenção em pricing —
  preço menor que o concorrente é `success`, não `danger`.
- **Paleta categórica fixa** para as 11 categorias (`CATEGORY_COLORS`): mesma categoria
  usa sempre o mesmo índice/cor em todas as seções. Canais: `ecommerce` = cyan,
  `loja_fisica` = navy.
- **Tipografia:** Inter (fallback system-ui), sem CDN. Escala definida (título de
  página `text-2xl`, valor de KPI `text-3xl font-bold`, label/eixo `text-xs`).
- **Layout:** grid de KPIs `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`; grid de
  gráficos `lg:grid-cols-2`; container `max-w-7xl mx-auto`; card
  `bg-surface rounded-2xl border shadow-sm p-6`.
- **Gráficos (Recharts):** sempre `Tooltip`, `Legend` (2+ séries), eixos rotulados,
  `ResponsiveContainer`. Valores monetários via `formatBRL`. Proibido 3D, pizza com
  mais de ~5 fatias e eixos truncados. Todo componente que busca dados trata `loading`
  e `error`.

### Convenções (resumo de [`CONVENTIONS.md`](../CONVENTIONS.md))
- **Propriedade exclusiva de pastas.** Cada especialista só edita sua pasta:
  `src/sections/vendas`, `.../pricing`, `.../clientes`. QA só **cria** em `tests/**`.
  Arquivos compartilhados (`src/App.tsx`, `src/lib/**`, configs, `tailwind.config.js`)
  são do líder.
- **Estrutura por seção:** `index.tsx` (default export, usado como rota) +
  `components/` + `hooks/` (data fetching) + `README.md` (KPIs, fórmulas, queries).
- **Acesso a dados** só pelo cliente compartilhado `src/lib/supabase.ts`; reutilizar
  `src/lib/format.ts` e `src/lib/theme.ts`. Nunca criar outro cliente nem usar
  `DATABASE_URL`.
- **Estilo:** TypeScript estrito, componentes funcionais + hooks, só classes Tailwind;
  componentes em PascalCase, hooks em camelCase com prefixo `use`.
- **Rotas** definidas em `src/App.tsx` (líder): `/vendas`, `/pricing`, `/clientes`.

### Divisão de trabalho por domínio
| Domínio | Tabelas | Pasta |
|---|---|---|
| Vendas & Receita | `vendas` (+ join `produtos`, `clientes`) | `src/sections/vendas` |
| Pricing & Margem | `produtos`, `preco_competidores` | `src/sections/pricing` |
| Clientes & Comportamento | `clientes`, `vendas` | `src/sections/clientes` |
