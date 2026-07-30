"""ETAPA B (parte 1): construtores de graficos como SVG inline, usando
apenas a stdlib. Sem matplotlib, sem JS/CDN externo -- o HTML final deve
funcionar 100% offline.
"""

from xml.sax.saxutils import escape

from src.formatting import format_brl, format_pct

INK_TITLE = "#111111"
INK_BODY = "#4A4A4A"
INK_MUTED = "#898781"
GRID = "#E0E0E0"
SURFACE = "#FFFFFF"

HUE_DEFAULT = "#38BDF8"
CHANNEL_COLORS = {"ecommerce": "#38BDF8", "loja_fisica": "#F5A623"}
DIVERGING_NEG = "#38BDF8"
DIVERGING_POS = "#E63946"
DIVERGING_MID = "#E0E0E0"

FONT_FAMILY = "'Poppins','Segoe UI',system-ui,sans-serif"


def _esc(text):
    return escape(str(text))


def _svg_open(width, height, title):
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="auto" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" font-family="{FONT_FAMILY}">'
        f"<title>{_esc(title)}</title>"
    )


def bar_chart_h(items, *, title, width=640, bar_h=28, gap=12, label_w=190, value_w=100,
                 color=HUE_DEFAULT, value_fmt=format_brl):
    n = len(items)
    height = gap + n * (bar_h + gap)
    max_value = max((item["value"] for item in items), default=1) or 1
    bar_area = width - label_w - value_w

    parts = [_svg_open(width, height, title)]
    for i, item in enumerate(items):
        y = gap + i * (bar_h + gap)
        bar_w = max(bar_area * (item["value"] / max_value), 2)
        label = str(item["label"])
        if len(label) > 26:
            label = label[:25] + "…"
        value_label = value_fmt(item["value"])
        parts.append(
            f'<g>'
            f'<title>{_esc(item["label"])}: {_esc(value_label)}</title>'
            f'<text x="0" y="{y + bar_h / 2}" dominant-baseline="middle" '
            f'font-size="13" fill="{INK_BODY}">{_esc(label)}</text>'
            f'<rect x="{label_w}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" rx="4" fill="{color}"/>'
            f'<text x="{label_w + bar_w + 8}" y="{y + bar_h / 2}" dominant-baseline="middle" '
            f'font-size="13" font-weight="600" fill="{INK_TITLE}">{_esc(value_label)}</text>'
            f'</g>'
        )
    parts.append("</svg>")
    return "".join(parts)


def stacked_bar_100pct(segments, *, title, width=640, height=56):
    total = sum(seg["value"] for seg in segments) or 1
    parts = [_svg_open(width, height, title)]
    x = 0
    bar_y, bar_h = 0, 36
    for seg in segments:
        seg_w = width * (seg["value"] / total)
        parts.append(
            f'<g><title>{_esc(seg["label"])}: {_esc(format_pct(seg["value"] / total * 100, signed=False))}</title>'
            f'<rect x="{x:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="{bar_h}" fill="{seg["color"]}"/>'
        )
        if seg_w > 60:
            parts.append(
                f'<text x="{x + seg_w / 2:.1f}" y="{bar_y + bar_h / 2}" dominant-baseline="middle" '
                f'text-anchor="middle" font-size="13" font-weight="600" fill="#FFFFFF">'
                f'{_esc(format_pct(seg["value"] / total * 100, 0, signed=False))}</text>'
            )
        parts.append("</g>")
        x += seg_w
    parts.append("</svg>")
    return "".join(parts)


