#!/usr/bin/env python3
"""Gera os SVGs do símbolo e do ícone do app.

Geometria única: o símbolo do logotipo (src/logo-white.png, o que vem antes do "A"),
vértices medidos em pixels da fonte 2314x645 e normalizados para a caixa do símbolo.
"""
import os
here = os.path.dirname(os.path.abspath(__file__))

FLAP = [(88, 237), (328, 86), (276, 237)]
BODY = [(88, 252), (290, 252), (323, 157), (362, 157), (362, 391), (88, 391)]
SLIVER = [(395, 355), (372, 391), (395, 391)]
X0, Y0, X1, Y1 = 88, 86, 395, 391
K = 100 / max(X1 - X0, Y1 - Y0)          # símbolo normalizado para ~100 unidades
SHAPES = [[((x - X0) * K, (y - Y0) * K) for x, y in P] for P in (FLAP, BODY, SLIVER)]
W, H = round((X1 - X0) * K, 2), round((Y1 - Y0) * K, 2)
pts = lambda P: " ".join(f"{x:.2f},{y:.2f}" for x, y in P)


def polys(fill, indent="  "):
    return "".join(f'{indent}<polygon fill="{fill}" points="{pts(P)}"/>\n' for P in SHAPES)


def mark(fill):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">\n'
            f'{polys(fill)}</svg>\n')


def w(name, s):
    open(os.path.join(here, name), "w").write(s)


w("aerographene-mark.svg", mark("currentColor"))
w("aerographene-mark-black.svg", mark("#000"))
w("aerographene-mark-white.svg", mark("#fff"))

# ícone do app: símbolo branco sobre fundo preto arredondado, ocupando 64% do lado
S = 0.64 * 256 / max(W, H)
ox, oy = (256 - W * S) / 2, (256 - H * S) / 2
w("aerographene-icon.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <rect width="256" height="256" rx="56" fill="#000"/>
  <rect x="2" y="2" width="252" height="252" rx="54" fill="none" stroke="#fff" stroke-opacity=".14" stroke-width="2"/>
  <g transform="translate({ox:.2f} {oy:.2f}) scale({S:.4f})">
{polys("#fff", "    ")}  </g>
</svg>
''')
