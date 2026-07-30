"""Regras genéricas de limpeza para planilhas de pedidos de venda.

Não dependem de nenhum ID de pedido específico: qualquer planilha com as
mesmas colunas de data/planilha_vendas.xlsx pode ser processada. Reutilizado
por corrigir_planilha.py (linha de comando) e por app.py (Streamlit).
"""

import re

import pandas as pd

COLUNAS_ESPERADAS = [
    "ID Pedido",
    "Nome do Cliente",
    "Região",
    "Representante",
    "Data do Pedido",
    "Receita",
    "Produto",
    "Status",
    "Observações",
]

COLUNAS_TEXTO_LIVRE = ["Nome do Cliente", "Região", "Representante"]
COLUNAS_CRITICAS_PARA_ANOTACAO = ["Região", "Representante", "Receita"]

STATUS_SINONIMOS = {
    "fechado ganho": "Fechado Ganho",
    "ganho": "Fechado Ganho",
    "closed won": "Fechado Ganho",
    "won": "Fechado Ganho",
    "fechado perdido": "Fechado Perdido",
    "perdido": "Fechado Perdido",
    "closed lost": "Fechado Perdido",
    "lost": "Fechado Perdido",
}

CHAVE_NEGOCIO_COLUNAS = ["Nome do Cliente", "Região", "Representante", "Produto", "Status", "Receita"]


def padronizar_texto(valor):
    if pd.isna(valor):
        return valor
    return str(valor).strip().title()


def padronizar_status(valor):
    if pd.isna(valor):
        return valor
    chave = str(valor).strip().lower()
    return STATUS_SINONIMOS.get(chave, str(valor).strip().title())


def limpar_valor_monetario(valor):
    """Converte texto como 'R$ 1.234,56' ou 'R$ 1234.56' em float."""
    if pd.isna(valor):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = re.sub(r"[^\d,.\-]", "", str(valor)).strip()
    if not texto:
        return None
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _identificador(df, idx):
    return df.at[idx, "ID Pedido"] if "ID Pedido" in df.columns else idx


def _chave_negocio(row, colunas, incluir_data, coluna_data):
    partes = [str(row.get(c, "")).strip().lower() for c in colunas]
    if incluir_data and coluna_data:
        partes.append(str(row.get(coluna_data, "")))
    return "|".join(partes)


class RegistroLog(list):
    def registrar(self, id_pedido, campo, valor_antigo, valor_novo, motivo):
        self.append(
            {
                "ID Pedido": id_pedido,
                "Campo": campo,
                "Valor Antigo": valor_antigo,
                "Valor Novo": valor_novo,
                "Motivo": motivo,
            }
        )


