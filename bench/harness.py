#!/usr/bin/env python3
"""harness de medição do aerographene (linha de base).

mede, para cada navegador:
- startup: do exec até a página inicial carregar e pintar (beacon HTTP local).
- ram: soma do PSS de todos os processos do navegador com N abas sintéticas,
  depois de um tempo de assentamento.

perfil novo por navegador. modo "first": perfil recriado a cada repetição (inclui a
criação do perfil). modo "warm": perfil criado uma vez, repetições reaproveitam.
"cold" de verdade (cache de página do kernel limpo) exige root: use --drop-caches.

sem dependências fora da stdlib. só Linux.
"""
from __future__ import annotations

import argparse
import http.server
import json
import os
import shutil
import signal
import statistics
import subprocess
import sys
import threading
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGES = HERE / "pages"
BROWSERS = HERE / "browsers"
OUT = HERE / "out"

CHROMIUM_ARGS = [
    "--no-first-run",
    "--no-default-browser-check",
    "--password-store=basic",
    "--disable-session-crashed-bubble",
]

FIREFOX_PREFS = {
    "browser.shell.checkDefaultBrowser": False,
    "browser.aboutwelcome.enabled": False,
    "browser.startup.homepage_override.mstone": "ignore",
    "startup.homepage_welcome_url": "",
    "startup.homepage_welcome_url.additional": "",
    "datareporting.policy.dataSubmissionPolicyBypassNotification": True,
    "browser.sessionstore.resume_from_crash": False,
    "browser.tabs.warnOnClose": False,
    "browser.warnOnQuit": False,
    "toolkit.telemetry.reportingpolicy.firstRun": False,
}


def browser_defs() -> dict[str, dict]:
    return {
        "aerographene": {"kind": "chromium", "bin": BROWSERS / "aerographene" / "chrome"},
        "ungoogled": {"kind": "chromium", "bin": BROWSERS / "ungoogled" / "chrome"},
        "helium": {"kind": "chromium", "bin": BROWSERS / "helium" / "chrome"},
        "thorium": {"kind": "chromium", "bin": BROWSERS / "thorium" / "AppRun"},
        "zen": {"kind": "firefox", "bin": Path(shutil.which("zen-browser") or "/usr/bin/zen-browser")},
    }


# ---------------------------------------------------------------- servidor local

class Beacons:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)
        self.hits: dict[str, list[float]] = {}

    def hit(self, run: str) -> None:
        with self.cond:
            self.hits.setdefault(run, []).append(time.monotonic())
            self.cond.notify_all()

    def wait(self, run: str, count: int, timeout: float) -> list[float]:
        deadline = time.monotonic() + timeout
        with self.cond:
            while len(self.hits.get(run, [])) < count:
                left = deadline - time.monotonic()
                if left <= 0:
                    break
                self.cond.wait(left)
            return list(self.hits.get(run, []))


def start_server(beacons: Beacons) -> tuple[http.server.ThreadingHTTPServer, int]:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(PAGES), **kw)

        def do_GET(self):  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/ready":
                run = urllib.parse.parse_qs(parsed.query).get("run", [""])[0]
                beacons.hit(run)
                self.send_response(204)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
            super().do_GET()

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


# ---------------------------------------------------------------- processos

