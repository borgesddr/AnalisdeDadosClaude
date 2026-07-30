# Convenções de código e propriedade de arquivos

Regras de colaboração para os 6 agentes. **Leia antes de escrever qualquer arquivo.**

## 1. Propriedade exclusiva de pastas

Cada especialista é **dono exclusivo** da sua pasta de seção e só edita arquivos
dentro dela:

| Agente | Pasta (propriedade exclusiva) |
|---|---|
| Especialista Vendas | `src/sections/vendas/**` |
| Especialista Pricing | `src/sections/pricing/**` |
| Especialista Clientes | `src/sections/clientes/**` |
| QA / Arquitetura | `tests/**` (apenas cria arquivos de teste) |
| Líder (lider) | fundação + integração na Fase 3 |

**Ninguém edita arquivos fora da própria pasta.** Arquivos compartilhados
(`src/App.tsx`, `src/lib/**`, configs na raiz, `tailwind.config.js`) pertencem ao
líder — se precisar de algo novo ali, peça ao líder; não edite diretamente.

Exceções:
- **Líder** pode tocar em qualquer arquivo (é dono da fundação e da integração Fase 3).
- **QA** só **cria** arquivos em `tests/**`; não altera código de seção.

## 2. Estrutura dentro de cada `src/sections/<dominio>/`

```
src/sections/<dominio>/
  index.tsx          # exporta o componente da seção (default export)
  components/        # sub-componentes (cards, gráficos) desta seção
  hooks/             # data fetching (ex: useVendas.ts) via cliente supabase
  README.md          # KPIs da seção, fórmulas e queries usadas
```

- `index.tsx` deve exportar um componente React default, já usado como rota em `App.tsx`.
- Todo acesso a dados passa pelo cliente compartilhado `src/lib/supabase.ts` (import
  `supabase`). Nunca crie outro cliente nem use `DATABASE_URL`/senhas.
- Reutilize helpers compartilhados: `src/lib/format.ts` (formatação pt-BR/BRL),
  `src/lib/theme.ts` (`CATEGORY_COLORS`, cores de canal/semânticas).

## 3. Recursos compartilhados (`src/lib/`, propriedade do líder)

- `supabase.ts` — cliente `@supabase/supabase-js` já configurado com as env `VITE_`.
- `format.ts` — `formatBRL`, `formatNumber`, `formatPercent`, `formatDate` (pt-BR).
- `theme.ts` — tokens de cor em JS para uso nos gráficos Recharts.

## 4. Estilo de código

- TypeScript estrito; componentes funcionais + hooks.
- Estilização só com classes Tailwind (tokens do `DESIGN_SYSTEM.md`). Sem CSS inline
  de cor solto — use os tokens.
- Cada seção trata estados de `loading` e `error` no fetch.
- Nomes de arquivos de componente em PascalCase; hooks em camelCase com prefixo `use`.

## 5. Git / segurança

- Nunca versionar `.env`, senhas ou `DATABASE_URL` (o `.env` já está no `.gitignore`).
- Só leitura (SELECT) contra o Supabase a partir do dashboard; RLS libera SELECT anon.
- Não instale dependências novas sem alinhar com o líder (mantém o `package.json` coeso).

## 6. Rotas

Rotas já definidas em `src/App.tsx` (líder): `/vendas`, `/pricing`, `/clientes`.
Cada especialista preenche o `index.tsx` da sua seção; o líder faz o wiring final.
