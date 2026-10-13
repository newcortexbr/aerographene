#!/usr/bin/env python3
"""Resume rodadas de bench/ab.py e gera gráficos SVG (barras horizontais; imagens combinadas startup/tabs/speed). Só stdlib.

  python3 bench/charts.py --data /tmp/bench02b-out --json docs/img/bench/v02.json --out docs/img/bench \
      --title "v0.2" --note "Comet Lake i3-10110U, perfil performance, 13/10/2026"
  python3 bench/charts.py --from-json docs/img/bench/v02.json --out docs/img/bench   # só redesenha
"""
import argparse, json, random, re, statistics as st, sys
from pathlib import Path
from xml.sax.saxutils import escape

LABEL = {"aerographene": "aerographene", "helium": "Helium", "thorium": "Thorium",
         "chrome": "Google Chrome", "ungoogled": "ungoogled-chromium"}
METRICS = [  # chave, bloco, campo, título, unidade
    ("warm", "warm", "first_ms", "Startup, existing profile", "ms"),
    ("first", "first", "first_ms", "Startup, new profile", "ms"),
    ("tabs_all", "tabs", "all_ms", "10 tabs: time until all loaded", "ms"),
    ("tabs_pss", "tabs", "pss_mib", "10 tabs: memory (total PSS)", "MiB"),
    ("speedo", "speedo", "score", "Speedometer 3.1", "score"),
    ("jetstream", "jetstream", "score", "JetStream 2", "score"),
]
HIGHER = {"speedo", "jetstream"}  # maior é melhor (as demais: menor é melhor)
SUBTITLE = {"speedo": "median score (runs per minute) · higher is better",
            "jetstream": "median score · higher is better"}
# imagens combinadas: arquivo -> chaves (painéis empilhados; chave sem dados é omitida)
COMBINED = {"startup": ["warm", "first"], "tabs": ["tabs_all", "tabs_pss"], "speed": ["speedo", "jetstream"]}


def load(d: Path):
    data = {}  # (block, browser) -> {lap: [values per field]}
    for p in sorted(d.glob("*-lap*-*.jsonl")):
        m = re.match(r"(warm|first|tabs|speedo|jetstream)-lap(\d+)-(\w+)-results", p.name)
        if not m:
            continue
        blk, lap, br = m.group(1), int(m.group(2)), m.group(3)
        for line in p.read_text().splitlines():
            r = json.loads(line)
            data.setdefault((blk, br), {}).setdefault(lap, []).append(r)
    return data


def boot_ci(vals, n=2000, seed=1):
    rnd = random.Random(seed)
    meds = sorted(st.median(rnd.choices(vals, k=len(vals))) for _ in range(n))
    return meds[int(.025 * n)], meds[int(.975 * n)]


def q(vals, p):
    s = sorted(vals); i = (len(s) - 1) * p; lo = int(i); hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def summarize(data):
    out = {}
    for key, blk, field, title, unit in METRICS:
        res = {}
        for (b, br), laps in data.items():
            if b != blk:
                continue
            vals = [r[field] for rs in laps.values() for r in rs if r.get(field) is not None]
            if not vals:
                continue
            lo, hi = boot_ci(vals)
            res[br] = {"n": len(vals), "median": st.median(vals), "ci95": [lo, hi],
                       "q1": q(vals, .25), "q3": q(vals, .75), "min": min(vals), "max": max(vals),
                       "lap_med": {str(l): st.median([r[field] for r in rs if r.get(field) is not None])
                                   for l, rs in laps.items() if any(r.get(field) is not None for r in rs)}}
        # razões pareadas vs helium (mediana das razões por volta)
        for br, v in res.items():
            h = res.get("helium")
            if h and br != "helium":
                rat = [v["lap_med"][l] / h["lap_med"][l] for l in v["lap_med"] if l in h["lap_med"]]
                v["paired_vs_helium"] = {"median_ratio": st.median(rat), "laps": len(rat),
                                         "below": sum(1 for x in rat if x < 1)}
                v["median_vs_helium"] = v["median"] / h["median"]
        if not res:
            continue
        out[key] = {"title": title, "unit": unit, "browsers": res}
    return out


