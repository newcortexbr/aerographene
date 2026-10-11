#!/usr/bin/env python3
"""Captura reprodutível do chrome do aerographene para comparar com os mockups.

Stdlib + ctypes (XTest) + ImageMagick `import`/`xprop`/`xwininfo`; sem dependências globais novas.
Uso: python3 theming/fidelity/capture.py [--pkg DIR] [--out DIR] [--themes default,pixelized] [--modes sidebar,topbar]
Cada combinação tema×modo abre um navegador novo (perfil em --out/prof/), espera, captura e encerra
só o PID aberto (SIGTERM). Porta CDP 9333; nunca toca outros navegadores.
Saídas: <out>/shots/<tema>-<modo>-<cena>.png (1440x900). Cenas: home, pagina, menu-aba, menu-3pontos.
Menus nativos são janelas X próprias: cena por captura da raiz recortada na geometria da janela.
"""
import argparse, ctypes, functools, http.server, io, json, os, re, signal, subprocess, sys
import threading, time, urllib.request, uuid
from pathlib import Path

from PIL import Image, ImageDraw

PKG_DEFAULT = "/home/dasher/.cache/aero-bench/pkg-6289423/x"
PORT, SPORT = 9333, 8767
SURL = f"http://127.0.0.1:{SPORT}"
LAYOUT = {"topbar": 0, "sidebar": 2}  # helium.browser.layout: 0 clássico, 2 vertical

# ---------- site local (pinned + abas fictícias) ----------
PAGES = {  # caminho: (título, cor do favicon, letra)
    "gh": ("GitHub", (36, 41, 46), "G"), "yt": ("YouTube", (255, 0, 0), "Y"),
    "nt": ("Notion", (255, 255, 255), "N"), "go": ("Google", (66, 133, 244), "g"),
    "fg": ("Figma", (162, 89, 255), "F"), "sp": ("Spotify", (30, 215, 96), "S"),
    "tr": ("Trabalho: painel", (80, 120, 200), "T"),
    "mdn": ("MDN Web Docs", (255, 255, 255), "M"), "yt2": ("YouTube", (255, 0, 0), "Y"),
}


def icon_png(color, letter):
    im = Image.new("RGBA", (32, 32), color + (255,))
    d = ImageDraw.Draw(im)
    d.text((11, 9), letter, fill=(0, 0, 0, 255) if sum(color) > 450 else (255, 255, 255, 255))
    b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()


def start_site():
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            p = self.path.split("?")[0].strip("/")
            if p.endswith(".png") and p[:-4] in PAGES:
                _, c, l = PAGES[p[:-4]]; body, ct = icon_png(c, l), "image/png"
            elif p in PAGES:
                t = PAGES[p][0]
                body = (f'<!doctype html><meta charset=utf-8><title>{t}</title>'
                        f'<link rel=icon type=image/png href="/{p}.png">'
                        f'<body style="background:#fff;color:#111;font:16px sans-serif;padding:40px">'
                        f'<h1>{t}</h1><p>página fictícia local para captura de fidelidade.</p>').encode()
                ct = "text/html; charset=utf-8"
            else:
                self.send_error(404); return
            self.send_response(200); self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", SPORT), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# ---------- perfil semeado ----------
def seed(prof, theme, mode):
    d = Path(prof) / "Default"; d.mkdir(parents=True, exist_ok=True)
    T = "13400000000000000"; g = lambda: str(uuid.uuid4())
    def url(i, key, open_=False):
        return {"id": str(i), "guid": g(), "name": PAGES[key][0], "type": "url", "url": f"{SURL}/{key}",
                "date_added": T, "meta_info": ({"aerographene.open": "1"} if open_ else {})}
    kids = [url(10, "gh", True), url(11, "yt", True), url(12, "nt"), url(13, "go"), url(14, "fg"), url(15, "sp"),
            {"id": "20", "guid": g(), "name": "Trabalho", "type": "folder", "date_added": T, "date_modified": T,
             "meta_info": {"aerographene.folder": "1"}, "children": [url(21, "tr")]}]
    root = {"id": "5", "guid": g(), "name": "aerographene", "type": "folder", "date_added": T, "date_modified": T,
            "meta_info": {"aerographene.pinned": "1"}, "children": kids}
    bm = {"version": 1, "roots": {
        "bookmark_bar": {"id": "1", "guid": "0bc5d13f-2cba-5d74-951f-3f233fe6c908", "name": "Barra", "type": "folder",
                         "date_added": T, "date_modified": T, "children": [root]},
        "other": {"id": "2", "guid": "82b081ec-3dd3-529c-8475-ab6c344590dd", "name": "Outros", "type": "folder",
                  "date_added": T, "date_modified": T, "children": []},
        "synced": {"id": "3", "guid": "4cf2e351-0e85-532b-bb37-df045d8f8d0f", "name": "Mobile", "type": "folder",
                   "date_added": T, "date_modified": T, "children": []}}}
    (d / "Bookmarks").write_text(json.dumps(bm))
    (d / "Preferences").write_text(json.dumps({"helium": {"browser": {"layout": LAYOUT[mode]}},
                                              "aerographene": {"theme": theme}}))


