"""Formatação pt-BR — equivalente a src/lib/format.ts. Sem depender de locale do SO."""

from datetime import datetime


def format_brl(v: float | None) -> str:
    v = v or 0
    s = f"{v:,.2f}"
    s = s.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {s}"


def format_number(v: float | None) -> str:
    v = v or 0
    s = f"{v:,.0f}"
    return s.replace(",", ".")


def format_percent(v: float | None, decimals: int = 1) -> str:
    """Recebe uma fração (0.15 => '15,0%')."""
    v = v or 0
    s = f"{v * 100:.{decimals}f}"
    return f"{s.replace('.', ',')}%"


def format_date(d) -> str:
    if isinstance(d, str):
        d = datetime.fromisoformat(d[:19])
    return d.strftime("%d/%m/%Y")
