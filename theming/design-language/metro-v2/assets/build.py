#!/usr/bin/env python3
# metro-v2: mesma composição da print real; só pele (cor, fonte, borda, ícone) no idioma do Windows 10.
import pathlib
OUT = pathlib.Path(__file__).resolve().parent.parent
T = {
 'dark': dict(frame='#1f1f1f', side='#1f1f1f', panel='#2b2b2b', page='#000000', line='#3c3c3c',
   fg='#ffffff', fg2='#c8c8c8', fg3='#a8a8a8', hover='#333333', sel='#3e3e3e', btn='#333333', btnfg='#ffffff',
   box='#1f1f1f', field='#000000', fieldb='#666666', accent='#0072cb', link='#4cc2ff', kbd='#333333'),
 'light': dict(frame='#f2f2f2', side='#f2f2f2', panel='#e6e6e6', page='#ffffff', line='#d6d6d6',
   fg='#000000', fg2='#333333', fg3='#4a4a4a', hover='#e0e0e0', sel='#cccccc', btn='#cccccc', btnfg='#000000',
   box='#f2f2f2', field='#ffffff', fieldb='#7a7a7a', accent='#0063b1', link='#0063b1', kbd='#d9d9d9'),
}
import sys; sys.path.insert(0, str(OUT / 'assets'))
from icons import svg
def ic(name, c, s=16):
  return svg(name, c, s)

def tile(name, bg, s=20):
  return f'<span class="tile" style="width:{s}px;height:{s}px;background:{bg}">{ic(name, "#ffffff", s-6)}</span>'

