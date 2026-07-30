# Relatório QA / Arquitetura — Dashboard E-commerce Keyrus

Data: 2026-07-30 · Responsável: agente `qa` · Escopo: auditoria de segurança,
configuração, eficiência de queries e testes automatizados das 3 seções.

## 1. Resumo executivo

Estado geral **BOM**. A postura de segurança está correta (RLS restritivo,
chave publishable/anon, sem credenciais no bundle). As 3 seções (Vendas, Pricing,
Clientes) estão cobertas por testes automatizados — **25 testes, todos passando** —
e o projeto compila sem erros de tipo (`tsc --noEmit` limpo).

## 2. Auditoria de segurança e configuração

### Segredos / credenciais
- `.env` está no `.gitignore` e é efetivamente ignorado pelo git (`git check-ignore .env` confirma).
- Nenhuma credencial hardcoded em `src/` (grep por `DATABASE_URL`, `service_role`, `postgresql://`, chave: 0 ocorrências).
- `VITE_SUPABASE_ANON_KEY` usa a chave **publishable** (`sb_publishable_...`) — segura para bundle client-side, não é service_role.
- `src/lib/supabase.ts` cria um único cliente com `persistSession: false`, sem service_role.

### Supabase (banco)
- `get_advisors(security)` → **0 lints**.
- RLS **habilitado** nas 4 tabelas (`clientes`, `produtos`, `preco_competidores`, `vendas`).
- Policies: apenas `SELECT` para `{anon, authenticated}` com `qual = true`; **nenhuma** policy de INSERT/UPDATE/DELETE e nenhum `with_check`. Exatamente o esperado para um dashboard somente-leitura.

### Configuração / scaffold
- Todos os arquivos de build presentes: `tsconfig.json`, `tsconfig.node.json`, `tailwind.config.js`, `postcss.config.js`, `index.html`, `src/main.tsx`, `src/index.css`.
- `tsconfig.json` estrito e coerente (`strict`, `noUnusedLocals`, `noEmit`).

## 3. Auditoria de eficiência e qualidade das queries

- **Vendas** (`useVendas`): paginação correta via `.range()` em lotes de 1000 (para as 3000 linhas); usa join embutido `produtos(...)` em vez de N+1; seleciona colunas explícitas (sem `SELECT *`). OK.
- **Pricing** (`usePricing`): 2 queries em paralelo (`Promise.all`), colunas explícitas, sem N+1. Volumes atuais (215 produtos, 728 preços) estão sob o limite padrão de 1000 linhas do PostgREST. **Observação de baixa severidade**: não há paginação; se `preco_competidores` crescer além de 1000 linhas, haveria truncamento silencioso (ver Achado B-1).
- **Clientes** (`useClientes`): paginação via `fetchAll` para ambas as tabelas; agregação em memória; sem N+1. OK.
- **Injeção de SQL**: não há SQL bruto nem input de usuário concatenado em nenhuma seção — todo acesso passa pelo query builder do supabase-js. Risco nulo.

## 4. Consistência com Design System / Convenções

- **0 cores hardcoded** (hex) em `src/sections/**` — todas as cores vêm de `src/lib/theme.ts` (`CATEGORY_COLORS`, `CHANNEL_COLORS`, `COLORS`).
- Formatação monetária/numérica sempre via `src/lib/format.ts` (`formatBRL`, `formatNumber`, `formatPercent`).
- Gráficos Recharts usam `ResponsiveContainer` + `Tooltip` conforme o guia.
- Cada seção trata `loading` (skeleton) e `error` (mensagem curta).
- Uso de `style` inline restrito a valores dinâmicos legítimos (largura de barra, cor vinda de token) — em conformidade.

## 5. Testes automatizados criados (`tests/`)

Ferramentas: Vitest + @testing-library/react + jsdom. Mock reutilizável do cliente
Supabase em `tests/helpers/supabaseMock.ts` (query builder encadeável e thenable,
com dados/erros configuráveis por teste). Polyfill de `ResizeObserver` para o
Recharts em `tests/setup.ts`.

| Arquivo | Testes | Cobre |
|---|---|---|
| `tests/vendas/useVendas.test.ts` | 5 | KPIs (receita, ticket, % e-commerce), ordenação, série diária, lista vazia, erro |
| `tests/vendas/VendasSection.test.tsx` | 3 | render + KPIs, lista vazia, estado de erro |
| `tests/pricing/usePricing.test.ts` | 6 | gap/líderes/categoria em alerta, risco, ordenação de concorrentes, filtro de inválidos, vazio, erro |
| `tests/pricing/PricingSection.test.tsx` | 3 | render + KPIs, vazio, erro |
| `tests/clientes/useClientes.test.ts` | 5 | ativos/receita/concentração, ranking geográfico, canal preferido/recência, vazio, erro |
| `tests/clientes/ClientesSection.test.tsx` | 3 | render + KPIs, vazio, erro |
| **Total** | **25** | **100% passando** |

Comando: `npm run test` (ou `npx vitest run`).

## 6. Achados

### Resolvidos
- **[#8 — MÉDIO/infra]** Artefatos `vite.config.js` e `vite.config.d.ts` versionáveis coexistindo com o fonte `.ts`. **Resolvido** pelo líder e verificado: causa-raiz era `tsconfig.node.json` com `composite:true` sem `outDir`, fazendo `tsc -b` emitir na raiz; o emit foi redirecionado para `node_modules/.tmp/`. Após `npm run build`, apenas `vite.config.ts` permanece na raiz, e os dois artefatos + `*.tsbuildinfo` foram adicionados ao `.gitignore` (confirmado por `git check-ignore`).

### Risco aceito (documentado)
- **[#9 — BAIXO/segurança]** `DATABASE_URL` com senha real no `.env`. **Aceite de risco explícito do usuário/dono da credencial**, não pendência: a credencial foi configurada pelo usuário antes do projeto e serve a outro propósito fora do dashboard; o usuário decidiu manter o `.env` como está. Mitigantes confirmados por esta auditoria: `.env` gitignored, `DATABASE_URL` não referenciado em `src/` (não vaza no bundle), e o MCP usa OAuth via `.mcp.json` (HTTP), não a connection string. Recomendação de higiene (fora do escopo de arquivos da equipe): rotacionar a senha no painel Supabase, já que existiu em arquivo local.

### Pendentes / rastreamento (owners externos)
- **[#10 — BAIXO/eficiência, owner=pricing]** `usePricing` não pagina as duas queries. Sem impacto hoje (dados < 1000 linhas), mas recomenda-se adotar o padrão de paginação de `useVendas`/`useClientes` caso `preco_competidores` ultrapasse 1000 linhas, para evitar truncamento silencioso.
- **[#11 — BAIXO/MÉDIO perf, owner=lider]** Bundle de produção ~842kB (chunk > 500kB) após a entrada das 3 seções (Recharts é o maior contribuinte). Code-splitting por rota (`React.lazy`/`Suspense`) planejado para a Fase 3.

## 7. Conclusão

As 3 seções estão funcionalmente corretas (validadas por testes de cálculo de KPI
com dados controlados), seguras e consistentes com o design system. **Nenhum achado
crítico ou de média severidade permanece aberto no código das seções.** Os achados
de infra (#8) foram resolvidos e verificados; o item de credencial (#9) é um aceite
de risco documentado pelo dono da credencial. Restam apenas dois itens de baixa
prioridade em rastreamento por owners externos: paginação preventiva em `usePricing`
(#10) e code-splitting do bundle na Fase 3 (#11).
