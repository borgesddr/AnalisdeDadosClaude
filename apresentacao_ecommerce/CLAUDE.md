# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This repository currently contains only raw source data and a PRD (`.llm/prd.md`) — there is no analysis code, build tooling, or generated output yet. Any commands to "build," "lint," or "test" do not yet exist; the first substantive work here is to create the KPI-extraction scripts and the final HTML report described below.

Note: the git repository root is one level up (`AnalisedeDados_Claude/`), and it contains a sibling project `limpeza_venda/` (a Streamlit CSV-cleaning tool with an unrelated data schema). Treat `apresentacao_ecommerce/` as self-contained — don't assume shared code or dependencies with that sibling project.

## Goal (from `.llm/prd.md`)

Produce a complete e-commerce analysis as a final **HTML report**, using the CSVs in `data/`. The required workflow, per the PRD:

1. **Do not dump all raw CSVs into the LLM context at once.** `vendas.csv` alone has ~3000 rows.
2. First identify the joins between the tables (see Data model below).
3. Determine the KPIs needed for the analysis.
4. Pre-compute those KPIs into smaller intermediate files (e.g. aggregated CSV/JSON summaries) so later analysis/generation steps work from compact data instead of raw rows.
5. Generate the final HTML from those pre-computed KPI files.

When implementing this, prefer a script (Python/pandas is the natural fit given the sibling project's stack) that reads `data/*.csv`, computes and writes intermediate KPI files (e.g. into a `output/` or `kpis/` folder), and a separate step/template that renders HTML from those intermediate files — keep these two steps decoupled so the HTML-generation step never needs to touch the full raw data.

## Data model (`data/`)

Four CSVs, joined by `id_cliente` / `id_produto`:

- **`clientes.csv`** — `id_cliente, nome_cliente, estado, pais, data_cadastro` (51 rows; one row per customer; `estado` is a Brazilian UF)
- **`produtos.csv`** — `id_produto, nome_produto, categoria, marca, preco_atual, data_criacao` (216 rows; catalog price is `preco_atual`, distinct from the actual transacted price in `vendas.csv`)
- **`vendas.csv`** — `id_venda, data_venda, id_cliente, id_produto, canal_venda, quantidade, preco_unitario` (3021 rows; fact table; `canal_venda` is `ecommerce` or `loja_fisica`; dates span 2025-12-13 to 2026-01-11)
- **`preco_competidores.csv`** — `id_produto, nome_concorrente, preco_concorrente, data_coleta` (729 rows; competitor price scraped per product; `nome_concorrente` is one of Amazon, Magalu, Mercado Livre, Shopee)

Joins:
- `vendas.id_cliente → clientes.id_cliente`
- `vendas.id_produto → produtos.id_produto`
- `preco_competidores.id_produto → produtos.id_produto`

Revenue per sale = `vendas.quantidade * vendas.preco_unitario` (do not use `produtos.preco_atual` for realized revenue — it's the current catalog price, not what was charged historically). Competitive pricing analysis compares `vendas.preco_unitario` / `produtos.preco_atual` against `preco_competidores.preco_concorrente` per product.

## Visual identity for the HTML output (Keyrus brand)

The PRD specifies a design system extracted from keyrus.com/br/pt visuals — apply this to any generated HTML/dashboard:

**Colors**
- Background: white `#FFFFFF`
- Topbar: dark navy `#0B2265` → `#0A1F5C`
- Accent cyan (active links, buttons): `#29ABE2` → `#38BDF8`
- Accent orange (geometric shapes, floating button): `#F5A623` → `#F7941D`
- Logo lettering (per-letter color): k=cyan `#29ABE2`, e=orange `#F5A623`, y=magenta `#EC4899`, r=red `#E63946`, u/s=black `#111111`
- Title text: `#111111`–`#1A1A1A`; body text: `#333333`–`#4A4A4A`
- Primary buttons: pill-shaped, cyan `#38BDF8` fill, white text
- Secondary buttons: cyan outline, cyan text, white fill
- Dividers/borders: light gray `#E0E0E0`
- "Ai" gradient accents: cyan→blue `#00D4FF`→`#2979FF` and red→orange `#E63946`→`#F2994A`

**Typography**: geometric sans-serif throughout (Poppins-like). Titles bold/extra-bold, slightly rounded. Body regular weight, ~1.5–1.6 line height. Buttons bold/semibold with short, direct labels. Nav text medium weight, smaller than titles.

**Layout**: fixed two-layer header (thin topbar + main navbar with logo/menu); generous whitespace between blocks; large-radius rounded cards (~16–24px) with soft shadows; pill-shaped buttons; decorative colored vertical bars on the page edges (cyan left, orange geometric shapes right); small circular icon/badge markers; circular floating action button in the bottom-left corner.

Note per the PRD: these hex values/fonts are visually estimated from screenshots, not inspected from live CSS — treat as close approximations, not exact brand tokens.
