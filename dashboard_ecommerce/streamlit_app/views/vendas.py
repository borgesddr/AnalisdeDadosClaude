import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib import data
from lib.format import format_brl, format_number, format_percent
from lib.theme import CATEGORY_COLORS, CHANNEL_COLORS, CHANNEL_LABELS, COLORS, apply_layout
from lib.ui import chart_card_header, kpi_card

st.title("Vendas & Receita")
st.caption("Desempenho comercial de 13/dez/2025 a 11/jan/2026 — receita, canais e os produtos que puxam o resultado.")

d = data.load_vendas()
if not d:
    st.error("Não foi possível carregar os dados de vendas.")
    st.stop()

# --- KPIs ---------------------------------------------------------------
row1 = st.columns(4)
kpi_card(row1[0], "Receita total", format_brl(d["receita_total"]))
kpi_card(row1[1], "Ticket médio", format_brl(d["ticket_medio"]))
kpi_card(row1[2], "Total de vendas", format_number(d["total_vendas"]), f"{format_number(d['itens_vendidos'])} itens vendidos")
kpi_card(row1[3], "Clientes ativos", format_number(d["clientes_ativos"]))

row2 = st.columns(4)
kpi_card(row2[0], "Receita e-commerce", format_percent(d["pct_ecommerce"]), "participação no faturamento")
cat_lider = d["categoria_lider"]
if cat_lider is not None:
    pct = cat_lider["receita"] / d["receita_total"] if d["receita_total"] else 0
    kpi_card(
        row2[1],
        "Categoria líder",
        cat_lider["categoria"],
        f"{format_brl(cat_lider['receita'])} · {format_percent(pct)}",
    )

st.write("")

# --- Evolução diária -----------------------------------------------------
with st.container(border=True):
    chart_card_header("Evolução diária da receita", "Faturamento diário no período analisado.")
    serie = d["serie_diaria"]
    fig = go.Figure(
        go.Scatter(
            x=serie["dia"],
            y=serie["receita"],
            mode="lines",
            fill="tozeroy",
            line=dict(color=COLORS["cyan"], width=2),
            fillcolor="rgba(41,171,226,0.15)",
            hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
        )
    )
    fig.update_yaxes(tickprefix="R$ ", tickformat=",.0f")
    apply_layout(fig, height=320, showlegend=False)
    st.plotly_chart(fig, width="stretch")

st.write("")

# --- Receita por canal -----------------------------------------------------
col_a, col_b = st.columns([1, 1])
with col_a:
    with st.container(border=True):
        canais = d["canais"]
        chart_card_header(
            "Receita por canal",
            f"O e-commerce responde por {format_percent(d['pct_ecommerce'])} da receita.",
        )
        fig = go.Figure(
            go.Pie(
                labels=[CHANNEL_LABELS.get(c, c) for c in canais["canal_venda"]],
                values=canais["receita"],
                hole=0.6,
                marker=dict(colors=[CHANNEL_COLORS.get(c, COLORS["neutral"]) for c in canais["canal_venda"]]),
                textinfo="percent",
            )
        )
        apply_layout(fig, height=300)
        st.plotly_chart(fig, width="stretch")

        for _, c in canais.iterrows():
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;padding:.4rem 0;"
                f"border-top:1px solid {COLORS['border']};'>"
                f"<span><span style='color:{CHANNEL_COLORS.get(c['canal_venda'])};'>●</span> "
                f"{CHANNEL_LABELS.get(c['canal_venda'], c['canal_venda'])}</span>"
                f"<b>{format_percent(c['pct_receita'])}</b></div>"
                f"<div style='font-size:.8rem;color:{COLORS['text_muted']};display:flex;justify-content:space-between;'>"
                f"<span>Receita: {format_brl(c['receita'])}</span>"
                f"<span>Ticket médio: {format_brl(c['ticket_medio'])}</span></div>",
                unsafe_allow_html=True,
            )

with col_b:
    with st.container(border=True):
        top_categorias = d["top_categorias"]
        lider = top_categorias.iloc[0]
        chart_card_header(
            "Receita por categoria",
            f"{lider['categoria']} lidera com {format_percent(lider['receita'] / d['receita_total'])} do faturamento.",
        )
        cats_sorted = top_categorias.sort_values("receita", ascending=True)
        fig = go.Figure(
            go.Bar(
                x=cats_sorted["receita"],
                y=cats_sorted["categoria"],
                orientation="h",
                marker_color=[CATEGORY_COLORS.get(c, COLORS["neutral"]) for c in cats_sorted["categoria"]],
                hovertemplate="%{y}: R$ %{x:,.2f}<extra></extra>",
            )
        )
        fig.update_xaxes(tickprefix="R$ ", tickformat=",.0f")
        apply_layout(fig, height=340, showlegend=False)
        st.plotly_chart(fig, width="stretch")

st.write("")

# --- Top 5 produtos -----------------------------------------------------
with st.container(border=True):
    chart_card_header(
        "Top 5 produtos por receita",
        "Poucos SKUs concentram boa parte do faturamento — atenção a estoque e disponibilidade.",
    )
    for i, (_, p) in enumerate(d["top_produtos"].iterrows(), start=1):
        pct = p["receita"] / d["top_produtos"]["receita"].max()
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;margin-top:.6rem;'>"
            f"<span><b>{i}. {p['nome_produto']}</b></span>"
            f"<b>{format_brl(p['receita'])}</b></div>"
            f"<div style='background:{COLORS['border']};border-radius:6px;height:8px;margin-top:.2rem;'>"
            f"<div style='background:{CATEGORY_COLORS.get(p['categoria'], COLORS['neutral'])};"
            f"width:{pct * 100:.1f}%;height:8px;border-radius:6px;'></div></div>"
            f"<div style='font-size:.8rem;color:{COLORS['text_muted']};'>{p['categoria']} · {format_number(p['itens'])} un.</div>",
            unsafe_allow_html=True,
        )
