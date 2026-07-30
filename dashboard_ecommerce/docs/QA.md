# QA — achados e resoluções

Resumo do relatório de QA/Arquitetura (`tests/RELATORIO_QA.md`, 2026-07-30). Estado
geral **BOM**: segurança correta (RLS restritivo somente-SELECT, chave publishable/anon,
sem credenciais no bundle), `tsc --noEmit` limpo e **25 testes automatizados, todos
passando** (Vitest + Testing Library + jsdom), cobrindo hooks e render das 3 seções.

## Auditoria (resumo)
- **Segurança:** `.env` gitignored; 0 credenciais hardcoded em `src/`; cliente único em
  `src/lib/supabase.ts` com `persistSession:false`; `get_advisors(security)` = 0 lints;
  RLS habilitado nas 4 tabelas, apenas policies de SELECT para anon/authenticated.
- **Queries:** sem N+1, colunas explícitas, paginação por `.range()` em vendas/clientes;
  sem SQL bruto nem input de usuário → risco de injeção nulo.
- **Design system:** 0 cores hex hardcoded em `src/sections/**` (tudo via
  `src/lib/theme.ts`); formatação via `src/lib/format.ts`; gráficos com
  `ResponsiveContainer`+`Tooltip`; todas as seções tratam `loading` e `error`.

## Achados e resolução
| # | Sev. | Descrição | Status |
|---|---|---|---|
| #8 | Médio/infra | Artefatos `vite.config.js`/`.d.ts` versionáveis (causa: `tsconfig.node.json` com `composite` sem `outDir`) | **Resolvido** — emit redirecionado para `node_modules/.tmp/`; artefatos + `*.tsbuildinfo` no `.gitignore` (verificado) |
| #9 | Baixo/seg. | `DATABASE_URL` com senha real no `.env` | **Resolvido** — aceite de risco documentado pelo dono da credencial; `.env` gitignored e não referenciado em `src/` (não vaza no bundle). Recomendação de higiene: rotacionar a senha |
| #10 | Baixo/perf | `usePricing` sem paginação (preventivo, dados < 1000 linhas) | **Resolvido** — padrão de paginação adotado |
| #11 | Baixo-Médio/perf | Bundle de produção ~842kB (Recharts) | **Em andamento** — code-splitting por rota (`React.lazy`/`Suspense`) pelo líder na Fase 3 |

**Conclusão:** nenhum achado crítico ou de média severidade aberto no código das seções.
Resta apenas o code-splitting do bundle (#11), tratado na integração final da Fase 3.
