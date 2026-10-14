#!/usr/bin/env python3
"""-O3 seletivo (docs/BUILD.md, seção "-O3 seletivo").

Troca `optimize_max` (-O2) por `optimize_speed` (-O3) em alvos GN escolhidos do Blink/base.
V8 e partition_alloc já usam optimize_speed no upstream; blink core_hot também. Não faz nada
global. Idempotente: antes de aplicar, restaura os originais guardados em <estado>.

uso: o3.py --src <árvore> --state <dir> --profile off|hot|wide
     o3.py --src <árvore> --state <dir> --restore
"""
import argparse
import os
import shutil
import sys

OLD = '"//build/config/compiler:optimize_max"'
NEW = '"//build/config/compiler:optimize_speed"'
BLINK = 'third_party/blink/renderer'
_cfg = '    configs -= [ "//build/config/compiler:default_optimization" ]\n    configs += [ %s ]'
_base_anchor = '    configs += [ %s ]\n  }\n}\n\n# This meta-target is equivalent to //base'

# arquivo -> trecho exato (deve aparecer uma vez) com optimize_max
EDITS = {
    'platform': (f'{BLINK}/platform/BUILD.gn', _cfg % OLD),
    'heap': (f'{BLINK}/platform/heap/BUILD.gn', _cfg % OLD),
    'base': ('base/BUILD.gn', _base_anchor % OLD),
}
PROFILES = {
    'off': [],
    'hot': ['platform', 'heap'],          # wtf/bindings/core: ver docs/BUILD.md
    'wide': ['platform', 'heap', 'base'],
}


def restore(src, state):
    n = 0
    if not os.path.isdir(state):
        return 0
    for root, _, files in os.walk(state):
        for f in files:
            bak = os.path.join(root, f)
            rel = os.path.relpath(bak, state)
            dst = os.path.join(src, rel)
            if os.path.isfile(dst) and open(dst, 'rb').read() != open(bak, 'rb').read():
                shutil.copyfile(bak, dst)
                n += 1
    shutil.rmtree(state)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--state', required=True)
    ap.add_argument('--profile', default='off', choices=PROFILES)
    ap.add_argument('--restore', action='store_true')
    a = ap.parse_args()
    n = restore(a.src, a.state)
    if n:
        print(f'o3: {n} arquivo(s) restaurado(s)')
    if a.restore or a.profile == 'off':
        return 0
    for key in PROFILES[a.profile]:
        rel, old = EDITS[key]
        path = os.path.join(a.src, rel)
        text = open(path).read()
        if text.count(old) != 1:
            sys.exit(f'o3: âncora de {key} não encontrada exatamente uma vez em {rel}; árvore mudou?')
        bak = os.path.join(a.state, rel)
        os.makedirs(os.path.dirname(bak), exist_ok=True)
        shutil.copyfile(path, bak)
        open(path, 'w').write(text.replace(old, old.replace(OLD, NEW)))
        print(f'o3: {rel}: optimize_max -> optimize_speed ({key})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
