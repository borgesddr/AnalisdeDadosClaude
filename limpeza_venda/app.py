"""App Streamlit: o usuário envia um CSV/Excel de pedidos de venda, o app
aplica a limpeza automática (limpeza.py) e os testes de qualidade
(validador.py) — as mesmas regras usadas por corrigir_planilha.py e
testar_correcoes.py — e permite baixar o resultado em CSV ou Excel.
"""

import io

import pandas as pd
import streamlit as st

from limpeza import COLUNAS_ESPERADAS, limpar_planilha
from validador import resumir_resultados, validar_planilha

st.set_page_config(page_title="Limpeza de Planilha de Vendas", page_icon="🧹", layout="wide")

st.title("🧹 Limpeza automática de planilhas de pedidos de venda")
st.write(
    "Envie o CSV (ou Excel) de pedidos de venda. O app roda automaticamente as mesmas regras "
    "de limpeza de `limpeza.py` e os mesmos testes de qualidade de `validador.py` usados nos "
    "scripts `corrigir_planilha.py` e `testar_correcoes.py`."
)

with st.expander("Colunas esperadas no arquivo"):
    st.code("\n".join(COLUNAS_ESPERADAS))
    st.caption("Colunas ausentes não travam o processamento: as etapas que dependem delas são apenas puladas.")

arquivo = st.file_uploader("Arquivo de pedidos", type=["csv", "xlsx"])

if arquivo is None:
    st.info("Envie um arquivo para começar.")
    st.stop()


def carregar_arquivo(arquivo):
    nome = arquivo.name.lower()
    if nome.endswith(".xlsx"):
        return pd.read_excel(arquivo)
    ultimo_erro = None
    for encoding in ("utf-8-sig", "utf-8", "latin1"):
        try:
            arquivo.seek(0)
            return pd.read_csv(arquivo, sep=None, engine="python", encoding=encoding)
        except (UnicodeDecodeError, pd.errors.ParserError) as e:
            ultimo_erro = e
    raise ValueError(f"não foi possível ler o CSV (encoding/separador não reconhecido): {ultimo_erro}")


try:
    df_original = carregar_arquivo(arquivo)
except Exception as e:
    st.error(f"Erro ao ler o arquivo: {e}")
    st.stop()

if df_original.empty:
    st.warning("O arquivo enviado está vazio.")
    st.stop()

colunas_faltando = [c for c in COLUNAS_ESPERADAS if c not in df_original.columns]
if colunas_faltando:
    st.warning(
        "Colunas não encontradas (as etapas que dependem delas serão puladas): " + ", ".join(colunas_faltando)
    )

st.subheader("1. Prévia dos dados originais")
st.caption(f"{len(df_original)} linhas, {len(df_original.columns)} colunas")
st.dataframe(df_original.head(10), width="stretch")

with st.spinner("Limpando dados..."):
    df_limpo, log_df, resumo = limpar_planilha(df_original)

with st.spinner("Validando qualidade dos dados..."):
    resultados = validar_planilha(df_limpo)
    resumo_testes = resumir_resultados(resultados)

st.subheader("2. Resumo da limpeza")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Linhas processadas", resumo["linhas_originais"])
c2.metric("Duplicatas exatas removidas", resumo["duplicatas_exatas_removidas"])
c3.metric("Total de correções aplicadas", resumo["total_correcoes"])
c4.metric("Linhas finais", resumo["linhas_finais"])

c5, c6, c7 = st.columns(3)
c5.metric("Capitalização padronizada", resumo["capitalizacao_padronizada"])
c6.metric("Status corrigidos", resumo["status_corrigidos"])
c7.metric("Receitas convertidas p/ número", resumo["receitas_convertidas"])

if resumo["total_correcoes"] == 0:
    st.success("Nenhuma inconsistência encontrada — os dados já estavam limpos.")
else:
    st.info(f"{resumo['total_correcoes']} inconsistência(s) encontrada(s) e corrigida(s) automaticamente.")

st.subheader("3. Testes de qualidade (pós-limpeza)")
st.metric("Testes aprovados", f"{resumo_testes['aprovados']}/{resumo_testes['total']}")

if resumo_testes["reprovados"] == 0:
    st.success("Todos os testes de qualidade passaram — a planilha está consistente.")
else:
    st.error(f"{resumo_testes['reprovados']} teste(s) de qualidade falharam. Veja os detalhes abaixo.")

with st.expander("Ver detalhes dos testes de qualidade", expanded=resumo_testes["reprovados"] > 0):
    for nome, ok, detalhe in resultados:
        icone = "✅" if ok else "❌"
        linha = f"{icone} {nome}"
        if not ok and detalhe:
            linha += f" — {detalhe}"
        st.markdown(linha)

with st.expander(f"Ver log de correções ({len(log_df)} alterações)"):
    st.dataframe(log_df, width="stretch")

st.subheader("4. Prévia dos dados limpos")
st.dataframe(df_limpo.head(20), width="stretch")

st.subheader("5. Baixar planilha limpa")

csv_bytes = df_limpo.to_csv(index=False).encode("utf-8-sig")

buffer_excel = io.BytesIO()
with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
    df_limpo.to_excel(writer, sheet_name="dados_limpos", index=False)
    log_df.to_excel(writer, sheet_name="log_correcoes", index=False)
    pd.DataFrame(
        [{"Teste": nome, "Resultado": "PASS" if ok else "FALHA", "Detalhe": detalhe} for nome, ok, detalhe in resultados]
    ).to_excel(writer, sheet_name="validacao", index=False)
buffer_excel.seek(0)

col_a, col_b = st.columns(2)
col_a.download_button(
    "⬇️ Baixar CSV",
    data=csv_bytes,
    file_name="planilha_vendas_limpa.csv",
    mime="text/csv",
    width="stretch",
)
col_b.download_button(
    "⬇️ Baixar Excel",
    data=buffer_excel,
    file_name="planilha_vendas_limpa.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    width="stretch",
)