def proc_tree(root: int) -> list[int]:
    children: dict[int, list[int]] = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open(f"/proc/{d}/stat", "rb") as f:
                stat = f.read().decode(errors="replace")
            ppid = int(stat.rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            continue
        children.setdefault(ppid, []).append(int(d))
    out, stack = [], [root]
    while stack:
        p = stack.pop()
        out.append(p)
        stack.extend(children.get(p, []))
    return out


def pss_kib(pid: int) -> int:
    try:
        with open(f"/proc/{pid}/smaps_rollup") as f:
            for line in f:
                if line.startswith("Pss:"):
                    return int(line.split()[1])
    except OSError:
        pass
    return 0


def kill_tree(root: int) -> None:
    pids = proc_tree(root)
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for p in reversed(pids):
            try:
                os.kill(p, sig)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and any(Path(f"/proc/{p}").exists() for p in pids):
            time.sleep(0.1)


# ---------------------------------------------------------------- navegador

def prepare_profile(name: str, kind: str, path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    if kind == "firefox":
        lines = [f'user_pref("{k}", {json.dumps(v)});' for k, v in FIREFOX_PREFS.items()]
        (path / "user.js").write_text("\n".join(lines) + "\n")


def command(defn: dict, profile: Path, urls: list[str]) -> list[str]:
    if defn["kind"] == "chromium":
        return [str(defn["bin"]), f"--user-data-dir={profile}", *CHROMIUM_ARGS, *urls]
    return [str(defn["bin"]), "--profile", str(profile), "--no-remote", "--new-instance", *urls]


def power_state() -> dict:
    """perfil de energia e governor no momento da medição (resultados só comparam com o mesmo estado)."""
    def read(path):
        try:
            return Path(path).read_text().strip()
        except OSError:
            return None
    try:
        profile = subprocess.run(["powerprofilesctl", "get"], capture_output=True, text=True, timeout=5).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        profile = None
    return {
        "power_profile": profile,
        "governor": read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"),
        "epp": read("/sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference"),
        "on_ac": read("/sys/class/power_supply/AC/online") or read("/sys/class/power_supply/ACAD/online"),
    }


def drop_caches() -> None:
    subprocess.run(["sudo", "-n", "sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches"], check=True)


def run_once(name, defn, profile, base, beacons, tabs, settle, timeout, run_id):
    if tabs:
        urls = [f"{base}/tab.html?run={run_id}&i={i}" for i in range(tabs)]
    else:
        urls = [f"{base}/start.html?run={run_id}"]
    env = dict(os.environ)
    t0 = time.monotonic()
    proc = subprocess.Popen(command(defn, profile, urls), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)
    try:
        hits = beacons.wait(run_id, len(urls), timeout)
        res = {
            "browser": name, "run": run_id, "tabs": tabs or 1,
            "loaded": len(hits),
            "first_ms": round((hits[0] - t0) * 1000, 1) if hits else None,
            "all_ms": round((hits[-1] - t0) * 1000, 1) if len(hits) == len(urls) else None,
        }
        if tabs:
            time.sleep(settle)
            pids = proc_tree(proc.pid)
            res["procs"] = len(pids)
            res["pss_mib"] = round(sum(pss_kib(p) for p in pids) / 1024, 1)
        return res
    finally:
        kill_tree(proc.pid)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass


def summarize(rows: list[dict]) -> None:
    by: dict[tuple, list[dict]] = {}
    for r in rows:
        by.setdefault((r["browser"], r["mode"], r["tabs"]), []).append(r)
    print("\nbrowser    mode   tabs  n  first_ms(med)  all_ms(med)  pss_mib(med)  procs(med)  loaded(min)")
    for (b, m, t), rs in sorted(by.items()):
        def med(k):
            v = [r[k] for r in rs if r.get(k) is not None]
            return f"{statistics.median(v):.1f}" if v else "-"
        print(f"{b:<10} {m:<6} {t:>4} {len(rs):>2}  {med('first_ms'):>13}  {med('all_ms'):>11}"
              f"  {med('pss_mib'):>12}  {med('procs'):>10}  {min(r['loaded'] for r in rs):>11}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--browsers", default="ungoogled,helium,thorium,zen")
    ap.add_argument("--mode", choices=["first", "warm"], default="warm")
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--tabs", type=int, default=0, help="0 = só startup; N = abre N abas e mede PSS")
    ap.add_argument("--settle", type=float, default=15.0, help="segundos antes de medir PSS")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--pause", type=float, default=2.0, help="pausa entre execuções")
    ap.add_argument("--quick", action="store_true",
                    help="rodada rápida do dia a dia: repeat 3, settle 6 s, pause 1 s")
    ap.add_argument("--require-profile", default="performance",
                    help="aborta se o perfil de energia for outro ('' desliga a checagem)")
    ap.add_argument("--drop-caches", action="store_true", help="limpa page cache antes de cada execução (sudo -n)")
    args = ap.parse_args()
    if args.quick:
        args.repeat, args.settle, args.pause = 3, 6.0, 1.0
    power = power_state()
    print("energia:", json.dumps(power))
    if args.require_profile and power["power_profile"] != args.require_profile:
        sys.exit(f"perfil de energia é {power['power_profile']!r}, esperado {args.require_profile!r}")

    defs = browser_defs()
    names = [n.strip() for n in args.browsers.split(",") if n.strip()]
    for n in names:
        if n not in defs:
            sys.exit(f"navegador desconhecido: {n}")
        if not defs[n]["bin"].exists():
            sys.exit(f"binário não encontrado para {n}: {defs[n]['bin']} (rode bench/fetch-browsers.sh)")

    OUT.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    outfile = OUT / f"results-{stamp}.jsonl"
    beacons = Beacons()
    srv, port = start_server(beacons)
    base = f"http://127.0.0.1:{port}"
    rows: list[dict] = []
    try:
        for name in names:
            defn = defs[name]
            profile = OUT / "profiles" / name
            if args.mode == "warm":
                prepare_profile(name, defn["kind"], profile)
                run_once(name, defn, profile, base, beacons, 0, 0, args.timeout, f"{name}-init")
                time.sleep(args.pause)
            for i in range(args.repeat):
                if args.mode == "first":
                    prepare_profile(name, defn["kind"], profile)
                if args.drop_caches:
                    drop_caches()
                run_id = f"{name}-{args.mode}-{args.tabs}-{i}-{stamp}"
                r = run_once(name, defn, profile, base, beacons, args.tabs, args.settle, args.timeout, run_id)
                r.update(mode=args.mode, i=i, ts=time.time(), **power)
                rows.append(r)
                with outfile.open("a") as f:
                    f.write(json.dumps(r) + "\n")
                print(json.dumps(r), flush=True)
                time.sleep(args.pause)
    finally:
        srv.shutdown()
    summarize(rows)
    print(f"\nresultados: {outfile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
