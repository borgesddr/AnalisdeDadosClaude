"""CLI orquestrador do pipeline: KPIs (Etapa A) -> relatorio HTML (Etapa B)."""

import argparse

from src import compute_kpis, generate_report


def main():
    parser = argparse.ArgumentParser(description="Pipeline de KPIs e relatorio HTML (e-commerce, identidade Keyrus)")
    parser.add_argument("--stage", choices=["kpis", "report", "all"], default="all")
    args = parser.parse_args()

    if args.stage in ("kpis", "all"):
        compute_kpis.main()
    if args.stage in ("report", "all"):
        generate_report.main()


if __name__ == "__main__":
    main()
