"""Linha de comando: aplica a limpeza genérica (ver limpeza.py) em
data/planilha_vendas.xlsx e gera data/planilha_vendas_corrigida.xlsx com os
dados tratados + uma aba de log.
"""

from pathlib import Path

import pandas as pd

from limpeza import limpar_planilha

BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "data" / "planilha_vendas.xlsx"
OUTPUT_PATH = BASE_DIR / "data" / "planilha_vendas_corrigida.xlsx"


def salvar_xlsx(df, log_df, caminho):
    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="pedidos_vendas", index=False)
        log_df.to_excel(writer, sheet_name="log_correcoes", index=False)

        workbook = writer.book
        sheet = writer.sheets["pedidos_vendas"]
        if "Receita" in df.columns:
            col_letter = chr(ord("A") + df.columns.get_loc("Receita"))
            for cell in sheet[col_letter][1:]:
                cell.number_format = "R$ #,##0.00"

        for ws in workbook.worksheets:
            for column_cells in ws.columns:
                length = max((len(str(cell.value)) if cell.value is not None else 0) for cell in column_cells)
                ws.column_dimensions[column_cells[0].column_letter].width = length + 2


def main():
    df_original = pd.read_excel(INPUT_PATH)
    df_limpo, log_df, resumo = limpar_planilha(df_original)
    salvar_xlsx(df_limpo, log_df, OUTPUT_PATH)

    print(f"Planilha corrigida gerada em: {OUTPUT_PATH}")
    print(f"Total de correções registradas: {resumo['total_correcoes']}")
    print(f"Duplicatas exatas removidas: {resumo['duplicatas_exatas_removidas']}")
    print(f"Linhas finais: {resumo['linhas_finais']} (era {resumo['linhas_originais']})")


if __name__ == "__main__":
    main()
