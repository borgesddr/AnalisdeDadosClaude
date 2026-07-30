"""Validações genéricas de qualidade de dados para planilhas de pedidos de
venda já limpas. Não dependem de nenhum ID específico. Reutilizado por
testar_correcoes.py (linha de comando) e por app.py (Streamlit).
"""

import pandas as pd


def _nome_bem_capitalizado(nome):
    if pd.isna(nome):
        return True
    palavras = [p for p in str(nome).split() if p]
    return all(p[:1].isupper() and p[1:] == p[1:].lower() for p in palavras)


def validar_planilha(df):
    """Roda uma bateria de checagens de qualidade sobre um df já limpo.

    Retorna uma lista de tuplas (nome, passou: bool, detalhe: str).
    """
    resultados = []

    def checar(nome, condicao, detalhe=""):
        resultados.append((nome, bool(condicao), detalhe))

    colunas = df.columns
    tem_id = "ID Pedido" in colunas

    def ids_de(subset):
        return subset["ID Pedido"].tolist() if tem_id else subset.index.tolist()

    if tem_id:
        repetidos = df.loc[df["ID Pedido"].duplicated(), "ID Pedido"].tolist()
        checar("IDs de pedido sem duplicidade", not repetidos, f"IDs repetidos: {repetidos}")

    if "Receita" in colunas:
        checar("Receita é numérica (não é mais texto com 'R$')", pd.api.types.is_numeric_dtype(df["Receita"]))
        nao_nulas = df["Receita"].dropna()
        if len(nao_nulas):
            invalidas = nao_nulas[nao_nulas <= 0]
            checar("Receita sem valores negativos ou zerados", invalidas.empty,
                   f"valores inválidos: {invalidas.tolist()}")

    for col in ["Região", "Representante", "Status", "Produto"]:
        if col not in colunas:
            continue
        valores = df[col].dropna().astype(str)
        if valores.empty:
            continue
        normalizados = valores.str.lower().str.strip()
        grupos = valores.groupby(normalizados).nunique()
        inconsistentes = sorted(set(valores[normalizados.isin(grupos[grupos > 1].index)]))
        checar(f"{col}: sem variações de capitalização para o mesmo valor", not inconsistentes,
               f"valores ainda inconsistentes: {inconsistentes}")

    if "Nome do Cliente" in colunas:
        mal_capitalizados = df.loc[~df["Nome do Cliente"].apply(_nome_bem_capitalizado)]
        checar("Nome do Cliente sem trechos em CAIXA ALTA ou minúsculas", mal_capitalizados.empty,
               f"linhas afetadas: {ids_de(mal_capitalizados)}")

    if "Status" in colunas:
        checar("Status sem valores nulos", df["Status"].notna().all(),
               f"linhas sem status: {ids_de(df[df['Status'].isna()])}")
        valores_status = set(df["Status"].dropna().unique())
        fora_do_padrao = valores_status - {"Fechado Ganho", "Fechado Perdido"}
        checar("Status usa vocabulário padronizado (Fechado Ganho / Fechado Perdido)",
               not fora_do_padrao, f"valores fora do padrão: {fora_do_padrao}")

    if "Observações" in colunas:
        for col_critica in ["Região", "Representante", "Receita"]:
            if col_critica not in colunas:
                continue
            faltantes = df[df[col_critica].isna()]
            sem_nota = faltantes[faltantes["Observações"].isna()]
            checar(f"Todo '{col_critica}' ausente está anotado em Observações", sem_nota.empty,
                   f"linhas sem anotação: {ids_de(sem_nota)}")

    chave_cols = [c for c in ["Nome do Cliente", "Região", "Representante", "Data do Pedido", "Receita", "Produto", "Status"]
                  if c in colunas]
    if chave_cols:
        chave = df[chave_cols].apply(lambda r: "|".join(str(v).strip().lower() for v in r), axis=1)
        duplicadas = chave.duplicated(keep=False)
        checar("Nenhuma linha totalmente duplicada (mesmo cliente/data/valor/produto/status)",
               not duplicadas.any(), f"linhas duplicadas: {ids_de(df[duplicadas])}")

    return resultados


def resumir_resultados(resultados):
    total = len(resultados)
    aprovados = sum(1 for _, ok, _ in resultados if ok)
    return {"total": total, "aprovados": aprovados, "reprovados": total - aprovados}
