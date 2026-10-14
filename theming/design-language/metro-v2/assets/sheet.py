#!/usr/bin/env python3
# folha de ícones (icons-dark/light.html) + tabela de contraste AA (contrastes.txt)
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); sys.argv = ['x']
from icons import ICONS, svg
import importlib.util
spec = importlib.util.spec_from_file_location('b', pathlib.Path(__file__).parent / 'build.py'); 
OUT = pathlib.Path(__file__).resolve().parent.parent
src = (OUT/'assets'/'build.py').read_text().split('def ic(')[0]
ns = {}; exec(src.replace('OUT = pathlib.Path(__file__).resolve().parent.parent', f'OUT = pathlib.Path("{OUT}")'), ns)
T = ns['T']
def lum(h):
  h = h.lstrip('#'); c = [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]
  c = [x/12.92 if x <= .03928 else ((x+.055)/1.055)**2.4 for x in c]
  return .2126*c[0]+.7152*c[1]+.0722*c[2]
def cr(a, b):
  la, lb = sorted((lum(a), lum(b)), reverse=True); return (la+.05)/(lb+.05)
pairs = [('fg','page'),('fg','frame'),('fg','panel'),('fg2','panel'),('fg3','panel'),('fg3','frame'),('link','page'),('link','panel'),('btnfg','btn'),('fg3','btn'),('fg','sel')]
lines = []
for m, t in T.items():
  for a, b in pairs:
    r = cr(t[a], t[b]); lines.append(f'{m:5} {a:5} {t[a]} sobre {b:5} {t[b]}  {r:5.2f}  {"AA" if r>=4.5 else "FALHA"}')
  lines.append(f'{m:5} branco sobre destaque {t["accent"]}  {cr("#ffffff", t["accent"]):5.2f}  {"AA" if cr("#ffffff", t["accent"])>=4.5 else "FALHA"}')
  lines.append(f'{m:5} borda de campo {t["fieldb"]} sobre {t["field"]} {cr(t["fieldb"], t["field"]):5.2f} (não texto, mínimo 3)')
(OUT/'contrastes.txt').write_text('\n'.join(lines)+'\n'); print('\n'.join(lines))
for m, t in T.items():
  cells = ''.join(f'<div class=i>{svg(n, t["fg"], 20)}<span>{n}</span></div>' for n in ICONS)
  cells2 = ''.join(f'<div class=i>{svg(n, t["fg"], 32)}</div>' for n in list(ICONS)[:12])
  (OUT/f'icons-{m}.html').write_text(f'''<!doctype html><meta charset=utf-8><style>
@font-face{{font-family:Selawik;src:url(assets/fonts/selawk.woff2)}}
body{{margin:0;width:1000px;background:{t["panel"]};color:{t["fg2"]};font:11px Selawik}}
.g{{display:flex;flex-wrap:wrap;padding:16px}} .i{{width:100px;height:64px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px}}</style>
<div class=g>{cells}</div><div class=g style="background:{t["frame"]}">{cells2}</div>''')