def page(mode):
  t = T[mode]; a = t['accent']
  css = f"""
@font-face{{font-family:'Selawik';font-weight:300;src:url('assets/fonts/selawkl.woff2')}}
@font-face{{font-family:'Selawik';font-weight:400;src:url('assets/fonts/selawk.woff2')}}
@font-face{{font-family:'Selawik';font-weight:600;src:url('assets/fonts/selawksb.woff2')}}
@font-face{{font-family:'Selawik';font-weight:700;src:url('assets/fonts/selawkb.woff2')}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1599px;height:872px;overflow:hidden;background:{t['frame']};color:{t['fg']};font:13px 'Selawik','Segoe UI',sans-serif;position:relative}}
.a{{position:absolute}} .c{{display:flex;align-items:center;justify-content:center}}
.tile{{display:inline-flex;align-items:center;justify-content:center;flex:none}}
.btn{{background:{t['btn']};color:{t['btnfg']};font-size:12px}}
.btn.p{{background:{a};color:#fff}} .btn.off{{color:{t['fg3']}}}
kbd{{background:{t['kbd']};color:{t['fg']};font:12px 'Noto Sans Mono',monospace;padding:1px 5px;margin-right:6px}}
"""
  h = [f'<!doctype html><meta charset="utf-8"><title>metro-v2 {mode}</title><style>{css}</style>']
  def A(x, y, w, hh, inner='', st='', cl=''):
    h.append(f'<div class="a {cl}" style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;{st}">{inner}</div>')
  # toolbar: mesma posição de todos os controles da print
  for x, n, c in [(6, 'side', t['fg']), (45, 'back', t['fg3']), (82, 'fwd', t['fg3']), (118, 'reload', t['fg'])]:
    A(x, 7, 32, 32, ic(n, c), cl='c')
  A(479, 6, 640, 34, '', f"background:{t['field']};border:2px solid {t['fieldb']}")
  A(484, 10, 116, 26, f'{tile("globe", a, 18)}<span style="margin-left:6px;font-weight:600">aerographene</span>',
    f"background:{t['btn']};display:flex;align-items:center;padding-left:4px")
  A(600, 6, 410, 34, f'<span style="color:{t["fg2"]}">aerographene://</span>notes/?new=1', '', cl='c')
  A(1058, 7, 32, 32, ic('tune', t['fg2']), cl='c'); A(1086, 7, 32, 32, ic('link', t['fg2']), cl='c')
  A(1393, 7, 32, 32, ic('shield', t['fg']), cl='c')
  A(1428, 7, 30, 32, ic('user', '#ffffff', 18), f'background:{a}', cl='c')
  A(1461, 7, 32, 32, ic('more', t['fg']), cl='c')
  for x, n in [(1500, 'min'), (1532, 'max'), (1565, 'close')]:
    A(x, 7, 32, 32, ic(n, t['fg'], 14), cl='c')
  A(0, 46, 1599, 1, '', f'background:{t["line"]}')
  # sidebar de abas
  A(0, 47, 208, 825, '', f'background:{t["side"]}')
  A(11, 54, 84, 40, f'{tile("chat", "#107c10", 22)}<span style="margin-left:8px">Whats</span>',
    f"background:{t['panel']};display:flex;align-items:center;padding-left:8px")
  A(87, 57, 5, 5, '', f'background:{a}')
  A(11, 100, 185, 1, '', f'background:{t["line"]}')
  rows = [(122, 'plus', 'New tab', None, False), (153, 'gear', 'Settings – Appearan', '#5c2d91', False),
          (187, 'globe', 'New Tab', '#0078d7', False), (221, 'doc', 'o: vault', '#0063b1', True),
          (255, 'term', 't: workspace 1', '#4c4a48', False)]
  for y, n, txt, bg, act in rows:
    st = 'display:flex;align-items:center;padding-left:9px;' + (f'background:{t["sel"]};' if act else '')
    icon = ic(n, t['fg'], 16) if bg is None else tile(n, bg, 20)
    close = '' if bg is None else f'<span class="a c" style="right:4px;top:5px;width:20px;height:20px">{ic("close", t["fg"], 12)}</span>'
    A(10, y, 186, 30, f'{icon}<span style="margin-left:10px;white-space:nowrap;overflow:hidden;width:118px">{txt}</span>{close}', st)
    if act:
      A(10, y, 3, 30, '', f'background:{a}')
  A(0, 826, 208, 1, '', f'background:{t["line"]}')
  A(6, 830, 32, 32, ic('down', t['fg']), cl='c'); A(42, 830, 32, 32, ic('ext', t['fg']), cl='c')
  A(208, 47, 1, 825, '', f'background:{t["line"]}')
  # painel de notas (WebUI), mesma composição
  A(209, 47, 259, 825, '', f'background:{t["panel"]}')
  A(221, 52, 120, 24, f'<span style="color:{t["fg2"]};font-size:11px">VAULT</span><span style="margin-left:8px;font-size:15px;font-weight:300">vault</span>',
    'display:flex;align-items:center')
  A(342, 52, 113, 22, 'escolher pasta', cl='c btn')
  A(217, 88, 77, 24, '+ nota', cl='c btn p'); A(300, 88, 77, 24, '+ pasta', cl='c btn off'); A(383, 88, 77, 24, 'buscar', cl='c btn')
  A(217, 126, 243, 29, f'<span style="color:{t["fg3"]}">buscar na vault</span>',
    f"background:{t['field']};border:2px solid {t['fieldb']};display:flex;align-items:center;padding-left:8px")
  for i, n in enumerate(['agents', 'human', 'meta']):
    A(221, 170 + i * 22, 200, 20, n, f'color:{t["link"]};display:flex;align-items:center')
  A(209, 822, 259, 1, '', f'background:{t["line"]}')
  A(221, 827, 250, 20, f'<kbd>Ctrl+S</kbd><span style="color:{t["fg2"]};margin-right:14px">salvar</span><kbd>Ctrl+N</kbd><span style="color:{t["fg2"]}">nova nota</span>',
    'font-size:12px;display:flex;align-items:center')
  A(221, 848, 250, 20, f'<kbd>Ctrl+K</kbd><span style="color:{t["fg2"]}">buscar</span>', 'font-size:12px;display:flex;align-items:center')
  A(468, 47, 6, 825, '', f'background:{t["line"]}')
  # página (WebUI notas)
  A(474, 47, 1125, 825, '', f'background:{t["page"]}')
  A(486, 52, 300, 24, 'sem nota aberta', 'font-size:15px;font-weight:300;display:flex;align-items:center')
  for x, w, n in [(1381, 58, 'salvar'), (1447, 73, 'renomear'), (1528, 59, 'apagar')]:
    A(x, 52, w, 22, n, cl='c btn off')
  A(474, 82, 1125, 1, '', f'background:{t["line"]}')
  A(627, 181, 820, 145, '', f'background:{t["box"]}')
  A(647, 200, 300, 22, 'nenhuma nota aberta', f'color:{t["link"]};font-size:15px;font-weight:300')
  for i, (k, v) in enumerate([('Ctrl+N', 'criar uma nota'), ('Ctrl+K', 'buscar na vault'), ('Ctrl+S', 'salvar a nota aberta')]):
    A(647, 229 + i * 27, 400, 22, f'<kbd>{k}</kbd>{v}', 'display:flex;align-items:center;font-size:14px')
  A(474, 843, 1125, 1, '', f'background:{t["line"]}')
  A(1300, 846, 287, 22, '0 notas visíveis', f'color:{t["fg2"]};font-size:12px;display:flex;align-items:center;justify-content:flex-end')
  return '\n'.join(h)

for m in T:
  (OUT / f'{m}.html').write_text(page(m))
