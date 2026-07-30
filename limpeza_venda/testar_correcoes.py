"""Linha de comando: roda a bateria de validação genérica (ver validador.py)
sobre data/planilha_vendas_corrigida.xlsx.

Uso: python testar_correcoes.py
Saída: lista de testes com PASS/FALHA e código de saída 0 (tudo ok) ou 1 (falhou algo).
"""

import sys
from pathlib import Path

import pandas as pd

from validador import resumir_resultados, validar_planilha

BASE_DIR = Path(__file__).resolve().parent
CORRIGIDA_PATH = BASE_DIR / "data" / "planilha_vendas_corrigida.xlsx"


def main():
    xls = pd.ExcelFile(CORRIGIDA_PATH)
    resultados = []

    resultados.append(("Arquivo possui aba 'pedidos_vendas'", "pedidos_vendas" in xls.sheet_names, ""))
    resultados.append(("Arquivo possui aba 'log_correcoes'", "log_correcoes" in xls.sheet_names, ""))

    df = pd.read_excel(xls, sheet_name="pedidos_vendas")
    log_df = pd.read_excel(xls, sheet_name="log_correcoes") if "log_correcoes" in xls.sheet_names else pd.DataFrame()
    resultados.append(("Log de correções não está vazio", len(log_df) > 0, ""))

    resultados.extend(validar_planilha(df))

    largura = max(len(nome) for nome, _, _ in resultados)
    falhas = 0
    for nome, ok, detalhe in resultados:
        status = "PASS" if ok else "FALHA"
        sufixo = f"- {detalhe}" if (not ok and detalhe) else ""
        print(f"[{status:5}] {nome.ljust(largura)} {sufixo}")
        if not ok:
            falhas += 1

    resumo = resumir_resultados(resultados)
    print()
    print(f"Total: {resumo['total']} testes | {resumo['aprovados']} passaram | {falhas} falharam")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
