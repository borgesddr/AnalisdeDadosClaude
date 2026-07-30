# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This directory currently contains only planning artifacts (`.llm/prd.md`, `PROJETO_REFERENCIA.md`) and one stray file (`supabase_client.py`) — **`app.py`, the bot itself, has not been written yet.** There is no build, lint, or test tooling because there is no application code yet. The first substantive work here is writing `app.py` per the PRD below.

Note: the git repository root is one level up (`AnalisedeDados_Claude/`), which contains sibling projects (`dashboard_ecommerce/`, `apresentacao_ecommerce/`, `limpeza_venda/`) with unrelated/independent stacks. Treat `AgenteTelegram/` as self-contained — don't assume shared code or dependencies with those siblings, even though it reuses the same Supabase database and business rules as `dashboard_ecommerce`.

## Goal (from `.llm/prd.md`)

Build a single-file Python Telegram bot (`app.py`) that gives 3 capabilities over the e-commerce data in Supabase:

1. **Chat livre** — answers arbitrary questions about the e-commerce data by having Claude (Anthropic API) query the database live via tool use (Claude decides and executes SQL dynamically, not canned queries).
2. **Relatório executivo** — on `/relatorio`, generates a report for 3 directors (Comercial, CS, Pricing) with actionable insights, built from the KPIs defined in `PROJETO_REFERENCIA.md`.
3. **Envio automático** — the `/relatorio` command triggers the send.

Stack mandated by the PRD:
- **DB:** PostgreSQL via Supabase (read-only, anon key — see Data access below)
- **LLM:** Claude (Anthropic API), using tool use so the model can issue SQL against the DB
- **Bot framework:** `python-telegram-bot` v20+
- Everything lives in one file, `app.py`, at the root of this directory

## Required environment variables

`.env` (gitignored, at `AgenteTelegram/.env`) currently only has the Supabase credentials, copied from `dashboard_ecommerce`:
- `SUPABASE_URL` / `SUPABASE_KEY` (anon key — read-only)
- `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` (aliases, unused by this Python project)
- `DATABASE_URL` (direct Postgres connection string — **do not use this in application code**, see Data access below)

Per the PRD, still need to be added:
- Anthropic API key (for Claude tool use)
- Telegram bot token (from BotFather)

## Data model and business rules

`PROJETO_REFERENCIA.md` is the authoritative reference for this project — it's a consolidated knowledge doc (schema, KPI formulas, validated values) pulled from the `dashboard_ecommerce` project so it can be reused here without re-deriving anything. Read it before writing any SQL or KPI logic. Key points:

- 4 tables in Supabase schema `public`, all with RLS enabling anon `SELECT` only: `clientes` (50), `produtos` (215), `preco_competidores` (728), `vendas` (3000, the fact table).
- Joins: `vendas.id_cliente → clientes.id_cliente`, `vendas.id_produto → produtos.id_produto`, `preco_competidores.id_produto → produtos.id_produto`.
- **Revenue convention:** `receita = quantidade * preco_unitario` from `vendas`, always — never `produtos.preco_atual` for historical revenue (that's the current catalog price, not what was charged).
- **Pricing gap convention:** `gap_frac(p) = (preco_atual(p) - avg_comp(p)) / avg_comp(p)`, where `avg_comp` is the mean competitor price for that product. Sign is inverted vs. revenue KPIs: a **lower** price than competitors is the good outcome here.
- `preco_competidores` is a single-day snapshot — there is no time series for competitor pricing.
- The full validated KPI list (with SQL) for Vendas & Receita, Pricing & Margem, and Clientes & Comportamento is in `PROJETO_REFERENCIA.md` §5 — use those formulas verbatim for `/relatorio` rather than inventing new ones.

## Data access

- **Read-only.** The app must only use the Supabase anon/public key (`SUPABASE_URL`/`SUPABASE_KEY`), which has RLS-scoped `SELECT` access to the 4 tables. Never use `DATABASE_URL` or direct Postgres credentials from application code.
- PostgREST (and therefore `supabase-py`) caps result pages at 1000 rows. `vendas` has 3000 rows, so any full-table fetch needs `.range()` pagination — see the `fetch_all` pattern in `PROJETO_REFERENCIA.md` §2. Aggregate in Python (pandas or plain loops) after fetching, not via Supabase's query builder.
- `supabase_client.py` in this directory is a leftover copy from `dashboard_ecommerce/streamlit_app/lib/supabase_client.py` (same shared-client/`.env`-loading pattern) — its `ROOT_ENV` path (`parents[2]`) was correct for that file's original nesting depth (`streamlit_app/lib/`) but is **wrong here**, since `.env` sits directly alongside this file in `AgenteTelegram/`. Fix the path (or inline the client) when building `app.py`; don't copy the `parents[2]` logic as-is. It's also written against `streamlit`'s `@st.cache_resource`, which doesn't apply outside a Streamlit app — a Telegram bot should instantiate the client once at module load instead.
