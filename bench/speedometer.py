#!/usr/bin/env python3
"""Speedometer 3.1 automatizado via CDP, rodadas intercaladas e rotacionadas. Só stdlib.

Serve uma cópia local do benchmark (bench/cache/Speedometer3.1, ignorada pelo git):
  git clone --depth 1 -b release/3.1 https://github.com/WebKit/Speedometer.git bench/cache/Speedometer3.1

Cada execução: perfil temporário novo, janela de tamanho fixo, remote debugging em porta livre,
abre `index.html?startAutomatically`, espera `benchmarkClient._hasResults` e lê o score.
Gate antes de cada execução: perfil de energia performance, load1 < 1, nenhum outro navegador aberto.

  python3 bench/speedometer.py --laps 5 --browsers aerographene,helium,thorium,chrome \
      --bin aerographene=/tmp/aero-v03-x/<pacote>/chrome --bin chrome=/tmp/chrome-off/x/opt/google/chrome/chrome \
      --out /tmp/speedo-out

Grava `speedo-lap<N>-<nome>-results.jsonl` em --out (lido por bench/charts.py). Não edita harness.py.
"""
import argparse, base64, http.server, json, os, shutil, socket, struct, subprocess
import sys, tempfile, threading, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

HERE = Path(__file__).resolve().parent
SITE = HERE / "cache" / "Speedometer3.1"
OTHER_BROWSERS = {"chrome", "chromium", "helium", "thorium", "thorium-browser", "zen", "zen-bin", "firefox",
                  "brave", "vivaldi-bin", "opera", "msedge", "chrome_crashpad"}


# ------------------------------------------------------------------ CDP mínimo (WebSocket)

