import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import plotly.graph_objects as go
import streamlit as st

from lib import data
from lib.format import format_brl, format_number, format_percent
from lib.theme import COLORS, apply_layout
from lib.ui import chart_card_header, kpi_card

st.title("Pricing & Margem")
st.caption("Posicionamento competitivo dos nossos preços frente aos marketplaces concorrentes.")

d = data.load_pricing()
if not d:
    st.error("Não foi possível carregar os dados de pricing.")
    st.stop()

categoria_alerta = d["categoria_alerta"]

# --- KPIs ---------------------------------------------------------------
row = st.columns(4)
gap = d["gap_medio_frac"]
kpi_card(
    row[0],
    "Gap médio vs mercado",
    f"+{format_percent(gap)}" if gap >= 0 else f"-{format_percent(-gap)}",
    "Nosso preço vs média dos concorrentes",
    value_color=COLORS["danger"] if gap > 0 else COLORS["success"],
)
kpi_card(
    row[1],
    "Acima do mercado",
    format_percent(d["pct_acima_mercado"]),
    f"{format_number(d['n_acima_mercado'])} de {format_number(d['n_produtos'])} produtos mais caros que a média",
    value_color=COLORS["warning"],
)
kpi_card(
    row[2],
    "Líderes de preço",
    format_number(d["n_lideres"]),
    f"{format_percent(d['pct_lideres'])} igualam ou batem o menor concorrente",
    value_color=COLORS["success"],
)
if categoria_alerta is not None:
    kpi_card(
        row[3],
        "Categoria em alerta",
        categoria_alerta["categoria"],
        f"Gap médio de {'+' if categoria_alerta['gap_frac'] >= 0 else ''}{format_percent(categoria_alerta['gap_frac'])} vs mercado",
        value_color=COLORS["danger"],
    )

with st.container(border=True):
    st.markdown(
        f"Na média, praticamos preços **{format_percent(abs(gap))} {'acima' if gap > 0 else 'abaixo'}** "
        f"dos {d['n_concorrentes']} marketplaces monitorados, e **{d['n_acima_mercado']}** dos "
        f"**{d['n_produtos']}** produtos estão mais caros que a média do mercado. "
        + (
            f"O ofensor é claro: a categoria **{categoria_alerta['categoria']}** está "
            f"{'+' if categoria_alerta['gap_frac'] >= 0 else ''}{format_percent(categoria_alerta['gap_frac'])} acima dos concorrentes. "
            if categoria_alerta is not None
            else ""
        )
        + f"Fora dela, o portfólio fica próximo da paridade, com **{d['n_lideres']}** produtos liderando em preço."
    )

st.write("")

# --- Posicionamento por categoria + Paridade de preços -------------------
col_a, col_b = st.columns(2)
with col_a:
    with st.container(border=True):
        chart_card_header(
            "Posicionamento por categoria",
            "Gap médio de preço vs média dos concorrentes. Verde = mais baratos (bom); vermelho = mais caros.",
        )
        by_cat = d["by_category"].sort_values("gap_frac", ascending=True)
        colors = [COLORS["danger"] if g > 0 else COLORS["success"] for g in by_cat["gap_frac"]]
        fig = go.Figure(
            go.Bar(
                x=by_cat["gap_frac"] * 100,
                y=by_cat["categoria"],
                orientation="h",
                marker_color=colors,
                hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
            )
        )
        fig.update_xaxes(ticksuffix="%")
        fig.add_vline(x=0, line_color=COLORS["text_muted"])
        apply_layout(fig, height=340, showlegend=False)
        st.plotly_chart(fig, width="stretch")

with col_b:
    with st.container(border=True):
        chart_card_header(
            "Paridade de preços",
            "Cada ponto é um produto. Acima da linha tracejada = preço acima da média do mercado.",
        )
        parity = d["parity"]
        colors = [COLORS["danger"] if p > a else COLORS["success"] for p, a in zip(parity["preco_atual"], parity["avg_comp"])]
        max_v = max(parity["preco_atual"].max(), parity["avg_comp"].max())
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=parity["avg_comp"],
                y=parity["preco_atual"],
                mode="markers",
                marker=dict(color=colors, size=7, opacity=0.75),
                text=parity["nome_produto"],
                hovertemplate="%{text}<br>Concorrentes: R$ %{x:,.2f}<br>Nosso: R$ %{y:,.2f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[0, max_v],
                y=[0, max_v],
                mode="lines",
                line=dict(color=COLORS["text_muted"], dash="dash", width=1),
                hoverinfo="skip",
            )
        )
        fig.update_xaxes(tickprefix="R$ ", tickformat=",.0f")
        fig.update_yaxes(tickprefix="R$ ", tickformat=",.0f")
        apply_layout(fig, height=340, showlegend=False)
        st.plotly_chart(fig, width="stretch")

st.write("")

# --- Posição vs concorrente + Risco de competitividade --------------------
col_c, col_d = st.columns(2)
with col_c:
    with st.container(border=True):
        chart_card_header(
            "Posição frente a cada concorrente",
            "Em quantas comparações somos mais caros (vermelho) ou mais baratos (verde) que cada marketplace.",
        )
        by_comp = d["by_competitor"]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Somos mais baratos", x=by_comp["nome_concorrente"], y=by_comp["mais_baratos"], marker_color=COLORS["success"]))
        fig.add_trace(go.Bar(name="Somos mais caros", x=by_comp["nome_concorrente"], y=by_comp["mais_caros"], marker_color=COLORS["danger"]))
        fig.update_layout(barmode="stack")
        apply_layout(fig, height=340, showlegend=True)
        st.plotly_chart(fig, width="stretch")

with col_d:
    with st.container(border=True):
        chart_card_header(
            "Produtos com maior risco de competitividade",
            "Maior sobrepreço vs o menor concorrente disponível — candidatos prioritários a reprecificação.",
        )
        risk = d["risk"].sort_values("sobrepreco_frac", ascending=True)
        fig = go.Figure(
            go.Bar(
                x=risk["sobrepreco_frac"] * 100,
                y=risk["nome_produto"],
                orientation="h",
                marker_color=COLORS["danger"],
                hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
            )
        )
        fig.update_xaxes(ticksuffix="%")
        apply_layout(fig, height=340, showlegend=False)
        st.plotly_chart(fig, width="stretch")
