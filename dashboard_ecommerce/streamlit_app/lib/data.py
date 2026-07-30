"""Fetch + agregação para as 3 seções — porta 1:1 das hooks React:
src/sections/vendas/hooks/useVendas.ts, pricing/hooks/usePricing.ts, clientes/hooks/useClientes.ts.

Fórmula comum de receita: quantidade * preco_unitario (ver docs/KPIS.md).
"""

import pandas as pd
import streamlit as st

from .supabase_client import get_client

PAGE = 1000


def _fetch_all(table: str, columns: str, order_by: str | None = None) -> list[dict]:
    client = get_client()
    rows: list[dict] = []
    frm = 0
    while True:
        q = client.table(table).select(columns)
        if order_by:
            q = q.order(order_by)
        res = q.range(frm, frm + PAGE - 1).execute()
        batch = res.data or []
        rows.extend(batch)
        if len(batch) < PAGE:
            break
        frm += PAGE
    return rows


# ---------------------------------------------------------------------------
# Vendas & Receita
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300, show_spinner="Carregando vendas...")
def load_vendas() -> dict:
    rows = _fetch_all(
        "vendas",
        "data_venda,canal_venda,quantidade,preco_unitario,id_cliente,produtos(categoria,nome_produto)",
        order_by="data_venda",
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return {}

    df["categoria"] = df["produtos"].apply(lambda p: (p or {}).get("categoria") or "Sem categoria")
    df["nome_produto"] = df["produtos"].apply(lambda p: (p or {}).get("nome_produto") or "Sem nome")
    df["receita"] = df["quantidade"] * df["preco_unitario"]
    df["dia"] = df["data_venda"].str.slice(0, 10)

    receita_total = float(df["receita"].sum())
    total_vendas = len(df)
    itens_vendidos = int(df["quantidade"].sum())
    clientes_ativos = int(df["id_cliente"].nunique())
    ticket_medio = receita_total / total_vendas if total_vendas else 0.0

    canais = (
        df.groupby("canal_venda")
        .agg(receita=("receita", "sum"), vendas=("receita", "count"))
        .reset_index()
    )
    canais["ticket_medio"] = canais["receita"] / canais["vendas"]
    canais["pct_receita"] = canais["receita"] / receita_total if receita_total else 0
    canais = canais.sort_values("receita", ascending=False)

    pct_ecommerce = float(
        canais.loc[canais["canal_venda"] == "ecommerce", "pct_receita"].sum()
    )

    top_categorias = (
        df.groupby("categoria")
        .agg(receita=("receita", "sum"), itens=("quantidade", "sum"))
        .reset_index()
        .sort_values("receita", ascending=False)
    )

    top_produtos = (
        df.groupby(["nome_produto", "categoria"])
        .agg(receita=("receita", "sum"), itens=("quantidade", "sum"))
        .reset_index()
        .sort_values("receita", ascending=False)
        .head(5)
    )

    serie_diaria = (
        df.groupby("dia").agg(receita=("receita", "sum")).reset_index().sort_values("dia")
    )

    categoria_lider = top_categorias.iloc[0] if not top_categorias.empty else None

    return {
        "receita_total": receita_total,
        "ticket_medio": ticket_medio,
        "total_vendas": total_vendas,
        "itens_vendidos": itens_vendidos,
        "clientes_ativos": clientes_ativos,
        "pct_ecommerce": pct_ecommerce,
        "canais": canais,
        "serie_diaria": serie_diaria,
        "top_categorias": top_categorias,
        "top_produtos": top_produtos,
        "categoria_lider": categoria_lider,
    }


# ---------------------------------------------------------------------------
# Pricing & Margem
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300, show_spinner="Carregando pricing...")
def load_pricing() -> dict:
    produtos_rows = _fetch_all(
        "produtos", "id_produto,nome_produto,categoria,marca,preco_atual"
    )
    precos_rows = _fetch_all(
        "preco_competidores", "id_produto,nome_concorrente,preco_concorrente"
    )

    produtos = pd.DataFrame(produtos_rows)
    precos = pd.DataFrame(precos_rows)
    if produtos.empty or precos.empty:
        return {}

    produtos["preco_atual"] = pd.to_numeric(produtos["preco_atual"], errors="coerce")
    precos["preco_concorrente"] = pd.to_numeric(precos["preco_concorrente"], errors="coerce")
    precos = precos[precos["preco_concorrente"] > 0]

    comp_stats = (
        precos.groupby("id_produto")["preco_concorrente"]
        .agg(avg_comp="mean", min_comp="min")
        .reset_index()
    )

    merged = produtos.merge(comp_stats, on="id_produto", how="inner")
    merged = merged[merged["preco_atual"] > 0].copy()

    merged["gap_frac"] = (merged["preco_atual"] - merged["avg_comp"]) / merged["avg_comp"]
    merged["gap_reais"] = merged["preco_atual"] - merged["avg_comp"]
    merged["acima_mercado"] = merged["preco_atual"] > merged["avg_comp"]
    merged["lider"] = merged["preco_atual"] <= merged["min_comp"]

    n_produtos = len(merged)
    n_acima = int(merged["acima_mercado"].sum())
    n_lideres = int(merged["lider"].sum())

    by_category = (
        merged.groupby("categoria")
        .agg(gap_frac=("gap_frac", "mean"), n=("gap_frac", "count"), mais_caros=("acima_mercado", "sum"))
        .reset_index()
        .sort_values("gap_frac", ascending=False)
    )
    categoria_alerta = by_category.iloc[0] if not by_category.empty else None

    parity = merged[["id_produto", "nome_produto", "categoria", "preco_atual", "avg_comp"]].copy()

    risk = merged[merged["preco_atual"] > merged["min_comp"]].copy()
    risk["sobrepreco_frac"] = (risk["preco_atual"] - risk["min_comp"]) / risk["min_comp"]
    risk = risk.sort_values("sobrepreco_frac", ascending=False).head(10)

    preco_by_produto = produtos.set_index("id_produto")["preco_atual"]
    precos2 = precos.copy()
    precos2["nosso"] = precos2["id_produto"].map(preco_by_produto)
    precos2 = precos2.dropna(subset=["nosso"])
    precos2["gap"] = (precos2["nosso"] - precos2["preco_concorrente"]) / precos2["preco_concorrente"]
    precos2["mais_caro"] = precos2["nosso"] > precos2["preco_concorrente"]
    precos2["mais_barato"] = precos2["nosso"] < precos2["preco_concorrente"]

    by_competitor = (
        precos2.groupby("nome_concorrente")
        .agg(mais_caros=("mais_caro", "sum"), mais_baratos=("mais_barato", "sum"), gap_frac=("gap", "mean"))
        .reset_index()
        .sort_values("gap_frac", ascending=False)
    )

    return {
        "n_produtos": n_produtos,
        "gap_medio_frac": float(merged["gap_frac"].mean()) if n_produtos else 0.0,
        "n_acima_mercado": n_acima,
        "pct_acima_mercado": n_acima / n_produtos if n_produtos else 0.0,
        "n_lideres": n_lideres,
        "pct_lideres": n_lideres / n_produtos if n_produtos else 0.0,
        "categoria_alerta": categoria_alerta,
        "n_concorrentes": int(precos2["nome_concorrente"].nunique()),
        "by_category": by_category,
        "parity": parity,
        "by_competitor": by_competitor,
        "risk": risk,
    }


