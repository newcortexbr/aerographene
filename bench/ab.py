#!/usr/bin/env python3
"""Rodada intercalada: uma chamada do harness por navegador por volta, ordem rotacionada.

Importa bench/harness.py sem editá-lo e permite apontar binários por --bin nome=caminho.
Exemplo:
  python3 bench/ab.py --laps 10 --block warm --browsers aerographene,helium,thorium,chrome,ungoogled \
      --bin aerographene=/tmp/pkg/chrome --bin chrome=/tmp/chrome/opt/google/chrome/chrome --out /tmp/out
Cada chamada grava em bench/out/results-*.jsonl; o arquivo é copiado para --out.
"""
import argparse, os, shutil, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402


def wait_load(limit=1.0, tries=120):
    for _ in range(tries):
        if float(open("/proc/loadavg").read().split()[0]) < limit:
            return True
        time.sleep(10)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--browsers", required=True)
    ap.add_argument("--block", choices=["warm", "first", "tabs"], required=True)
    ap.add_argument("--laps", type=int, default=10)
    ap.add_argument("--repeat", type=int, default=2)
    ap.add_argument("--bin", action="append", default=[], help="nome=caminho")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    names = a.browsers.split(",")
    overrides = dict(b.split("=", 1) for b in a.bin)
    orig = harness.browser_defs
    def defs():
        d = orig()
        d.setdefault("chrome", {"kind": "chromium", "bin": Path("/nonexistent")})
        for k, v in overrides.items():
            d[k] = {"kind": "chromium", "bin": Path(v)}
        return d
    harness.browser_defs = defs
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    status = out / "status.txt"
    for lap in range(a.laps):
        k = lap % len(names)
        order = names[k:] + names[:k]
        for n in order:
            ok = wait_load()
            with status.open("a") as f:
                f.write(f"{time.strftime('%T')} {a.block} lap={lap} {n} load_ok={ok}\n")
            argv = ["harness.py", "--browsers", n, "--mode", "first" if a.block == "first" else "warm",
                    "--repeat", str(a.repeat), "--pause", "2"]
            if a.block == "tabs":
                argv += ["--tabs", "10"]
            before = set(harness.OUT.glob("results-*.jsonl"))
            sys.argv = argv
            rc = harness.main()
            for p in set(harness.OUT.glob("results-*.jsonl")) - before:
                shutil.copy(p, out / f"{a.block}-lap{lap}-{n}-{p.name}")
            time.sleep(1.1)  # stamps distintos
    return 0


if __name__ == "__main__":
    sys.exit(main())