def limpar_planilha(df_original):
    """Aplica as regras de limpeza e devolve (df_limpo, log_df, resumo)."""
    df = df_original.copy()
    log = RegistroLog()
    colunas_negocio = [c for c in CHAVE_NEGOCIO_COLUNAS if c in df.columns]
    coluna_data = "Data do Pedido" if "Data do Pedido" in df.columns else None

    if coluna_data:
        df[coluna_data] = pd.to_datetime(df[coluna_data], errors="coerce", dayfirst=False)

    # 1) status extraviado na coluna Observações
    if "Status" in df.columns and "Observações" in df.columns:
        mascara = df["Status"].isna() & df["Observações"].notna()
        for idx in df[mascara].index:
            texto_obs = str(df.at[idx, "Observações"]).strip().lower()
            if texto_obs in STATUS_SINONIMOS:
                status_corrigido = STATUS_SINONIMOS[texto_obs]
                log.registrar(_identificador(df, idx), "Status", None, status_corrigido,
                               "status estava lançado na coluna Observações")
                log.registrar(_identificador(df, idx), "Observações", df.at[idx, "Observações"], None,
                               "valor movido para a coluna Status")
                df.at[idx, "Status"] = status_corrigido
                df.at[idx, "Observações"] = None

    # 2) padronizar capitalização de texto livre
    for col in COLUNAS_TEXTO_LIVRE:
        if col not in df.columns:
            continue
        for idx in df.index:
            antigo = df.at[idx, col]
            novo = padronizar_texto(antigo)
            if pd.notna(antigo) and novo != antigo:
                log.registrar(_identificador(df, idx), col, antigo, novo, "padronização de capitalização")
        df[col] = df[col].apply(padronizar_texto)

    # 3) padronizar status
    if "Status" in df.columns:
        for idx in df.index:
            antigo = df.at[idx, "Status"]
            novo = padronizar_status(antigo)
            if pd.notna(antigo) and novo != antigo:
                log.registrar(_identificador(df, idx), "Status", antigo, novo, "padronização de status")
        df["Status"] = df["Status"].apply(padronizar_status)

    # 4) receita numérica
    if "Receita" in df.columns:
        for idx in df.index:
            antigo = df.at[idx, "Receita"]
            if pd.notna(antigo):
                novo = limpar_valor_monetario(antigo)
                if novo != antigo:
                    log.registrar(_identificador(df, idx), "Receita", antigo, novo, "conversão de texto para número")
        df["Receita"] = df["Receita"].apply(limpar_valor_monetario)

    # 5) anotar dados críticos faltantes sem observação
    if "Observações" in df.columns:
        for idx in df.index:
            if pd.notna(df.at[idx, "Observações"]):
                continue
            faltantes = [c for c in COLUNAS_CRITICAS_PARA_ANOTACAO if c in df.columns and pd.isna(df.at[idx, c])]
            if faltantes:
                nota = "; ".join(f"{c.lower()} ausente" for c in faltantes)
                log.registrar(_identificador(df, idx), "Observações", None, nota, "sinaliza dado crítico faltante")
                df.at[idx, "Observações"] = nota

    # 6) duplicatas exatas (mesmo cliente/região/representante/produto/status/valor/data) -> remover
    if colunas_negocio:
        chave_exata = df.apply(
            lambda r: _chave_negocio(r, colunas_negocio, incluir_data=True, coluna_data=coluna_data), axis=1
        )
        primeira_ocorrencia = {}
        manter = []
        for idx, chave in chave_exata.items():
            if chave not in primeira_ocorrencia:
                primeira_ocorrencia[chave] = _identificador(df, idx)
                manter.append(True)
            else:
                log.registrar(_identificador(df, idx), "linha inteira",
                               f"duplicata do pedido {primeira_ocorrencia[chave]}", "removida",
                               "duplicata exata (mesmo cliente/região/representante/produto/status/valor/data)")
                manter.append(False)
        df = df.loc[chave_exata.index[manter]].copy()

    # 7) possíveis duplicados (mesmo perfil, data diferente) -> sinalizar
    if colunas_negocio and "Observações" in df.columns:
        chave_perfil = df.apply(
            lambda r: _chave_negocio(r, colunas_negocio, incluir_data=False, coluna_data=None), axis=1
        )
        df = df.assign(_chave_perfil=chave_perfil)
        for _, grupo in df.groupby("_chave_perfil"):
            if len(grupo) < 2:
                continue
            grupo_ordenado = grupo.sort_values(coluna_data) if coluna_data else grupo
            for idx in grupo_ordenado.index[1:]:
                if pd.isna(df.at[idx, "Observações"]):
                    log.registrar(_identificador(df, idx), "Observações", None, "possível duplicado",
                                   "mesmo perfil de outro pedido (cliente/representante/produto/valor/status), data diferente")
                    df.at[idx, "Observações"] = "possível duplicado"
        df = df.drop(columns=["_chave_perfil"])

    log_df = pd.DataFrame(log, columns=["ID Pedido", "Campo", "Valor Antigo", "Valor Novo", "Motivo"])
    for col in ("Valor Antigo", "Valor Novo"):
        # a coluna mistura tipos entre linhas (texto, número, None) conforme o
        # campo alterado; padroniza para string para exibição/exportação segura
        log_df[col] = log_df[col].map(lambda v: "" if pd.isna(v) else str(v))

    resumo = {
        "linhas_originais": len(df_original),
        "linhas_finais": len(df),
        "duplicatas_exatas_removidas": len(df_original) - len(df),
        "total_correcoes": len(log_df),
        "capitalizacao_padronizada": int(log_df["Campo"].isin(COLUNAS_TEXTO_LIVRE).sum()) if len(log_df) else 0,
        "status_corrigidos": int((log_df["Campo"] == "Status").sum()) if len(log_df) else 0,
        "receitas_convertidas": int((log_df["Campo"] == "Receita").sum()) if len(log_df) else 0,
        "notas_adicionadas": int((log_df["Campo"] == "Observações").sum()) if len(log_df) else 0,
    }
    return df.reset_index(drop=True), log_df, resumo
