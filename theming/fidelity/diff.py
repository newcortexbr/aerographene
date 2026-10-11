#!/usr/bin/env python3
"""Diff captura vs mockup por região (PIL, stdlib).

Uso: python3 theming/fidelity/diff.py [--shots /tmp/fid0-out/shots] [--out /tmp/fid0-out/diff] [--mock-root theming]
Saídas por cena: <out>/<tema>-<modo>-<cena>.png (mockup | captura | diferença x4, com retângulos das regiões)
e <out>/results.json + tabela no stdout. Métricas por região: mae (0-255, média de |Δ| por canal),
dmean (Δ da cor média, RGB do mockup -> captura) e sim = 1 - mae/255.
Limite: a captura real tem 1366x740 (tela 1366x768) e o mockup 1440x900; regiões são caixas
(x,y,w,h) escolhidas por âncora (esquerda, direita ou centro) e comparadas no mesmo tamanho; o conteúdo
(abas, textos, pinned) difere por construção, então a métrica mede fundo/forma/cor, não texto.
"""
import argparse, json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageStat

M = "1"  # theming/1 = mockups default; theming/design-language/pixelized = pixelized
MOCK = {
    ("default", "sidebar", "home"): "1/R-r01a-home-sidebar.png",
    ("default", "sidebar", "menu-aba"): "1/M-r01c-aba.png",
    ("default", "sidebar", "menu-3pontos"): "1/M-r01a-3-pontos.png",
    ("default", "topbar", "home"): "1/R-r01b-notas-topbar.png",
    ("pixelized", "sidebar", "home"): "design-language/pixelized/R-r01a-home-sidebar.png",
    ("pixelized", "topbar", "home"): "design-language/pixelized/R-r01b-notas-topbar.png",
}
# (nome, caixa no mockup, caixa na captura)
REG = {
    ("sidebar", "home"): [
        ("toolbar-esq", (0, 0, 300, 44), (0, 0, 300, 44)),
        ("url", (400, 0, 640, 44), (363, 0, 640, 44)),
        ("toolbar-dir", (1240, 0, 200, 44), (1166, 0, 200, 44)),
        ("sidebar", (0, 44, 240, 690), (0, 44, 240, 690)),
        ("pinned", (8, 84, 190, 90), (4, 44, 235, 36)),
        ("aba-ativa", (14, 270, 200, 24), (8, 212, 200, 24)),
        ("pagina", (540, 322, 600, 300), (503, 260, 600, 300)),
    ],
    ("topbar", "home"): [
        ("abas", (0, 44, 600, 32), (0, 4, 600, 32)),
        ("nav", (0, 80, 400, 38), (0, 42, 400, 38)),
        ("pinned-linha", (0, 0, 420, 40), (0, 82, 420, 36)),
    ],
}
MENU = {  # caixa do menu no mockup
    "menu-aba": (131, 341, 247, 285), "menu-3pontos": (1175, 47, 254, 212)}


def stats(a, b):
    d = ImageChops.difference(a, b)
    mae = sum(ImageStat.Stat(d).mean) / 3
    ma, mb = ImageStat.Stat(a).mean, ImageStat.Stat(b).mean
    return {"mae": round(mae, 2), "sim": round(1 - mae / 255, 4),
            "mean_mock": "#%02x%02x%02x" % tuple(round(v) for v in ma[:3]),
            "mean_cap": "#%02x%02x%02x" % tuple(round(v) for v in mb[:3]),
            "dmean": [round(y - x, 1) for x, y in zip(ma[:3], mb[:3])]}


def crop(im, box):
    x, y, w, h = box
    return im.crop((x, y, min(x + w, im.width), min(y + h, im.height)))


def changed_bbox(a, b, thr=24):
    d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > thr else 0)
    return d.getbbox()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default="/tmp/fid0-out/shots"); ap.add_argument("--out", default="/tmp/fid0-out/diff")
    ap.add_argument("--mock-root", default=str(Path(__file__).resolve().parents[1]))
    a = ap.parse_args(); shots = Path(a.shots); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    root = Path(a.mock_root); res = {}
    for (theme, mode, scene), rel in MOCK.items():
        cp = shots / f"{theme}-{mode}-{scene}.png"; mp = root / rel
        if not cp.exists() or not mp.exists():
            res[f"{theme}-{mode}-{scene}"] = {"erro": f"falta {cp if not cp.exists() else mp}"}; continue
        cap = Image.open(cp).convert("RGB"); mock = Image.open(mp).convert("RGB")
        regs = []
        if scene == "home":
            for n, mb, cb in REG[(mode, "home")]:
                w = min(mb[2], cb[2], mock.width - mb[0], cap.width - cb[0]); h = min(mb[3], cb[3], mock.height - mb[1], cap.height - cb[1])
                m_, c_ = crop(mock, (*mb[:2], w, h)), crop(cap, (*cb[:2], w, h))
                regs.append({"regiao": n, "mock_box": mb, "cap_box": cb, "tam": [w, h], **stats(m_, c_)})
        else:  # menu: caixa do mockup vs bbox do que mudou entre home e menu na captura
            home = Image.open(shots / f"{theme}-{mode}-home.png").convert("RGB")
            bb = changed_bbox(home, cap)
            mb = MENU[scene]
            if bb:
                cb = (bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1])
                w, h = min(mb[2], cb[2]), min(mb[3], cb[3])
                regs.append({"regiao": "menu", "mock_box": mb, "cap_box": list(cb), "tam": [w, h],
                             "tam_mock": mb[2:], "tam_cap": list(cb[2:]),
                             **stats(crop(mock, (mb[0], mb[1], w, h)), crop(cap, (cb[0], cb[1], w, h)))})
        # painel
        W = mock.width + cap.width + mock.width
        panel = Image.new("RGB", (W, mock.height), (30, 0, 30))
        panel.paste(mock, (0, 0)); panel.paste(cap, (mock.width, 0))
        dm = Image.new("RGB", mock.size, (0, 0, 0))
        dr = ImageDraw.Draw(panel)
        for r in regs:
            mb, cb, (w, h) = r["mock_box"], r["cap_box"], r["tam"]
            m_, c_ = crop(mock, (*mb[:2], w, h)), crop(cap, (*cb[:2], w, h))
            d = ImageChops.difference(m_, c_).point(lambda v: min(255, v * 4))
            dm.paste(d, (mb[0], mb[1]))
            dr.rectangle((mb[0], mb[1], mb[0] + w, mb[1] + h), outline=(255, 200, 0))
            dr.rectangle((mock.width + cb[0], cb[1], mock.width + cb[0] + w, cb[1] + h), outline=(255, 200, 0))
        panel.paste(dm, (mock.width + cap.width, 0))
        panel.save(out / f"{theme}-{mode}-{scene}.png")
        res[f"{theme}-{mode}-{scene}"] = {"mock": rel, "regioes": regs}
    (out / "results.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    for k, v in res.items():
        print(k, v.get("erro", ""))
        for r in v.get("regioes", []):
            print(f"  {r['regiao']:13s} mae={r['mae']:6.2f} sim={r['sim']:.3f} mock={r['mean_mock']} cap={r['mean_cap']} {r.get('tam_mock','')}{r.get('tam_cap','')}")


if __name__ == "__main__":
    main()