class WS:
    def __init__(self, url):
        host, rest = url[len("ws://"):].split("/", 1)
        h, p = host.split(":")
        self.s = socket.create_connection((h, int(p)), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /{rest} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        if b" 101 " not in buf.split(b"\r\n")[0]:
            raise RuntimeError("handshake ws falhou")
        self.buf = buf.split(b"\r\n\r\n", 1)[1]
        self.id = 0

    def _read(self, n):
        while len(self.buf) < n:
            c = self.s.recv(65536)
            if not c:
                raise EOFError
            self.buf += c
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _send(self, data):
        mask = os.urandom(4)
        n = len(data)
        hdr = bytes([0x81]) + (bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack(">H", n)
                               if n < 65536 else bytes([0x80 | 127]) + struct.pack(">Q", n))
        self.s.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _recv(self):
        msg = b""
        while True:
            b0, b1 = self._read(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            payload = self._read(n)
            op = b0 & 0x0F
            if op == 9:  # ping
                continue
            msg += payload
            if b0 & 0x80:
                return msg

    def call(self, method, **params):
        self.id += 1
        self._send(json.dumps({"id": self.id, "method": method, "params": params}).encode())
        while True:
            m = json.loads(self._recv())
            if m.get("id") == self.id:
                if "error" in m:
                    raise RuntimeError(m["error"])
                return m["result"]

    def eval(self, expr):
        r = self.call("Runtime.evaluate", expression=expr, returnByValue=True)
        return r.get("result", {}).get("value")


# ------------------------------------------------------------------ gate

def load1():
    return float(open("/proc/loadavg").read().split()[0])


def foreign_browsers():
    found = set()
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                c = Path(f"/proc/{d}/comm").read_text().strip()
            except OSError:
                continue
            if c in OTHER_BROWSERS:
                found.add(c)
    return sorted(found)


def gate(limit=1.0, window_s=3600, step=10, announce=600):
    """espera load1 < limit e nenhum navegador; (True, info) ou (False, motivo) após window_s."""
    t0, last = time.monotonic(), 0
    while True:
        prof = harness.power_state()["power_profile"]
        if prof != "performance":
            return False, f"perfil de energia '{prof}' (exige performance)"
        l, fb = load1(), foreign_browsers()
        if l < limit and not fb:
            return True, {"load1": l}
        if time.monotonic() - t0 > window_s:
            return False, f"sem janela ociosa em {window_s}s (load1={l}, navegadores={fb})"
        if time.monotonic() - last > announce:
            print(f"  gate: aguardando (load1={l}, navegadores={fb})", flush=True)
            last = time.monotonic()
        time.sleep(step)


# ------------------------------------------------------------------ execução

def serve():
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(SITE), **k)
        def log_message(self, *a):
            pass
        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def run_once(name, defn, port, size, iterations, timeout):
    prof = Path(tempfile.mkdtemp(prefix=f"speedo-{name}-"))
    url = f"http://127.0.0.1:{port}/index.html?startAutomatically&iterationCount={iterations}"
    argv = [str(defn["bin"]), f"--user-data-dir={prof}", *harness.CHROMIUM_ARGS,
            "--remote-debugging-port=0", "--remote-allow-origins=*",
            f"--window-size={size[0]},{size[1]}", "--window-position=0,0", url]
    proc = subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    t0 = time.monotonic()
    res = {"browser": name, "iterations": iterations, **harness.power_state()}
    try:
        dbg = prof / "DevToolsActivePort"
        while not dbg.exists():
            if time.monotonic() - t0 > 60 or proc.poll() is not None:
                raise RuntimeError("DevToolsActivePort não apareceu")
            time.sleep(0.2)
        dport = int(dbg.read_text().split()[0])
        ver = json.load(urllib.request.urlopen(f"http://127.0.0.1:{dport}/json/version", timeout=10))
        res["version"] = ver.get("Browser")
        ws = None
        while ws is None:
            pages = [t for t in json.load(urllib.request.urlopen(f"http://127.0.0.1:{dport}/json/list", timeout=10))
                     if t.get("type") == "page" and f":{port}/" in t.get("url", "")]
            if pages:
                ws = WS(pages[0]["webSocketDebuggerUrl"])
            elif time.monotonic() - t0 > 60:
                raise RuntimeError("aba do Speedometer não apareceu")
            else:
                time.sleep(0.3)
        res["inner"] = ws.eval("[innerWidth, innerHeight]")
        t1 = time.monotonic()
        while True:
            if time.monotonic() - t1 > timeout:
                raise RuntimeError("timeout")
            time.sleep(5)
            if ws.eval("globalThis.benchmarkClient && benchmarkClient._hasResults"):
                break
        res["wall_s"] = round(time.monotonic() - t1, 1)
        res["score_text"] = ws.eval("document.getElementById('result-number').textContent")
        res["delta_text"] = ws.eval("document.getElementById('confidence-number').textContent")
        vals = ws.eval("benchmarkClient._measuredValuesList.map(v => v.score)")
        res["iter_scores"] = vals
        res["score"] = round(sum(vals) / len(vals), 3) if vals else None
        if res["score_text"] == "Error":
            res["score"] = None
        res["load1_end"] = load1()
    except Exception as e:  # noqa: BLE001
        res["error"] = str(e)
        res["score"] = None
    finally:
        harness.kill_tree(proc.pid)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        shutil.rmtree(prof, ignore_errors=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--browsers", required=True)
    ap.add_argument("--laps", type=int, default=5)
    ap.add_argument("--iterations", type=int, default=10, help="iterationCount do Speedometer (oficial: 10)")
    ap.add_argument("--bin", action="append", default=[], help="nome=caminho")
    ap.add_argument("--out", required=True)
    ap.add_argument("--window", default="1280x800")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--gate-window", type=int, default=3600, help="s sem janela ociosa antes de desistir")
    a = ap.parse_args()
    if not (SITE / "index.html").exists():
        sys.exit(f"falta {SITE} (ver docstring)")
    names = a.browsers.split(",")
    defs = harness.browser_defs()
    defs.setdefault("chrome", {"kind": "chromium", "bin": Path("/nonexistent")})
    for b in a.bin:
        k, v = b.split("=", 1)
        defs[k] = {"kind": "chromium", "bin": Path(v)}
    size = tuple(int(x) for x in a.window.split("x"))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    srv, port = serve()
    for lap in range(a.laps):
        k = lap % len(names)
        for n in names[k:] + names[:k]:
            ok, info = gate(window_s=a.gate_window)
            if not ok:
                print(f"ABORTADO: {info}", file=sys.stderr)
                return 2
            r = run_once(n, defs[n], port, size, a.iterations, a.timeout)
            r.update(lap=lap, ts=time.strftime("%FT%T"), gate_load1=info["load1"])
            with (out / f"speedo-lap{lap}-{n}-results.jsonl").open("a") as f:
                f.write(json.dumps(r) + "\n")
            print(f"{time.strftime('%T')} lap={lap} {n}: score={r['score']} ({r.get('wall_s')}s) {r.get('error', '')}", flush=True)
            time.sleep(5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
