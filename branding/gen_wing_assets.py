#!/usr/bin/env python3
"""gera os ativos de marca a partir da asa (wing/wing-j-asa.svg e aerographene-wing-metal.svg).

saídas (sobrescreve): aerographene-icon.svg, aerographene-icon-flat.svg,
aerographene-mark{,-white,-black}.svg, png/* nos tamanhos que build/apply_branding_assets.sh espera.
dependências: python3 + Pillow, ImageMagick (`magick`).
uso: python3 branding/gen_wing_assets.py
"""
import pathlib
import re
import subprocess
import tempfile

from PIL import Image

B = pathlib.Path(__file__).resolve().parent
PNG = B / "png"
SIZES = [16, 22, 24, 32, 48, 64, 128, 256]
SMALL = 32  # até aqui usa o ícone liso (degradê some em tamanho pequeno)


def mark_svg(fill):
    """símbolo sem fundo: as 3 peças da asa j, viewBox justo."""
    polys = re.findall(r'points="([^"]+)"', (B / "wing/wing-j-asa.svg").read_text())
    pts = [[tuple(map(float, p.split(","))) for p in s.split()] for s in polys]
    xs = [x for P in pts for x, _ in P]
    ys = [y for P in pts for _, y in P]
    x0, y0, w, h = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    body = "".join(
        f'<polygon fill="{fill}" points="' + " ".join(f"{x-x0:.2f},{y-y0:.2f}" for x, y in P) + '"/>'
        for P in pts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.2f} {h:.2f}" '
            f'width="{w:.2f}" height="{h:.2f}">{body}</svg>\n')


def flat_icon(metal):
    """mesma geometria do ícone metálico, cinza liso e sem sombra."""
    s = re.sub(r'<polygon fill="url\(#shade\)"[^>]*/>', "", metal)
    s = s.replace('fill="url(#metal)"', 'fill="#c9cdd3"').replace(' filter="url(#drop)"', "")
    return s


def render(svg, size, out):
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as f:
        f.write(svg)
    subprocess.run(["magick", "-background", "none", "-density", str(max(96, 96 * 1024 // 256)),
                    f.name, "-resize", f"{size}x{size}", "-gravity", "center", "-extent", f"{size}x{size}",
                    f"PNG32:{out}"], check=True)
    pathlib.Path(f.name).unlink()


def name_logo(color, h, out_w, out):
    """símbolo novo + texto 'Aerographene' recortado de src/logo-<cor>.png."""
    src = Image.open(B / f"src/logo-{color}.png").convert("RGBA")
    text = src.crop((440, 0, src.width, src.height))
    with tempfile.TemporaryDirectory() as d:
        m = pathlib.Path(d) / "m.png"
        render(mark_svg("#fff" if color == "white" else "#000"), 485, m)
        mark = Image.open(m)
        mark = mark.crop(mark.getbbox())
    canvas = Image.new("RGBA", src.size, (0, 0, 0, 0))
    canvas.alpha_composite(mark, (80 + max(0, (316 - mark.width) // 2), 80))
    canvas.alpha_composite(text, (440, 0))
    canvas = canvas.crop(canvas.getbbox())
    # mesma proporção do original: altura h, largura out_w (centralizado)
    scale = h / canvas.height
    tw = min(out_w, round(canvas.width * scale))
    small = canvas.resize((tw, h), Image.LANCZOS)
    final = Image.new("RGBA", (out_w, h), (0, 0, 0, 0))
    final.alpha_composite(small, ((out_w - tw) // 2, 0))
    final.save(out)


def main():
    metal = (B / "aerographene-wing-metal.svg").read_text()
    flat = flat_icon(metal)
    (B / "aerographene-icon.svg").write_text(metal)
    (B / "aerographene-icon-flat.svg").write_text(flat)
    (B / "aerographene-mark.svg").write_text(mark_svg("#fff"))
    (B / "aerographene-mark-white.svg").write_text(mark_svg("#fff"))
    (B / "aerographene-mark-black.svg").write_text(mark_svg("#000"))
    for n in SIZES:
        render(flat if n <= SMALL else metal, n, PNG / f"aerographene-icon-{n}.png")
        for c, fill in (("white", "#fff"), ("black", "#000")):
            render(mark_svg(fill), n, PNG / f"aerographene-mark-{c}-{n}.png")
    subprocess.run(["magick"] + [str(PNG / f"aerographene-icon-{n}.png") for n in (16, 24, 32, 48, 64, 128, 256)]
                   + [str(PNG / "aerographene-icon.ico")], check=True)
    for c in ("white", "black"):
        name_logo(c, 22, 97, PNG / f"logo-name-22-{c}-1x.png")
        name_logo(c, 44, 194, PNG / f"logo-name-22-{c}-2x.png")
        name_logo(c, 32, 171, PNG / f"logo-name-32-{c}-1x.png")
        name_logo(c, 64, 342, PNG / f"logo-name-32-{c}-2x.png")


if __name__ == "__main__":
    main()
