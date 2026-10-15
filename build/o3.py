#!/usr/bin/env python3
"""-O3 seletivo (docs/BUILD.md, seção "-O3 seletivo").

Troca `optimize_max` (-O2) por `optimize_speed` (-O3) em alvos GN escolhidos (Blink, base, cc,
ui, skia); insere a troca onde o alvo não tem optimize_max; `lto3` sobe o nível do backend
ThinLTO para O3; `global` troca o padrão do build. V8 e partition_alloc já usam optimize_speed
no upstream; blink core_hot também. Idempotente: antes de aplicar, restaura os originais
guardados em <estado>.

uso: o3.py --src <árvore> --state <dir> --profile off|hot|wide|base|ui|skia|lto3|global
     o3.py --src <árvore> --state <dir> --restore
"""
import argparse
import os
import shutil
import sys

OLD = '"//build/config/compiler:optimize_max"'
NEW = '"//build/config/compiler:optimize_speed"'
BLINK = 'third_party/blink/renderer'
CC = 'build/config/compiler/BUILD.gn'
_cfg = '    configs -= [ "//build/config/compiler:default_optimization" ]\n    configs += [ %s ]'
_base_anchor = '    configs += [ %s ]\n  }\n}\n\n# This meta-target is equivalent to //base'
_skia = ('\n  if (!is_debug) {\n    configs -= [ "//build/config/compiler:default_optimization" ]\n'
         '    configs += [ %s ]\n  }\n')
_ins = '  configs -= [ "//build/config/compiler:default_optimization" ]\n  configs += [ %s ]\n' % NEW


def swap(rel, tpl):
    """troca optimize_max -> optimize_speed num trecho que já existe no alvo."""
    old = tpl % OLD
    return (rel, old, old.replace(OLD, NEW))


def insert(rel, head):
    """alvo sem optimize_max: insere a troca de config logo após a abertura do alvo."""
    return (rel, head, head + _ins)


# chave -> lista de (arquivo, trecho exato que deve aparecer uma vez, substituto)
EDITS = {
    'platform': [swap(f'{BLINK}/platform/BUILD.gn', _cfg)],
    'heap': [swap(f'{BLINK}/platform/heap/BUILD.gn', _cfg)],
    'base': [swap('base/BUILD.gn', _base_anchor)],
    # cc.gni aplica cc_add_configs (optimize_max) a todo cc_component/cc_test_static_library
    'cc': [swap('cc/cc.gni', '  cc_add_configs += [ %s ]')],
    # gfx, views e chrome/browser/ui não têm optimize_max (o de gfx é só Android): inserir
    'gfx': [insert('ui/gfx/BUILD.gn', 'component("gfx") {\n')],
    'views': [insert('ui/views/BUILD.gn', 'component("views") {\n')],
    'chrome_ui': [insert('chrome/browser/ui/BUILD.gn', 'static_library("ui") {\n')],
    'skia': [swap('skia/BUILD.gn', _skia)],
    # thinlto_optimize_max (chrome, blink heap/controller, angle) usa --lto-O2 com ThinLTO oficial
    'lto3': [(
        CC,
        '    if (thin_lto_enable_optimizations) {\n      lto_opt_level = 2\n',
        '    if (thin_lto_enable_optimizations) {\n      lto_opt_level = 3\n',
    )],
    # global: default_optimization (-O2 em Linux sem optimize_for_size) e optimize_max viram -O3
    'global': [
        (
            CC,
            '  } else {\n    configs = [ ":optimize" ]\n  }\n}',
            '  } else {\n    configs = [ ":optimize_speed" ]\n  }\n}',
        ),
        (
            CC,
            '    cflags = [ "-O2" ] + common_optimize_on_cflags\n  }\n  rustflags = [ "-Copt-level=3" ]\n}\n\n# This config can be used to override',
            '    cflags = [ "-O3" ] + common_optimize_on_cflags\n  }\n  rustflags = [ "-Copt-level=3" ]\n}\n\n# This config can be used to override',
        ),
    ],
}
PROFILES = {
    'off': [],
    'hot': ['platform', 'heap'],          # wtf/bindings/core: ver docs/BUILD.md
    'wide': ['platform', 'heap', 'base'],
    'base': ['base'],
    'ui': ['cc', 'gfx', 'views', 'chrome_ui'],
    'skia': ['skia'],
    'lto3': ['lto3'],
    'global': ['global'],
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
    # valida tudo antes de escrever: falha não deixa a árvore meio editada
    texts = {}
    for key in PROFILES[a.profile]:
        for rel, old, new in EDITS[key]:
            if rel not in texts:
                texts[rel] = open(os.path.join(a.src, rel)).read()
            if texts[rel].count(old) != 1:
                sys.exit(f'o3: âncora de {key} não encontrada exatamente uma vez em {rel}; árvore mudou?')
            texts[rel] = texts[rel].replace(old, new)
            print(f'o3: {rel}: {key}')
    for rel, text in texts.items():
        path = os.path.join(a.src, rel)
        bak = os.path.join(a.state, rel)          # um backup por arquivo: o original
        os.makedirs(os.path.dirname(bak), exist_ok=True)
        shutil.copyfile(path, bak)
        open(path, 'w').write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