# ---------- processo, janela, captura ----------
def targets():
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=1) as r:
            return [t for t in json.load(r) if t["type"] == "page"]
    except Exception:
        return None


def port_free():
    return targets() is None


def find_window(pid, tries=100):
    for _ in range(tries):
        out = subprocess.run(["xprop", "-root", "_NET_CLIENT_LIST"], capture_output=True, text=True).stdout
        for w in re.findall(r"0x[0-9a-f]+", out):
            x = subprocess.run(["xprop", "-id", w, "_NET_WM_PID"], capture_output=True, text=True).stdout
            if x.strip().endswith(f"= {pid}"):
                return w
        time.sleep(0.2)


def geom(w):
    """origem absoluta e tamanho da janela, via XTranslateCoordinates/XGetGeometry (sem xwininfo)."""
    xl = ctypes.CDLL("libX11.so.6"); xl.XOpenDisplay.restype = ctypes.c_void_p
    d = ctypes.c_void_p(xl.XOpenDisplay(None)); win = ctypes.c_ulong(int(w, 16))
    root = ctypes.c_ulong(xl.XDefaultRootWindow(d))
    ax, ay, ch = ctypes.c_int(), ctypes.c_int(), ctypes.c_ulong()
    xl.XTranslateCoordinates(d, win, root, 0, 0, ctypes.byref(ax), ctypes.byref(ay), ctypes.byref(ch))
    r, gx, gy, gw, gh, bw, dp = ctypes.c_ulong(), ctypes.c_int(), ctypes.c_int(), ctypes.c_uint(), ctypes.c_uint(), ctypes.c_uint(), ctypes.c_uint()
    xl.XGetGeometry(d, win, ctypes.byref(r), ctypes.byref(gx), ctypes.byref(gy), ctypes.byref(gw), ctypes.byref(gh), ctypes.byref(bw), ctypes.byref(dp))
    xl.XCloseDisplay(d)
    return ax.value, ay.value, gw.value, gh.value


class X:  # XTest via ctypes
    def __init__(self):
        self.x = ctypes.CDLL("libX11.so.6"); self.t = ctypes.CDLL("libXtst.so.6")
        self.x.XOpenDisplay.restype = ctypes.c_void_p
        self.d = ctypes.c_void_p(self.x.XOpenDisplay(None))
    def move(self, x, y):
        self.t.XTestFakeMotionEvent(self.d, -1, int(x), int(y), 0); self.x.XFlush(self.d); time.sleep(0.25)
    def click(self, x, y, button=1):
        self.move(x, y)
        for down in (1, 0):
            self.t.XTestFakeButtonEvent(self.d, button, down, 0); self.x.XFlush(self.d); time.sleep(0.08)
        time.sleep(0.6)
    def esc(self):
        self.x.XStringToKeysym.restype = ctypes.c_ulong
        kc = self.x.XKeysymToKeycode(self.d, ctypes.c_ulong(self.x.XStringToKeysym(b"Escape")))
        for down in (1, 0):
            self.t.XTestFakeKeyEvent(self.d, kc, down, 0); self.x.XFlush(self.d); time.sleep(0.05)
        time.sleep(0.4)


class _Attr(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int), ("width", ctypes.c_int), ("height", ctypes.c_int),
                ("border_width", ctypes.c_int), ("depth", ctypes.c_int), ("visual", ctypes.c_void_p),
                ("root", ctypes.c_ulong), ("cls", ctypes.c_int), ("bit_gravity", ctypes.c_int),
                ("win_gravity", ctypes.c_int), ("backing_store", ctypes.c_int), ("backing_planes", ctypes.c_ulong),
                ("backing_pixel", ctypes.c_ulong), ("save_under", ctypes.c_int), ("colormap", ctypes.c_ulong),
                ("map_installed", ctypes.c_int), ("map_state", ctypes.c_int), ("all_event_masks", ctypes.c_long),
                ("your_event_masks", ctypes.c_long), ("do_not_propagate_mask", ctypes.c_long),
                ("override_redirect", ctypes.c_int), ("screen", ctypes.c_void_p)]


def mapped_toplevels():
    """{id: (x, y, w, h)} de filhos mapeados da raiz (inclui menus override-redirect)."""
    xl = ctypes.CDLL("libX11.so.6"); xl.XOpenDisplay.restype = ctypes.c_void_p
    d = ctypes.c_void_p(xl.XOpenDisplay(None)); root = ctypes.c_ulong(xl.XDefaultRootWindow(d))
    r, par, kids, n = ctypes.c_ulong(), ctypes.c_ulong(), ctypes.POINTER(ctypes.c_ulong)(), ctypes.c_uint()
    xl.XQueryTree(d, root, ctypes.byref(r), ctypes.byref(par), ctypes.byref(kids), ctypes.byref(n))
    out = {}
    for i in range(n.value):
        at = _Attr()
        if xl.XGetWindowAttributes(d, ctypes.c_ulong(kids[i]), ctypes.byref(at)) and at.map_state == 2 and at.width > 1:
            out[kids[i]] = (at.x, at.y, at.width, at.height)
    xl.XCloseDisplay(d)
    return out


