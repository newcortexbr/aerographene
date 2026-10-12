#!/usr/bin/env python3
"""wordmark em pixel estilo terminal (blocos + contorno duplo deslocado).

gera SVG com o ícone ao lado e uma versão ANSI para terminal.
uso: python3 gen_ascii_logo.py [saida_dir]
"""
import pathlib
import sys

GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "G": ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
}
WORD = "AEROGRAPHENE"
PX = 12          # lado do pixel
GAP = 1          # colunas entre letras
OFF = 4          # deslocamento de cada contorno
PALETTES = {
    "mono": ("#ffffff", "#8a8f98", "#cfd3da"),
    "aurora": ("#b9f3ff", "#4aa8ff", "#7cc4ff"),
}


def cells():
    out, x0 = [], 0
    for ch in WORD:
        g = GLYPHS[ch]
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == "1":
                    out.append((x0 + c, r))
        x0 += 5 + GAP
    return out, x0 - GAP


ICON = pathlib.Path(__file__).resolve().parent.parent / "aerographene-wing-metal.svg"


def outline(pts):
    """só as arestas externas do conjunto de pixels."""
    on, d = set(pts), []
    for x, y in pts:
        X, Y = x * PX, y * PX
        if (x, y - 1) not in on: d.append(f"M{X} {Y}h{PX}")
        if (x, y + 1) not in on: d.append(f"M{X} {Y+PX}h{PX}")
        if (x - 1, y) not in on: d.append(f"M{X} {Y}v{PX}")
        if (x + 1, y) not in on: d.append(f"M{X+PX} {Y}v{PX}")
    return "".join(d)


def svg(palette, with_icon=True):
    top, bot, line = PALETTES[palette]
    pts, cols = cells()
    icon = 7 * PX + 2 * OFF
    ix = icon + 28 if with_icon else 0
    w, h = ix + cols * PX + 3 * OFF, 7 * PX + 3 * OFF
    rects = "".join(f'<rect x="{x*PX}" y="{y*PX}" width="{PX}" height="{PX}"/>' for x, y in pts)
    edges = outline(pts)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 -8 {w+16} {h+16}" width="{w+16}" height="{h+16}">',
         f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
         f'<stop offset="1" stop-color="{bot}"/></linearGradient></defs>']
    if with_icon:
        inner = ICON.read_text().split(">", 1)[1].rsplit("</svg>", 1)[0]
        s.append(f'<g transform="scale({icon/256})">{inner}</g>')
    for k in (2, 1):  # contornos deslocados atrás
        s.append(f'<g transform="translate({ix+k*OFF} {k*OFF})" fill="none" stroke="{line}" '
                 f'stroke-width="2" stroke-linecap="square" stroke-opacity="{1.0 - 0.3*k}"><path d="{edges}"/></g>')
    s.append(f'<g transform="translate({ix} 0)" fill="url(#g)" shape-rendering="crispEdges">{rects}</g></svg>')
    return "".join(s)


def ansi():
    pts, cols = set(cells()[0]), cells()[1]
    shades = [255, 254, 253, 251, 249, 247, 245]
    lines = []
    for y in range(7):
        row = "".join("██" if (x, y) in pts else ("░░" if (x - 1, y - 1) in pts else "  ")
                      for x in range(cols + 1))
        lines.append(f"\x1b[38;5;{shades[y]}m{row}\x1b[0m")
    return "\n".join(lines)


if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).parent)
    for p in PALETTES:
        (out / f"wordmark-{p}.svg").write_text(svg(p))
    (out / "wordmark.ansi").write_text(ansi() + "\n")


def svg_simple(split=4, dim="#8a8f98", lit="#f2f3f5"):
    """variante simples estilo opencode: blocos sólidos, dois tons, sem contorno."""
    pts, cols = cells()
    icon = 7 * PX
    ix = icon + 24
    w, h = ix + cols * PX, 7 * PX
    cut = split * (5 + GAP)
    a = "".join(f'<rect x="{x*PX}" y="{y*PX}" width="{PX}" height="{PX}"/>' for x, y in pts if x < cut)
    b = "".join(f'<rect x="{x*PX}" y="{y*PX}" width="{PX}" height="{PX}"/>' for x, y in pts if x >= cut)
    inner = ICON.read_text().split(">", 1)[1].rsplit("</svg>", 1)[0]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 -8 {w+16} {h+16}" width="{w+16}" height="{h+16}">'
            f'<g transform="scale({icon/256})">{inner}</g>'
            f'<g transform="translate({ix} 0)" shape-rendering="crispEdges">'
            f'<g fill="{dim}">{a}</g><g fill="{lit}">{b}</g></g></svg>')


def ansi_simple(split=4):
    """meio-bloco (▀▄█): 7 linhas de pixel viram 4 de texto."""
    on, cols = set(cells()[0]), cells()[1]
    cut = split * (5 + GAP)
    lines = []
    for y in range(0, 8, 2):
        row = ""
        for x in range(cols):
            t, b = (x, y) in on, (x, y + 1) in on
            ch = "█" if t and b else "▀" if t else "▄" if b else " "
            row += f"\x1b[38;5;{245 if x < cut else 255}m{ch}"
        lines.append(row + "\x1b[0m")
    return "\n".join(lines)


if __name__ == "__main__":
    (out / "wordmark-simple.svg").write_text(svg_simple())
    (out / "wordmark-simple.ansi").write_text(ansi_simple() + "\n")
