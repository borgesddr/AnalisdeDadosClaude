"""Formatação de números/datas em pt-BR sem depender de locale do SO."""


def format_brl(value, decimals=2):
    sign = "-" if value < 0 else ""
    value = abs(value)
    inteiro, _, frac = f"{value:,.{decimals}f}".partition(".")
    inteiro = inteiro.replace(",", ".")
    return f"{sign}R$ {inteiro},{frac}" if decimals else f"{sign}R$ {inteiro}"


def format_number(value, decimals=0):
    inteiro, _, frac = f"{value:,.{decimals}f}".partition(".")
    inteiro = inteiro.replace(",", ".")
    return f"{inteiro},{frac}" if decimals else inteiro


def format_pct(value, decimals=1, signed=True):
    sign = "+" if (signed and value > 0) else ""
    return f"{sign}{value:.{decimals}f}%".replace(".", ",")


def format_date_br(iso_date):
    ano, mes, dia = iso_date.split("-")
    return f"{dia}/{mes}/{ano}"
