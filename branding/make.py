#!/usr/bin/env python3
"""Gera os SVGs do símbolo e do ícone do app (geometria única: corte a 30°)."""
import math, os
here = os.path.dirname(os.path.abspath(__file__))
T = math.tan(math.radians(30))
RUN, GAP, Y0 = 64, 9, 9           # corte, vão fixo entre aba e corpo, margem superior
rise = RUN * T
body = [(0, Y0 + rise), (RUN, Y0), (90, Y0), (90, 99), (0, 99)]
tri = [(0, Y0), (RUN, Y0), (0, Y0 + rise)]
dx, dy = GAP * math.sin(math.radians(30)), -GAP * math.cos(math.radians(30))
flap = [(x + dx, y + dy) for x, y in tri]
pts = lambda P: " ".join(f"{x:.2f},{y:.2f}" for x, y in P)
W, H = 94, 100

def mark(fill):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">\n'
            f'  <polygon fill="{fill}" points="{pts(body)}"/>\n'
            f'  <polygon fill="{fill}" points="{pts(flap)}"/>\n</svg>\n')

def w(name, s):
    open(os.path.join(here, name), "w").write(s)

w("aerographene-mark.svg", mark("currentColor"))
w("aerographene-mark-black.svg", mark("#000"))
w("aerographene-mark-white.svg", mark("#fff"))
S = 0.72 * 256 / H
ox, oy = (256 - W * S) / 2, (256 - H * S) / 2
w("aerographene-icon.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <rect width="256" height="256" rx="56" fill="#060b18"/>
  <rect x="3" y="3" width="250" height="250" rx="53" fill="none" stroke="#8cb4ff" stroke-opacity=".22" stroke-width="3"/>
  <g transform="translate({ox:.2f} {oy:.2f}) scale({S:.4f})" fill="#6cb6ff">
    <polygon points="{pts(body)}"/>
    <polygon points="{pts(flap)}"/>
  </g>
</svg>
''')
