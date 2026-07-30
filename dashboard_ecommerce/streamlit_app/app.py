import streamlit as st

st.set_page_config(
    page_title="Dashboard E-commerce · Keyrus",
    page_icon="📊",
    layout="wide",
)

vendas_page = st.Page("views/vendas.py", title="Vendas & Receita", icon="💰", default=True)
pricing_page = st.Page("views/pricing.py", title="Pricing & Margem", icon="🏷️")
clientes_page = st.Page("views/clientes.py", title="Clientes & Comportamento", icon="👥")

pg = st.navigation([vendas_page, pricing_page, clientes_page])

with st.sidebar:
    st.markdown(
        "<div style='padding:.5rem 0 1rem 0;'>"
        "<span style='color:#0B2265;font-weight:700;font-size:1.05rem;'>Dashboard E-commerce</span><br>"
        "<span style='color:#29ABE2;font-weight:600;'>Keyrus</span>"
        "</div>",
        unsafe_allow_html=True,
    )

pg.run()
