#!/usr/bin/env python3
"""gera assets/gallery/*.webp, assets/fonts/*.woff2, themes.json e themes.css a partir de tools/themes.src.json.
uso: tools/build-gallery.sh  (env DL=caminho de theming/design-language)"""
import json, os, shutil, sys
from pathlib import Path
from PIL import Image
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
DL = Path(os.environ.get("DL", ROOT.parent.parent / "theming" / "design-language"))
src = json.loads((ROOT / "tools/themes.src.json").read_text())
gal, fdir = ROOT / "assets/gallery", ROOT / "assets/fonts"
gal.mkdir(parents=True, exist_ok=True); fdir.mkdir(parents=True, exist_ok=True)
W = 1280  # largura dos prints (lossy); lossless mantém o tamanho original


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + .05) / (lb + .05)


# pares de texto usados pelo site (texto normal: AA = 4,5:1)
PAIRS = [("text", "bg"), ("text", "panel"), ("text2", "bg"), ("text2", "panel"), ("muted", "bg"), ("muted", "panel"),
         ("accent", "bg"), ("accent", "panel"), ("notes", "panel"), ("term", "panel"), ("text", "sel"),
         ("inv", "text"), ("on-hl", "hl"), ("bg", "term"), ("bg", "accent")]
rep, bad = [], 0
for t in src["themes"]:
    for m, tk in t.get("tokens", {}).items():
        for fg, bgk in PAIRS:
            if fg not in tk or bgk not in tk:
                continue
            r = ratio(tk[fg], tk[bgk]); ok = r >= 4.5; bad += not ok
            rep.append(f'{t["id"]:13} {m:5} {fg:7} {tk[fg]} sobre {bgk:6} {tk[bgk]} {r:6.2f} {"AA" if ok else "FALHA"}')
(ROOT / "tools/contrastes.txt").write_text("\n".join(rep) + "\n")

out = []
for t in src["themes"]:
    e = {k: t[k] for k in ("id", "name", "status", "modes") if k in t}
    if t.get("note"):
        e["note"] = t["note"]
    e["print"] = {}
    for m, f in t.get("print", {}).items():
        p = ROOT / "tools/src" / f[1:] if f.startswith("@") else DL / t["src"] / f
        im = Image.open(p).convert("RGB")
        if t.get("crop"):
            im = im.crop(tuple(t["crop"]))
        name = f'{t["id"]}-{m}.webp'
        if t.get("lossless"):
            im.save(gal / name, "WEBP", lossless=True, method=6)
        else:
            im = im.resize((W, round(im.height * W / im.width)), Image.LANCZOS)
            im.save(gal / name, "WEBP", quality=t.get("q", 80), method=6)
        e["print"][m] = f"assets/gallery/{name}"; e["w"], e["h"] = im.size
    if "tokens" in t:
        e["tokens"] = t["tokens"]
    out.append(e)
(ROOT / "themes.json").write_text(json.dumps({"themes": out}, indent=1, ensure_ascii=False) + "\n")

# fontes: subset latino pequeno, woff2
used = {f for t in src["themes"] for f in t.get("ui", {}).get("fonts", [])}
css = ["/* gerado por tools/build-gallery.sh; não editar à mão */"]
for fid in sorted(used):
    f = src["fonts"][fid]
    font = TTFont(DL / f["src"])
    if "fvar" in font:
        font = instancer.instantiateVariableFont(font, {"wght": f["pin"]})
    o = subset.Options(); o.flavor = "woff2"; o.layout_features = ["kern", "liga"]; o.name_IDs = [0, 1, 2, 3, 4, 6]
    s = subset.Subsetter(o)
    s.populate(unicodes=list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)) + [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x2192, 0x203A])
    s.subset(font)
    font.flavor = "woff2"; font.save(fdir / (f["file"] + ".woff2"))
    if f.get("license"):
        shutil.copy(DL / f["license"], fdir / f["licout"])
    css.append(f'@font-face{{font-family:"{f["family"]}";font-weight:{f["weight"]};font-style:normal;font-display:swap;src:url(assets/fonts/{f["file"]}.woff2) format("woff2")}}')

for t in src["themes"]:
    ui = t.get("ui", {})
    for m, tk in t.get("tokens", {}).items():
        v = ";".join(f"--{k}:{x}" for k, x in tk.items())
        v += f';--r:{ui.get("r", "0px")};--font:{ui.get("font", "monospace")};--wm:{ui.get("wm", {}).get(m, "none")};--shadow:{ui.get("shadow", "none")};--hcase:{ui.get("heading", "none")};--fs:{ui.get("fs", "14px")};color-scheme:{m}'
        one = len(t["tokens"]) == 1  # tema de um modo só: vale para qualquer data-mode
        css.append(f':root[data-theme="{t["id"]}"]{"" if one else f"[data-mode={chr(34)}{m}{chr(34)}]"}{{{v}}}')
        if t["id"] == "default":
            css.append(f":root{{{v}}}")
(ROOT / "themes.css").write_text("\n".join(css) + "\n")

print(f"temas: {len(out)}; contraste: {len(rep)} pares, {bad} falhas")
for f in sorted(gal.glob("*.webp")):
    print(f"{f.stat().st_size/1024:7.1f} KB {f.name}")
for f in sorted(fdir.glob("*.woff2")):
    print(f"{f.stat().st_size/1024:7.1f} KB {f.name}")
sys.exit(1 if bad else 0)
