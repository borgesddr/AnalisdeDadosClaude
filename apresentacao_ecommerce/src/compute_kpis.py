"""ETAPA A: le os CSVs brutos em data/, calcula KPIs agregados e grava
arquivos JSON pequenos em output/kpis/. Nenhum outro script deve ler os
CSVs brutos -- a etapa de geracao do HTML consome apenas esses JSONs.
"""

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output" / "kpis"

TOP_N_BRANDS = 15
TOP_N_PRODUCTS = 15
TOP_N_CUSTOMERS = 15
TOP_N_OUTLIERS = 10


def load_data():
    clientes = pd.read_csv(DATA_DIR / "clientes.csv", parse_dates=["data_cadastro"])
    produtos = pd.read_csv(DATA_DIR / "produtos.csv", parse_dates=["data_criacao"])
    vendas = pd.read_csv(DATA_DIR / "vendas.csv", parse_dates=["data_venda"])
    competidores = pd.read_csv(DATA_DIR / "preco_competidores.csv", parse_dates=["data_coleta"])
    return {
        "clientes": clientes,
        "produtos": produtos,
        "vendas": vendas,
        "competidores": competidores,
    }


def build_joined_vendas(data):
    v = data["vendas"].copy()
    v["receita"] = v["quantidade"] * v["preco_unitario"]
    v = v.merge(
        data["clientes"][["id_cliente", "nome_cliente", "estado"]],
        on="id_cliente",
        how="left",
    )
    v = v.merge(
        data["produtos"][["id_produto", "nome_produto", "categoria", "marca", "preco_atual"]],
        on="id_produto",
        how="left",
    )
    return v


