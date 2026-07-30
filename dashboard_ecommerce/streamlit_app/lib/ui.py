"""Componentes visuais compartilhados entre as 3 páginas (equivalente aos KpiCard/ChartCard React)."""

import streamlit as st

from .theme import COLORS


def kpi_card(col, label: str, value: str, sub: str | None = None, value_color: str = COLORS["text_muted"]) -> None:
    with col:
        with st.container(border=True):
            st.markdown(
                f"<div style='font-size:.72rem;color:{COLORS['text_muted']};"
                f"text-transform:uppercase;letter-spacing:.06em;'>{label}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-size:1.9rem;font-weight:700;color:#1A1A1A;"
                f"line-height:1.2;margin-top:.15rem;'>{value}</div>",
                unsafe_allow_html=True,
            )
            if sub:
                st.markdown(
                    f"<div style='font-size:.8rem;color:{value_color};margin-top:.1rem;'>{sub}</div>",
                    unsafe_allow_html=True,
                )


def chart_card_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"<div style='font-size:1.05rem;font-weight:600;color:#1A1A1A;'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div style='font-size:.85rem;color:{COLORS['text_muted']};margin-bottom:.5rem;'>{subtitle}</div>", unsafe_allow_html=True)