MACHINE = "Test machine: Intel Core i3-10110U · 16 GB RAM · CachyOS (kernel 7.3.0-rc6) · power profile: performance"


def fmt(x, unit):
    return (f"{x:,.0f}" if x >= 1000 else f"{x:.1f}") + f" {unit}"


def panel(key, m, y0, W=900, left=210, right=150, top=96, rh=44):
    """elementos SVG de um painel (título, barras) com origem vertical y0; devolve (elementos, altura)."""
    hib = key in HIGHER
    rows = sorted(m["browsers"].items(), key=lambda kv: kv[1]["median"], reverse=hib)
    mx = max(v["median"] for _, v in rows)
    bw = W - left - right
    sub = SUBTITLE.get(key, f'median, in {m["unit"]} · lower is better')
    o = [f'<text x="28" y="{y0+40}" font-size="22" font-weight="700" fill="#f2f4f8">{escape(m["title"])}</text>',
         f'<text x="28" y="{y0+64}" font-size="14" fill="#9aa3b2">{escape(sub)}</text>']
    for i, (br, v) in enumerate(rows):
        y = y0 + top + i * rh
        w = max(2, bw * v["median"] / mx)
        hl = br == "aerographene"
        col = "#7c9cff" if hl else "#3a4152"
        o.append(f'<text x="{left-14}" y="{y+23}" text-anchor="end" font-size="15" fill="{"#ffffff" if hl else "#c3cad6"}" font-weight="{700 if hl else 400}">{escape(LABEL.get(br, br))}</text>')
        o.append(f'<rect x="{left}" y="{y+6}" width="{w:.1f}" height="28" rx="5" fill="{col}"/>')
        o.append(f'<text x="{left+w+10:.1f}" y="{y+26}" font-size="15" font-weight="{700 if hl else 400}" fill="#f2f4f8">{fmt(v["median"], m["unit"])}</text>')
    return o, top + rh * len(rows) + 12


def svg(items, note):
    """items: lista de (key, m); painéis empilhados no mesmo fundo, rodapé único."""
    W, y, body = 900, 0, []
    for key, m in items:
        o, h = panel(key, m, y)
        body += o
        y += h
    H = y + 48
    head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif">',
            f'<rect width="{W}" height="{H}" rx="14" fill="#14161c"/>']
    foot = [f'<text x="28" y="{H-34}" font-size="12" fill="#7a8394">{escape(MACHINE)}</text>',
            f'<text x="28" y="{H-16}" font-size="12" fill="#7a8394">{escape(note)}</text>', '</svg>']
    return "\n".join(head + body + foot)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data"); ap.add_argument("--json"); ap.add_argument("--from-json")
    ap.add_argument("--out", required=True); ap.add_argument("--note", default="")
    ap.add_argument("--title", default="")
    a = ap.parse_args()
    if a.from_json:
        summ = json.loads(Path(a.from_json).read_text())
        note = summ.get("_note", a.note)
        summ = {k: v for k, v in summ.items() if not k.startswith("_")}
    else:
        summ = summarize(load(Path(a.data))); note = a.note
        if a.json:
            Path(a.json).parent.mkdir(parents=True, exist_ok=True)
            Path(a.json).write_text(json.dumps({"_note": note, **summ}, indent=1, ensure_ascii=False))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for name, keys in COMBINED.items():
        items = [(k, summ[k]) for k in keys if k in summ]
        if items:
            (out / f"{name}.svg").write_text(svg(items, note))
    for key, m in summ.items():
        print(f"## {m['title']}")
        for br, v in sorted(m["browsers"].items(), key=lambda kv: kv[1]["median"]):
            p = v.get("paired_vs_helium")
            print(f"{br:13} n={v['n']:3} med={v['median']:8.1f} IC95=[{v['ci95'][0]:.1f},{v['ci95'][1]:.1f}] IQR=[{v['q1']:.1f},{v['q3']:.1f}]"
                  + (f" vsHelium={100*(v['median_vs_helium']-1):+.1f}% pareada={100*(p['median_ratio']-1):+.1f}% ({p['below']}/{p['laps']} voltas abaixo)" if p else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