# ---------------------------------------------------------------------------
# Clientes & Comportamento
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300, show_spinner="Carregando clientes...")
def load_clientes() -> dict:
    clientes_rows = _fetch_all("clientes", "id_cliente,nome_cliente,estado,pais,data_cadastro")
    vendas_rows = _fetch_all(
        "vendas", "id_cliente,canal_venda,quantidade,preco_unitario,data_venda"
    )

    clientes = pd.DataFrame(clientes_rows)
    vendas = pd.DataFrame(vendas_rows)
    if clientes.empty or vendas.empty:
        return {}

    vendas["receita"] = vendas["quantidade"] * vendas["preco_unitario"]

    per_cliente = (
        vendas.groupby("id_cliente")
        .agg(receita=("receita", "sum"), compras=("receita", "count"))
        .reset_index()
    )

    canal_pivot = vendas.pivot_table(
        index="id_cliente", columns="canal_venda", values="receita", aggfunc="sum", fill_value=0
    ).reset_index()
    for c in ("ecommerce", "loja_fisica"):
        if c not in canal_pivot.columns:
            canal_pivot[c] = 0.0

    per_cliente = per_cliente.merge(canal_pivot, on="id_cliente", how="left")
    per_cliente["canal_preferido"] = per_cliente.apply(
        lambda r: "ecommerce" if r["ecommerce"] >= r["loja_fisica"] else "loja_fisica", axis=1
    )
    per_cliente["ticket_medio"] = per_cliente["receita"] / per_cliente["compras"]

    per_cliente = per_cliente.merge(
        clientes[["id_cliente", "nome_cliente", "estado"]], on="id_cliente", how="left"
    )
    per_cliente = per_cliente.sort_values("receita", ascending=False)

    receita_total = float(per_cliente["receita"].sum())
    receita_top10 = float(per_cliente.head(10)["receita"].sum())
    ticket_medio_geral = float(per_cliente["ticket_medio"].mean())
    frequencia_media = float(per_cliente["compras"].mean())

    por_estado = (
        per_cliente.groupby("estado")
        .agg(receita=("receita", "sum"), clientes=("id_cliente", "count"))
        .reset_index()
        .sort_values("receita", ascending=False)
    )

    por_canal = (
        vendas.groupby("canal_venda")
        .agg(receita=("receita", "sum"), transacoes=("receita", "count"))
        .reset_index()
    )

    canal_pref_counts = per_cliente["canal_preferido"].value_counts().to_dict()

    return {
        "total_clientes": len(clientes),
        "clientes_ativos": int(per_cliente["id_cliente"].nunique()),
        "receita_total": receita_total,
        "receita_media_cliente": receita_total / len(clientes) if len(clientes) else 0.0,
        "ticket_medio_geral": ticket_medio_geral,
        "frequencia_media": frequencia_media,
        "share_top10": receita_top10 / receita_total if receita_total else 0.0,
        "clientes": per_cliente,
        "top_clientes": per_cliente.head(10),
        "por_estado": por_estado,
        "por_canal": por_canal,
        "canal_preferido_counts": canal_pref_counts,
    }