def write_json(obj, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def compute_meta(data):
    vendas = data["vendas"]
    return {
        "source_row_counts": {name: int(len(df)) for name, df in data.items()},
        "vendas_date_range": {
            "start": vendas["data_venda"].min().strftime("%Y-%m-%d"),
            "end": vendas["data_venda"].max().strftime("%Y-%m-%d"),
        },
        "categorias": sorted(data["produtos"]["categoria"].dropna().unique().tolist()),
        "canais": sorted(vendas["canal_venda"].dropna().unique().tolist()),
        "concorrentes": sorted(data["competidores"]["nome_concorrente"].dropna().unique().tolist()),
    }


def compute_overview(v, data):
    return {
        "total_revenue": round(float(v["receita"].sum()), 2),
        "total_orders": int(len(v)),
        "total_units": int(v["quantidade"].sum()),
        "avg_order_value": round(float(v["receita"].mean()), 2),
        "avg_unit_price": round(float(v["preco_unitario"].mean()), 2),
        "unique_customers_active": int(v["id_cliente"].nunique()),
        "unique_products_sold": int(v["id_produto"].nunique()),
        "total_customers_registered": int(len(data["clientes"])),
        "total_products_catalog": int(len(data["produtos"])),
        "date_range": {
            "start": v["data_venda"].min().strftime("%Y-%m-%d"),
            "end": v["data_venda"].max().strftime("%Y-%m-%d"),
        },
    }


def compute_revenue_trend_daily(v):
    daily = (
        v.assign(date=v["data_venda"].dt.strftime("%Y-%m-%d"))
        .groupby("date")
        .agg(revenue=("receita", "sum"), orders=("id_venda", "count"), units=("quantidade", "sum"))
        .reset_index()
        .sort_values("date")
    )
    daily["revenue"] = daily["revenue"].round(2)
    return daily.to_dict("records")


def compute_revenue_by_channel(v):
    total = v["receita"].sum()
    grp = (
        v.groupby("canal_venda")
        .agg(revenue=("receita", "sum"), orders=("id_venda", "count"), units=("quantidade", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    grp["share_pct"] = (grp["revenue"] / total * 100).round(1)
    grp["avg_ticket"] = (grp["revenue"] / grp["orders"]).round(2)
    grp["revenue"] = grp["revenue"].round(2)
    return grp.to_dict("records")


def compute_revenue_by_category(v):
    total = v["receita"].sum()
    grp = (
        v.groupby("categoria")
        .agg(
            revenue=("receita", "sum"),
            orders=("id_venda", "count"),
            units=("quantidade", "sum"),
            n_products_sold=("id_produto", "nunique"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    grp["share_pct"] = (grp["revenue"] / total * 100).round(1)
    grp["revenue"] = grp["revenue"].round(2)
    return grp.to_dict("records")


def compute_revenue_by_brand(v, top_n=TOP_N_BRANDS):
    total = v["receita"].sum()
    grp = (
        v.groupby("marca")
        .agg(revenue=("receita", "sum"), orders=("id_venda", "count"), units=("quantidade", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    top = grp.head(top_n).copy()
    rest = grp.iloc[top_n:]
    if len(rest) > 0:
        outras = pd.DataFrame(
            [{
                "marca": "Outras marcas",
                "revenue": rest["revenue"].sum(),
                "orders": rest["orders"].sum(),
                "units": rest["units"].sum(),
            }]
        )
        top = pd.concat([top, outras], ignore_index=True)
    top["share_pct"] = (top["revenue"] / total * 100).round(1)
    top["revenue"] = top["revenue"].round(2)
    return top.to_dict("records")


def compute_top_products(v, top_n=TOP_N_PRODUCTS):
    grp = (
        v.groupby(["id_produto", "nome_produto", "categoria", "marca"])
        .agg(
            revenue=("receita", "sum"),
            units=("quantidade", "sum"),
            orders=("id_venda", "count"),
            avg_price_realizado=("preco_unitario", "mean"),
            preco_atual=("preco_atual", "first"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(top_n)
    )
    grp["revenue"] = grp["revenue"].round(2)
    grp["avg_price_realizado"] = grp["avg_price_realizado"].round(2)
    grp["preco_atual"] = grp["preco_atual"].round(2)
    return grp.to_dict("records")


def compute_top_customers(v, top_n=TOP_N_CUSTOMERS):
    grp = (
        v.groupby(["id_cliente", "nome_cliente", "estado"])
        .agg(revenue=("receita", "sum"), orders=("id_venda", "count"), units=("quantidade", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(top_n)
    )
    grp["avg_ticket"] = (grp["revenue"] / grp["orders"]).round(2)
    grp["revenue"] = grp["revenue"].round(2)
    return grp.to_dict("records")


def compute_revenue_by_estado(v):
    total = v["receita"].sum()
    grp = (
        v.groupby("estado")
        .agg(
            revenue=("receita", "sum"),
            orders=("id_venda", "count"),
            units=("quantidade", "sum"),
            customers_active=("id_cliente", "nunique"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    grp["share_pct"] = (grp["revenue"] / total * 100).round(1)
    grp["revenue"] = grp["revenue"].round(2)
    return grp.to_dict("records")


def compute_customer_growth(clientes, v):
    c = clientes.copy()
    c["month"] = c["data_cadastro"].dt.strftime("%Y-%m")
    monthly = (
        c.groupby("month")
        .size()
        .reset_index(name="new_customers")
        .sort_values("month")
    )
    monthly["cumulative_customers"] = monthly["new_customers"].cumsum()
    return {
        "monthly": monthly.to_dict("records"),
        "active_in_period": int(v["id_cliente"].nunique()),
        "total_customers": int(len(clientes)),
        "activation_rate_pct": round(v["id_cliente"].nunique() / len(clientes) * 100, 1),
    }


def compute_competitive_pricing(produtos, vendas, competidores):
    nosso_preco = vendas.groupby("id_produto")["preco_unitario"].mean()
    nosso_preco = nosso_preco.reindex(produtos["id_produto"])
    nosso_preco = nosso_preco.fillna(
        produtos.set_index("id_produto")["preco_atual"]
    )

    comp_por_produto_concorrente = (
        competidores.groupby(["id_produto", "nome_concorrente"])["preco_concorrente"]
        .mean()
        .reset_index()
    )
    comp_por_produto_concorrente["nosso_preco"] = comp_por_produto_concorrente["id_produto"].map(nosso_preco)
    comp_por_produto_concorrente["diff_pct"] = (
        (comp_por_produto_concorrente["nosso_preco"] - comp_por_produto_concorrente["preco_concorrente"])
        / comp_por_produto_concorrente["preco_concorrente"]
        * 100
    )

    summary_rows = []
    for concorrente, grupo in comp_por_produto_concorrente.groupby("nome_concorrente"):
        summary_rows.append({
            "nome_concorrente": concorrente,
            "n_products_compared": int(len(grupo)),
            "avg_our_price": round(float(grupo["nosso_preco"].mean()), 2),
            "avg_competitor_price": round(float(grupo["preco_concorrente"].mean()), 2),
            "avg_diff_pct": round(float(grupo["diff_pct"].mean()), 1),
            "median_diff_pct": round(float(grupo["diff_pct"].median()), 1),
            "pct_we_are_cheaper": round(float((grupo["diff_pct"] < 0).mean() * 100), 1),
            "pct_we_are_more_expensive": round(float((grupo["diff_pct"] > 0).mean() * 100), 1),
        })
    summary_rows.sort(key=lambda r: r["nome_concorrente"])

    comp_por_produto = (
        competidores.groupby("id_produto")["preco_concorrente"]
        .mean()
        .reset_index()
        .rename(columns={"preco_concorrente": "preco_concorrente_medio"})
    )
    comp_por_produto = comp_por_produto.merge(
        produtos[["id_produto", "nome_produto", "categoria"]], on="id_produto", how="left"
    )
    comp_por_produto["nosso_preco"] = comp_por_produto["id_produto"].map(nosso_preco)
    comp_por_produto["diff_pct"] = (
        (comp_por_produto["nosso_preco"] - comp_por_produto["preco_concorrente_medio"])
        / comp_por_produto["preco_concorrente_medio"]
        * 100
    ).round(1)
    comp_por_produto["nosso_preco"] = comp_por_produto["nosso_preco"].round(2)
    comp_por_produto["preco_concorrente_medio"] = comp_por_produto["preco_concorrente_medio"].round(2)

    ordenado = comp_por_produto.sort_values("diff_pct", ascending=False)
    outliers = {
        "most_overpriced": ordenado.head(TOP_N_OUTLIERS).to_dict("records"),
        "most_underpriced": ordenado.tail(TOP_N_OUTLIERS).sort_values("diff_pct").to_dict("records"),
    }
    return summary_rows, outliers


def main():
    data = load_data()
    v = build_joined_vendas(data)

    outputs = {
        "meta.json": compute_meta(data),
        "overview.json": compute_overview(v, data),
        "revenue_trend_daily.json": compute_revenue_trend_daily(v),
        "revenue_by_channel.json": compute_revenue_by_channel(v),
        "revenue_by_category.json": compute_revenue_by_category(v),
        "revenue_by_brand.json": compute_revenue_by_brand(v),
        "top_products.json": compute_top_products(v),
        "top_customers.json": compute_top_customers(v),
        "revenue_by_estado.json": compute_revenue_by_estado(v),
        "customer_growth.json": compute_customer_growth(data["clientes"], v),
    }

    summary_rows, outliers = compute_competitive_pricing(
        data["produtos"], data["vendas"], data["competidores"]
    )
    outputs["competitive_pricing_summary.json"] = summary_rows
    outputs["competitive_pricing_outliers.json"] = outliers

    for filename, obj in outputs.items():
        path = write_json(obj, filename)
        print(f"{path.name}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
