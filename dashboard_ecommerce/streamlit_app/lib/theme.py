"""Tokens de cor — espelham src/lib/theme.ts e DESIGN_SYSTEM.md do dashboard React."""

COLORS = {
    "navy": "#0B2265",
    "cyan": "#29ABE2",
    "cyan400": "#38BDF8",
    "orange": "#F5A623",
    "success": "#16A34A",
    "warning": "#F5A623",
    "danger": "#DC2626",
    "neutral": "#94A3B8",
    "border": "#E4E7EC",
    "text_muted": "#667085",
}

# Ordem e mapeamento fixos das 11 categorias de produto — mesmo índice/cor em toda a app.
CATEGORY_COLORS = {
    "Casa": "#0B2265",
    "Acessórios": "#29ABE2",
    "Moda": "#38BDF8",
    "Informática": "#16A34A",
    "Cozinha": "#F5A623",
    "Esporte": "#DC2626",
    "Games": "#7C3AED",
    "Áudio": "#EC4899",
    "Tênis": "#0EA5A4",
    "Eletrônicos": "#F97316",
    "Beleza": "#64748B",
}

CHANNEL_COLORS = {
    "ecommerce": "#29ABE2",
    "loja_fisica": "#0B2265",
}

CHANNEL_LABELS = {
    "ecommerce": "E-commerce",
    "loja_fisica": "Loja física",
}

SERIES_PALETTE = list(CATEGORY_COLORS.values())

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, system-ui, sans-serif", color=COLORS["text_muted"], size=12),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=10, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
)


def apply_layout(fig, **overrides):
    layout = {**PLOTLY_LAYOUT, **overrides}
    fig.update_layout(**layout)
    fig.update_xaxes(gridcolor=COLORS["border"], zeroline=False)
    fig.update_yaxes(gridcolor=COLORS["border"], zeroline=False)
    return fig