def line_chart(points, *, title, width=640, height=220, color=HUE_DEFAULT, value_fmt=format_brl,
               label_every=5):
    if not points:
        return ""
    pad_l, pad_r, pad_t, pad_b = 60, 16, 16, 28
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    values = [p["y"] for p in points]
    max_v = max(values) or 1
    min_v = min(0, min(values))
    span = (max_v - min_v) or 1
    n = len(points)

    def px(i):
        return pad_l + (plot_w * i / (n - 1) if n > 1 else 0)

    def py(v):
        return pad_t + plot_h - (plot_h * (v - min_v) / span)

    coords = [(px(i), py(p["y"])) for i, p in enumerate(points)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    area = f"{pad_l:.1f},{pad_t + plot_h:.1f} " + poly + f" {coords[-1][0]:.1f},{pad_t + plot_h:.1f}"

    parts = [_svg_open(width, height, title)]
    for frac in (0, 0.5, 1):
        gy = pad_t + plot_h * (1 - frac)
        gv = min_v + span * frac
        parts.append(
            f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{width - pad_r}" y2="{gy:.1f}" '
            f'stroke="{GRID}" stroke-width="1"/>'
            f'<text x="{pad_l - 8}" y="{gy:.1f}" dominant-baseline="middle" text-anchor="end" '
            f'font-size="11" fill="{INK_MUTED}">{_esc(value_fmt(gv, 0))}</text>'
        )
    parts.append(f'<polygon points="{area}" fill="{color}" opacity="0.12"/>')
    parts.append(f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2.5"/>')
    for i, (x, y) in enumerate(coords):
        is_marker_step = i % label_every == 0 or i == n - 1
        if not is_marker_step:
            continue
        show_label = i == n - 1 or (n - 1 - i) >= label_every
        label_svg = (
            f'<text x="{x:.1f}" y="{height - 6}" text-anchor="middle" font-size="10" '
            f'fill="{INK_MUTED}">{_esc(points[i].get("x_label", ""))}</text>'
            if show_label else ""
        )
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}">'
            f'<title>{_esc(points[i].get("x_label", ""))}: {_esc(value_fmt(points[i]["y"]))}</title>'
            f'</circle>'
            f'{label_svg}'
        )
    parts.append("</svg>")
    return "".join(parts)


def diverging_bar_h(items, *, title, width=640, bar_h=26, gap=12, label_w=170, value_w=64):
    n = len(items)
    height = gap + n * (bar_h + gap)
    max_abs = max((abs(item["value_pct"]) for item in items), default=1) or 1
    plot_w = width - label_w - 2 * value_w
    half_w = plot_w / 2
    center_x = label_w + value_w + half_w

    parts = [_svg_open(width, height, title)]
    parts.append(f'<line x1="{center_x}" y1="0" x2="{center_x}" y2="{height}" stroke="{DIVERGING_MID}" stroke-width="1"/>')
    for i, item in enumerate(items):
        y = gap + i * (bar_h + gap)
        value = item["value_pct"]
        bar_w = half_w * (abs(value) / max_abs)
        color = DIVERGING_POS if value >= 0 else DIVERGING_NEG
        x = center_x if value >= 0 else center_x - bar_w
        label = str(item["label"])
        if len(label) > 22:
            label = label[:21] + "…"
        parts.append(
            f'<g><title>{_esc(item["label"])}: {_esc(format_pct(value))}</title>'
            f'<text x="0" y="{y + bar_h / 2}" dominant-baseline="middle" font-size="13" '
            f'fill="{INK_BODY}">{_esc(label)}</text>'
            f'<rect x="{x:.1f}" y="{y}" width="{max(bar_w, 1):.1f}" height="{bar_h}" rx="4" fill="{color}"/>'
        )
        value_x = center_x + bar_w + 8 if value >= 0 else center_x - bar_w - 8
        anchor = "start" if value >= 0 else "end"
        parts.append(
            f'<text x="{value_x:.1f}" y="{y + bar_h / 2}" dominant-baseline="middle" text-anchor="{anchor}" '
            f'font-size="13" font-weight="600" fill="{INK_TITLE}">{_esc(format_pct(value))}</text></g>'
        )
    parts.append("</svg>")
    return "".join(parts)


def legend(entries):
    swatches = "".join(
        f'<span class="legend-item"><span class="legend-swatch" style="background:{color}"></span>{_esc(label)}</span>'
        for label, color in entries
    )
    return f'<div class="legend">{swatches}</div>'


def render_table(headers, rows):
    thead = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    tbody = "".join(
        "<tr>" + "".join(f"<td>{_esc(cell)}</td>" for cell in row) + "</tr>" for row in rows
    )
    return f'<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>'


def chart_figure(title, subtitle, svg, table_html, legend_html=""):
    subtitle_html = f'<p class="chart-subtitle">{_esc(subtitle)}</p>' if subtitle else ""
    return (
        f'<figure class="card chart-card">'
        f'<figcaption><h3>{_esc(title)}</h3>{subtitle_html}{legend_html}</figcaption>'
        f'<div class="chart-svg-wrap">{svg}</div>'
        f'<details><summary>Ver dados em tabela</summary>{table_html}</details>'
        f'</figure>'
    )
