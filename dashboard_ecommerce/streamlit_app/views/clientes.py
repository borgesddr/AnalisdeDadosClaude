import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import plotly.graph_objects as go
import streamlit as st

from lib import data
from lib.format import format_brl, format_number, format_percent
from lib.theme import CHANNEL_COLORS, CHANNEL_LABELS, COLORS, apply_layout
from lib.ui import chart_card_header, kpi_card

st.title("Clientes & Comportamento")
st.caption("Quem são, quanto valem e como compram os clientes — período de 13/dez/2025 a 11/jan/2026.")

d = data.load_clientes()
if not d:
    st.error("Não foi possível carregar os dados de clientes.")
    st.stop()

# --- KPIs ---------------------------------------------------------------
row = st.columns(4)
kpi_card(
    row[0],
    "Clientes ativos",
    f"{d['clientes_ativos']} / {d['total_clientes']}",
    f"{format_percent(d['clientes_ativos'] / d['total_clientes'] if d['total_clientes'] else 0)} da base comprou no período",
)
kpi_card(row[1], "Receita média / cliente", format_brl(d["receita_media_cliente"]), f"Receita total {format_brl(d['receita_total'])}")
kpi_card(row[2], "Ticket médio", format_brl(d["ticket_medio_geral"]), f"Frequência média {d['frequencia_media']:.0f} compras/cliente")
kpi_card(row[3], "Concentração Top 10", format_percent(d["share_top10"]), "da receita vem dos 10 maiores clientes")

pref = d["canal_preferido_counts"]
ecom_pref = pref.get("ecommerce", 0)
total = d["total_clientes"]
with st.container(border=True):
    st.markdown(
        f"**Insight:** a base é pequena e {'totalmente ativa' if d['clientes_ativos'] == total else 'majoritariamente ativa'} — "
        f"{d['clientes_ativos']} dos {total} clientes compraram no período. A receita é pouco concentrada: os 10 maiores "
        f"respondem por {format_percent(d['share_top10'])} do total. O e-commerce domina: {ecom_pref} dos {total} "
        f"clientes têm o canal digital como preferido."
    )

st.write("")

# --- Distribuição geográfica + Top 10 clientes ---------------------------
col_a, col_b = st.columns(2)
with col_a:
    with st.container(border=True):
        chart_card_header("Distribuição geográfica", "Receita por estado (UF).")
        estados = d["por_estado"].sort_values("receita", ascending=True)
        fig = go.Figure(
            go.Bar(
                x=estados["receita"],
                y=estados["estado"],
                orientation="h",
                marker_color=COLORS["cyan"],
                hovertemplate="%{y}: R$ %{x:,.2f}<extra></extra>",
            )
        )
        fig.update_xaxes(tickprefix="R$ ", tickformat=",.0f")
        apply_layout(fig, height=380, showlegend=False)
        st.plotly_chart(fig, width="stretch")

with col_b:
    with st.container(border=True):
        top10 = d["top_clientes"]
        chart_card_header("Top 10 clientes por receita", f"Juntos representam {format_percent(d['share_top10'])} da receita total.")
        top_sorted = top10.sort_values("receita", ascending=True)
        colors = [COLORS["orange"] if i == len(top_sorted) - 1 else COLORS["navy"] for i in range(len(top_sorted))]
        fig = go.Figure(
            go.Bar(
                x=top_sorted["receita"],
                y=top_sorted["nome_cliente"],
                orientation="h",
                marker_color=colors,
                hovertemplate="%{y}: R$ %{x:,.2f}<extra></extra>",
            )
        )
        fig.update_xaxes(tickprefix="R$ ", tickformat=",.0f")
        apply_layout(fig, height=380, showlegend=False)
        st.plotly_chart(fig, width="stretch")

st.write("")

# --- Comportamento de compra + Mix de canal -------------------------------
col_c, col_d = st.columns(2)
with col_c:
    with st.container(border=True):
        chart_card_header(
            "Comportamento de compra",
            "Cada ponto é um cliente: frequência (compras) × ticket médio; o tamanho reflete a receita.",
        )
        clientes = d["clientes"]
        freq_media = clientes["compras"].mean()
        ticket_media = clientes["ticket_medio"].mean()
        colors = [
            COLORS["success"] if (f >= freq_media and t >= ticket_media) else COLORS["cyan400"]
            for f, t in zip(clientes["compras"], clientes["ticket_medio"])
        ]
        fig = go.Figure(
            go.Scatter(
                x=clientes["compras"],
                y=clientes["ticket_medio"],
                mode="markers",
                marker=dict(
                    color=colors,
                    size=(clientes["receita"] / clientes["receita"].max() * 30 + 6),
                    opacity=0.75,
                ),
                text=clientes["nome_cliente"],
                hovertemplate="%{text}<br>Compras: %{x}<br>Ticket médio: R$ %{y:,.2f}<extra></extra>",
            )
        )
        fig.update_xaxes(title="Frequência (nº de compras)")
        fig.update_yaxes(tickprefix="R$ ", tickformat=",.0f")
        apply_layout(fig, height=380, showlegend=False)
        st.plotly_chart(fig, width="stretch")

with col_d:
    with st.container(border=True):
        por_canal = d["por_canal"]
        chart_card_header(
            "Mix de canal",
            f"Receita por canal de venda. {ecom_pref} de {total} clientes preferem o e-commerce.",
        )
        fig = go.Figure(
            go.Pie(
                labels=[CHANNEL_LABELS.get(c, c) for c in por_canal["canal_venda"]],
                values=por_canal["receita"],
                hole=0.6,
                marker=dict(colors=[CHANNEL_COLORS.get(c, COLORS["neutral"]) for c in por_canal["canal_venda"]]),
                textinfo="percent",
            )
        )
        apply_layout(fig, height=380)
        st.plotly_chart(fig, width="stretch")