def shot(w, geo, base, path):
    """captura a janela principal e cola por cima popups novos (menus), pois a raiz não é capturável aqui."""
    subprocess.run(["import", "-window", w, str(path)], check=True)
    im = Image.open(path).convert("RGB")
    for wid, (x, y, ww, hh) in mapped_toplevels().items():
        if wid in base or (x, y, ww, hh) == geo:
            continue
        tmp = Path(str(path) + ".pop.png")
        if subprocess.run(["import", "-window", hex(wid), str(tmp)]).returncode == 0:
            im.paste(Image.open(tmp).convert("RGB"), (x - geo[0], y - geo[1])); tmp.unlink()
    im.save(path)


def new_ntp():
    """abre a nova aba (página inicial do tema) por CDP; ela fica ativa, como no mockup."""
    urllib.request.urlopen(urllib.request.Request(
        f"http://127.0.0.1:{PORT}/json/new?chrome://newtab/", method="PUT"), timeout=5).read()


def activate(title_part):
    for t in targets() or []:
        if title_part in t.get("title", ""):
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/activate/{t['id']}", timeout=3).read(); return True


# coordenadas (px da janela 1440x900) dos alvos de clique, por modo; ajustadas pelas capturas reais
# a janela real tem 1366x740 (tela 1366x768); o botão de menu fica a 122 px da borda direita
CLICK = {"sidebar": {"tab": (110, 160), "menu": (1244, 22)},
         "topbar": {"tab": (230, 20), "menu": (1343, 61)}}


def run_combo(pkg, out, theme, mode, wait):
    prof = out / "prof" / f"{theme}-{mode}"; seed(prof, theme, mode)
    shots = out / "shots"; shots.mkdir(parents=True, exist_ok=True)
    binp = next(Path(pkg).glob("aerographene-*")) / "chrome"
    args = [str(binp), f"--user-data-dir={prof}", "--ozone-platform=x11", "--no-first-run",
            "--no-default-browser-check", "--window-size=1440,900", "--window-position=0,0", "--lang=pt-BR",
            f"--remote-debugging-port={PORT}", f"{SURL}/mdn", f"{SURL}/yt2"]
    env = dict(os.environ, LANGUAGE="pt_BR", LANG="pt_BR.UTF-8")
    lf = open(out / f"{theme}-{mode}.chrome.log", "w")
    p = subprocess.Popen(args, stdout=lf, stderr=subprocess.STDOUT, env=env)
    print(f"[{theme}-{mode}] pid={p.pid}", flush=True)
    names = []
    try:
        w = find_window(p.pid)
        if not w: raise RuntimeError("janela não encontrada")
        time.sleep(wait)
        new_ntp()
        time.sleep(3)
        geo = geom(w); print(f"  janela {w} geom={geo}")
        base = set(mapped_toplevels()); x = X(); c = CLICK[mode]
        x.move(geo[0] + 1300, geo[1] + 600)  # fora de qualquer controle
        time.sleep(0.5)
        for name, fn in (
            ("home", lambda: None),
            ("menu-aba", lambda: x.click(geo[0] + c["tab"][0], geo[1] + c["tab"][1], 3)),
            ("menu-3pontos", lambda: x.click(geo[0] + c["menu"][0], geo[1] + c["menu"][1])),
            ("pagina", lambda: activate("MDN")),
        ):
            fn(); time.sleep(0.8)
            shot(w, geo, base, shots / f"{theme}-{mode}-{name}.png"); names.append(name)
            x.esc(); x.move(geo[0] + 1300, geo[1] + 600); time.sleep(0.4)
    finally:
        try: os.kill(p.pid, signal.SIGTERM)
        except OSError: pass
        try: p.wait(30); print(f"  encerrado pid={p.pid}")
        except subprocess.TimeoutExpired: print(f"  AINDA VIVO pid={p.pid}")
        time.sleep(1.5)
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg", default=PKG_DEFAULT); ap.add_argument("--out", default="/tmp/fid0-out")
    ap.add_argument("--themes", default="default,pixelized"); ap.add_argument("--modes", default="sidebar,topbar")
    ap.add_argument("--wait", type=float, default=9)
    a = ap.parse_args(); out = Path(a.out)
    if not port_free(): sys.exit(f"porta {PORT} ocupada; abortando sem tocar em nada")
    start_site()
    for th in a.themes.split(","):
        for md in a.modes.split(","):
            run_combo(a.pkg, out, th, md, a.wait)


if __name__ == "__main__":
    main()
