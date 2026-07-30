"""ETAPA B (parte 2): monta o relatorio HTML final a partir dos JSONs de
KPI em output/kpis/. Nao importa pandas nem le data/*.csv -- consome
apenas os arquivos pequenos que a Etapa A (compute_kpis.py) gerou.
"""

import base64
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from src import charts
from src.formatting import format_brl, format_date_br, format_number, format_pct

BASE_DIR = Path(__file__).resolve().parent.parent
KPI_DIR = BASE_DIR / "output" / "kpis"
OUTPUT_HTML = BASE_DIR / "output" / "report.html"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
LOGO_PATH = BASE_DIR / "assets" / "Keyrus_AI_Original.png"

KPI_NAMES = [
    "meta", "overview", "revenue_trend_daily", "revenue_by_channel",
    "revenue_by_category", "revenue_by_brand", "top_products", "top_customers",
    "revenue_by_estado", "customer_growth", "competitive_pricing_summary",
    "competitive_pricing_outliers",
]


def load_kpi(name):
    path = KPI_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_all_kpis():
    return {name: load_kpi(name) for name in KPI_NAMES}


def load_logo_data_uri():
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def build_charts(kpis):
    blocks = {}

    blocks["revenue_trend"] = charts.chart_figure(
        "Receita ao Longo do Tempo",
        "Receita diaria no periodo analisado",
        charts.line_chart(
            [{"x_label": format_date_br(d["date"])[:5], "y": d["revenue"]} for d in kpis["revenue_trend_daily"]],
            title="Receita diaria",
        ),
        charts.render_table(
            ["Data", "Receita", "Pedidos", "Unidades"],
            [[format_date_br(d["date"]), format_brl(d["revenue"]), d["orders"], d["units"]] for d in kpis["revenue_trend_daily"]],
        ),
    )

    channel = kpis["revenue_by_channel"]
    channel_labels = {"ecommerce": "E-commerce", "loja_fisica": "Loja Fisica"}
    blocks["channel"] = charts.chart_figure(
        "Receita por Canal",
        "Participacao de cada canal de venda na receita total",
        charts.stacked_bar_100pct(
            [{"label": channel_labels.get(c["canal_venda"], c["canal_venda"]), "value": c["revenue"],
              "color": charts.CHANNEL_COLORS.get(c["canal_venda"], charts.HUE_DEFAULT)} for c in channel],
            title="Receita por canal",
        ),
        charts.render_table(
            ["Canal", "Receita", "Pedidos", "Participacao", "Ticket Medio"],
            [[channel_labels.get(c["canal_venda"], c["canal_venda"]), format_brl(c["revenue"]), c["orders"],
              format_pct(c["share_pct"], 0, signed=False), format_brl(c["avg_ticket"])] for c in channel],
        ),
        charts.legend([(channel_labels.get(c["canal_venda"], c["canal_venda"]),
                        charts.CHANNEL_COLORS.get(c["canal_venda"], charts.HUE_DEFAULT)) for c in channel]),
    )

    growth = kpis["customer_growth"]["monthly"]
    blocks["customer_growth"] = charts.chart_figure(
        "Crescimento da Base de Clientes",
        "Total acumulado de clientes cadastrados por mes",
        charts.line_chart(
            [{"x_label": m["month"][2:], "y": m["cumulative_customers"]} for m in growth],
            title="Clientes acumulados",
            value_fmt=lambda v, d=0: format_number(v, d),
            label_every=max(1, len(growth) // 8),
        ),
        charts.render_table(
            ["Mes", "Novos Clientes", "Acumulado"],
            [[m["month"], m["new_customers"], m["cumulative_customers"]] for m in growth],
        ),
    )

    category = kpis["revenue_by_category"]
    blocks["category"] = charts.chart_figure(
        "Receita por Categoria",
        "Categorias de produto ordenadas por receita",
        charts.bar_chart_h([{"label": c["categoria"], "value": c["revenue"]} for c in category], title="Receita por categoria"),
        charts.render_table(
            ["Categoria", "Receita", "Participacao", "Pedidos", "Produtos Vendidos"],
            [[c["categoria"], format_brl(c["revenue"]), format_pct(c["share_pct"], 0, signed=False), c["orders"], c["n_products_sold"]] for c in category],
        ),
    )

    brand = kpis["revenue_by_brand"]
    blocks["brand"] = charts.chart_figure(
        "Receita por Marca",
        "Top marcas por receita (demais agregadas em 'Outras marcas')",
        charts.bar_chart_h([{"label": b["marca"], "value": b["revenue"]} for b in brand], title="Receita por marca"),
        charts.render_table(
            ["Marca", "Receita", "Participacao", "Pedidos"],
            [[b["marca"], format_brl(b["revenue"]), format_pct(b["share_pct"], 0, signed=False), b["orders"]] for b in brand],
        ),
    )

    estado = kpis["revenue_by_estado"]
    blocks["estado"] = charts.chart_figure(
        "Receita por Estado",
        "Distribuicao geografica da receita por UF",
        charts.bar_chart_h([{"label": e["estado"], "value": e["revenue"]} for e in estado], title="Receita por estado"),
        charts.render_table(
            ["Estado", "Receita", "Participacao", "Clientes Ativos"],
            [[e["estado"], format_brl(e["revenue"]), format_pct(e["share_pct"], 0, signed=False), e["customers_active"]] for e in estado],
        ),
    )

    top_products = kpis["top_products"]
    blocks["top_products"] = charts.chart_figure(
        "Top Produtos",
        "Produtos com maior receita no periodo",
        charts.bar_chart_h([{"label": p["nome_produto"], "value": p["revenue"]} for p in top_products], title="Top produtos"),
        charts.render_table(
            ["Produto", "Categoria", "Marca", "Receita", "Unidades"],
            [[p["nome_produto"], p["categoria"], p["marca"], format_brl(p["revenue"]), p["units"]] for p in top_products],
        ),
    )

    top_customers = kpis["top_customers"]
    blocks["top_customers"] = charts.chart_figure(
        "Top Clientes",
        "Clientes com maior receita no periodo",
        charts.bar_chart_h([{"label": c["nome_cliente"], "value": c["revenue"]} for c in top_customers], title="Top clientes"),
        charts.render_table(
            ["Cliente", "Estado", "Receita", "Pedidos", "Ticket Medio"],
            [[c["nome_cliente"], c["estado"], format_brl(c["revenue"]), c["orders"], format_brl(c["avg_ticket"])] for c in top_customers],
        ),
    )

    summary = kpis["competitive_pricing_summary"]
    blocks["competitive_summary"] = charts.chart_figure(
        "Nosso Preco vs. Concorrencia",
        "Diferenca media percentual do nosso preco em relacao a cada concorrente (negativo = mais barato)",
        charts.diverging_bar_h([{"label": s["nome_concorrente"], "value_pct": s["avg_diff_pct"]} for s in summary], title="Diferenca de preco por concorrente"),
        charts.render_table(
            ["Concorrente", "Diferenca Media", "% Mais Barato", "% Mais Caro", "Produtos Comparados"],
            [[s["nome_concorrente"], format_pct(s["avg_diff_pct"]), format_pct(s["pct_we_are_cheaper"], 0, signed=False),
              format_pct(s["pct_we_are_more_expensive"], 0, signed=False), s["n_products_compared"]] for s in summary],
        ),
    )

    outliers = kpis["competitive_pricing_outliers"]
    blocks["outliers_overpriced"] = charts.chart_figure(
        "Produtos Mais Caros que a Concorrencia",
        "Maior diferenca percentual positiva vs. preco medio dos concorrentes",
        charts.diverging_bar_h([{"label": p["nome_produto"], "value_pct": p["diff_pct"]} for p in outliers["most_overpriced"]], title="Produtos mais caros"),
        charts.render_table(
            ["Produto", "Categoria", "Nosso Preco", "Preco Concorrencia", "Diferenca"],
            [[p["nome_produto"], p["categoria"], format_brl(p["nosso_preco"]), format_brl(p["preco_concorrente_medio"]), format_pct(p["diff_pct"])] for p in outliers["most_overpriced"]],
        ),
    )
    blocks["outliers_underpriced"] = charts.chart_figure(
        "Produtos Mais Baratos que a Concorrencia",
        "Maior diferenca percentual negativa vs. preco medio dos concorrentes",
        charts.diverging_bar_h([{"label": p["nome_produto"], "value_pct": p["diff_pct"]} for p in outliers["most_underpriced"]], title="Produtos mais baratos"),
        charts.render_table(
            ["Produto", "Categoria", "Nosso Preco", "Preco Concorrencia", "Diferenca"],
            [[p["nome_produto"], p["categoria"], format_brl(p["nosso_preco"]), format_brl(p["preco_concorrente_medio"]), format_pct(p["diff_pct"])] for p in outliers["most_underpriced"]],
        ),
    )

    return {key: Markup(html) for key, html in blocks.items()}


def build_environment():
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["brl"] = format_brl
    env.filters["pct"] = format_pct
    env.filters["num"] = format_number
    env.filters["date_br"] = format_date_br
    return env


def render(kpis, chart_blocks, logo_data_uri):
    env = build_environment()
    template = env.get_template("report.html.j2")
    return template.render(kpis=kpis, charts=chart_blocks, logo_data_uri=logo_data_uri)


def main():
    kpis = load_all_kpis()
    chart_blocks = build_charts(kpis)
    logo_data_uri = load_logo_data_uri()
    html = render(kpis, chart_blocks, logo_data_uri)
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    size_kb = OUTPUT_HTML.stat().st_size / 1024
    print(f"{OUTPUT_HTML}: {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
