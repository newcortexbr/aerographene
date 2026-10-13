#!/usr/bin/env python3
"""PSS por processo (10 abas sintéticas) para um navegador; reutiliza bench/harness.py sem editá-lo.

  python3 bench/pss_proc.py --browser aerographene --bin /caminho/chrome --repeat 3 --out saida.json
Agrupa por tipo (--type=) e, para o processo do navegador, soma Pss anônimo/arquivo/shmem (smaps_rollup).
"""
import argparse, json, statistics as st, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402


def cmdline(pid):
    try:
        return Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
    except OSError:
        return []


def kind(args):
    for x in args:
        if x.startswith(b"--type="):
            t = x[7:].decode()
            if t == "utility":
                for y in args:
                    if y.startswith(b"--utility-sub-type="):
                        return "utility:" + y.split(b".")[-1].decode()
            return t
    return "browser"


def rollup(pid):
    d = {}
    try:
        for l in Path(f"/proc/{pid}/smaps_rollup").read_text().splitlines():
            p = l.split()
            if p[0] in ("Pss:", "Pss_Anon:", "Pss_File:", "Pss_Shmem:"):
                d[p[0][:-1]] = int(p[1]) / 1024
    except OSError:
        pass
    return d


def one(name, defn, tabs, settle):
    import subprocess, os
    beacons = harness.Beacons(); srv, port = harness.start_server(beacons)
    base = f"http://127.0.0.1:{port}"
    prof = harness.OUT / "profiles" / (name + "-pss")
    harness.prepare_profile(name, "chromium", prof)
    def start(urls, rid):
        return subprocess.Popen(harness.command(defn, prof, urls), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, start_new_session=True)
    p = start([f"{base}/start.html?run={name}-init"], "i"); beacons.wait(f"{name}-init", 1, 60); harness.kill_tree(p.pid); p.wait(); time.sleep(2)
    urls = [f"{base}/tab.html?run={name}-t&i={i}" for i in range(tabs)]
    p = start(urls, "t")
    try:
        beacons.wait(f"{name}-t", tabs, 60); time.sleep(settle)
        procs = []
        for pid in harness.proc_tree(p.pid):
            r = rollup(pid); c = cmdline(pid); r["kind"] = kind(c); r["pid"] = pid; r["cmd"] = b" ".join(c)[:90].decode(errors="replace"); procs.append(r)
        return procs
    finally:
        harness.kill_tree(p.pid); srv.shutdown()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser", required=True); ap.add_argument("--bin")
    ap.add_argument("--repeat", type=int, default=3); ap.add_argument("--tabs", type=int, default=10)
    ap.add_argument("--settle", type=float, default=15); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    defn = harness.browser_defs().get(a.browser, {"kind": "chromium"})
    if a.bin:
        defn = {"kind": "chromium", "bin": Path(a.bin)}
    runs = [one(a.browser, defn, a.tabs, a.settle) for _ in range(a.repeat)]
    agg = {}
    for procs in runs:
        by = {}
        for r in procs:
            k = by.setdefault(r["kind"], {"n": 0, "Pss": 0, "Pss_Anon": 0, "Pss_File": 0, "Pss_Shmem": 0})
            k["n"] += 1
            for f in ("Pss", "Pss_Anon", "Pss_File", "Pss_Shmem"):
                k[f] += r.get(f, 0)
        for kk, v in by.items():
            for f, x in v.items():
                agg.setdefault(kk, {}).setdefault(f, []).append(x)
    res = {kk: {f: round(st.median(x), 1) for f, x in v.items()} for kk, v in agg.items()}
    res["_total"] = {"Pss": round(st.median(sum(r.get("Pss", 0) for r in procs) for procs in runs), 1)}
    Path(a.out).write_text(json.dumps({"browser": a.browser, "median_by_kind": res, "raw": runs}, indent=1))
    for kk, v in sorted(res.items(), key=lambda kv: -kv[1].get("Pss", 0)):
        print(a.browser, kk, v)


if __name__ == "__main__":
    main()
