# Dashboard E-commerce — Streamlit

Porta em Python/Streamlit do dashboard React (`../src`). Mesmas 3 seções, mesmas
fórmulas de KPI e mesma paleta de cores (ver `../DESIGN_SYSTEM.md` e `../docs/KPIS.md`
— fonte de verdade das fórmulas). Consome o mesmo Supabase, somente leitura, com as
credenciais já existentes em `../.env` (`SUPABASE_URL` / `SUPABASE_KEY`) — não
duplica nem versiona segredos.

## Setup

1. Crie e ative um ambiente virtual (a partir desta pasta `streamlit_app/`):

   ```
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS/Linux
   ```

2. Instale as dependências:

   ```
   pip install -r requirements.txt
   ```

3. Rode o app:

   ```
   streamlit run app.py
   ```

   Abre em `http://localhost:8501`.

## Estrutura

```
streamlit_app/
  app.py             # router (st.navigation) — 3 páginas
  views/
    vendas.py         # Vendas & Receita
    pricing.py        # Pricing & Margem
    clientes.py        # Clientes & Comportamento
  lib/
    supabase_client.py # cliente cacheado (st.cache_resource), lê ../.env
    data.py             # fetch paginado + agregação (pandas) por domínio, cacheado (st.cache_data, ttl=300s)
    theme.py            # cores de marca/categoria/canal (mesmos hex do React)
    format.py           # formatBRL/formatNumber/formatPercent equivalentes, pt-BR
    ui.py               # kpi_card / chart_card_header (cards no estilo do design system)
  .streamlit/config.toml # tema visual (cores da marca)
```

## Diferenças em relação à versão React

- Gráficos com **Plotly** (equivalente funcional ao Recharts: tooltip, legenda, eixos
  rotulados).
- Navegação por `st.navigation`/`st.Page` (sidebar) em vez de rotas `react-router`.
- Cache de dados via `st.cache_data`/`st.cache_resource` em vez de hooks React
  (`useVendas`, `usePricing`, `useClientes`).
