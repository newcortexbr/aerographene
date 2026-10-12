#!/usr/bin/env python3
"""gif do README: asa + "LOVES" no pixel do wordmark, vermelho pulsando.

uso: python3 branding/loves/gen_loves_gif.py  (precisa de rsvg-convert e Pillow)
"""
import io, math, pathlib, subprocess, sys
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ascii"))
from gen_ascii_logo import GLYPHS  # noqa: E402

GLYPHS = dict(GLYPHS)
GLYPHS.update({
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
})
WORD, PX, GAP, ICON, PAD, FRAMES = "LOVES", 10, 1, 96, 28, 20
LO, HI = (205, 40, 54), (255, 72, 88)

png = subprocess.run(["rsvg-convert", "-w", str(ICON), "-h", str(ICON),
                      str(HERE.parent / "aerographene-icon.svg")],
                     check=True, capture_output=True).stdout
icon = Image.open(io.BytesIO(png)).convert("RGBA")
tw = (len(WORD) * (5 + GAP) - GAP) * PX
W, H = ICON + PAD + tw, ICON
ty = (H - 7 * PX) // 2

frames = []
for f in range(FRAMES):
    t = (1 - math.cos(2 * math.pi * f / FRAMES)) / 2
    col = tuple(round(a + (b - a) * t) for a, b in zip(LO, HI)) + (255,)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    im.alpha_composite(icon, (0, 0))
    x0 = ICON + PAD
    for ch in WORD:
        for r, row in enumerate(GLYPHS[ch]):
            for c, v in enumerate(row):
                if v == "1":
                    im.paste(col, (x0 + c * PX, ty + r * PX,
                                   x0 + (c + 1) * PX, ty + (r + 1) * PX))
        x0 += (5 + GAP) * PX
    # transparência 1 bit: alfa < 128 vira índice transparente
    a = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    p = im.convert("RGB").quantize(255, dither=Image.Dither.NONE)
    p.paste(255, mask=Image.eval(a, lambda v: 255 - v))
    frames.append(p)

out = HERE / "aerographene-loves.gif"
frames[0].save(out, save_all=True, append_images=frames[1:], duration=70,
               loop=0, transparency=255, disposal=2, optimize=False)
print(out, out.stat().st_size)
