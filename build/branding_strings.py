#!/usr/bin/env python3
"""aerographene: troca "Chrome"/"Chromium"/"Helium" por "aerographene" nas strings de UI (GRIT)
e injeta traduções pt-BR das mensagens adicionadas pelos patches (build/strings_ptbr_extra.json).

Os ids de mensagem GRIT são fingerprints do texto inglês (+ meaning). Mudar o texto
no .grd/.grdp sem mudar o id nos .xtb faria todas as traduções caírem em inglês.
Para cada mensagem afetada este script:
  1. troca o nome do produto no texto do .grd/.grdp (fora de tags, `<ex>` e atributos);
  2. recalcula o id com o próprio grit da árvore (tools/grit, grit.extern.tclib via
     grd_reader.Parse num grd sintético), sem reimplementar o fingerprint;
  3. reescreve nos .xtb de cada idioma o id antigo -> novo e troca o nome do produto
     na tradução quando ele aparece literal.
Depois, para cada mensagem cujo nome está no JSON de extras, calcula o id do texto inglês
(já trocado) e acrescenta <translation> no .xtb pt-BR do grd se o id ainda não existir.
Idempotente: depois da troca não sobra texto a trocar e ids já presentes não são reinjetados. Chamado por build/inner.sh depois
dos patches e antes do `gn gen`. Detalhes e exclusões: docs/BUILD.md (seção branding).

Uso:
  branding_strings.py [--src DIR] [--check [--list]] [--root grd ...] [--backup DIR]
                      [--extra JSON | --no-extra]
"""
import argparse
import io
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter
from xml.sax.saxutils import escape

NAME = "aerographene"
HERE = os.path.dirname(os.path.abspath(__file__))
EXTRA_DEFAULT = os.path.join(HERE, "strings_ptbr_extra.json")
EXTRA_LANG = "pt-BR"
# mensagens que falam do projeto Helium ou dos servidores operados por ele (não do navegador):
# mantêm o nome, para não dizer que o aerographene opera esses serviços
KEEP_NAMES = {
    "IDS_HELIUM_ONBOARDING_PARTNER_TITLE",
    "IDS_HELIUM_ONBOARDING_PARTNER_TOOLTIP",
    "IDS_SETTINGS_HELIUM_SERVICES",
    "IDS_SETTINGS_HELIUM_SERVICES_DESCRIPTION",
    "IDS_SETTINGS_HELIUM_SCHEMA_NOTICE_TITLE",
    "IDS_SETTINGS_HELIUM_SERVICES_TOGGLE",
    "IDS_SETTINGS_HELIUM_SERVICES_TOGGLE_DESCRIPTION",
    "IDS_SETTINGS_HELIUM_SERVICES_OVERRIDE",
    "IDS_SETTINGS_HELIUM_SERVICES_OVERRIDE_DESCRIPTION",
    "IDS_SETTINGS_HELIUM_SERVICES_OVERRIDE_ARIA_LABEL",
    "IDS_SETTINGS_HELIUM_SERVICES_SETUP_PENDING_TEXT",
    "IDS_HELIUM_ONBOARDING_WELCOME_FOOTER",
    "IDS_HELIUM_ONBOARDING_SERVICES_TITLE",
    "IDS_HELIUM_ONBOARDING_SERVICES_CONNECTION_TITLE",
    "IDS_HELIUM_ONBOARDING_SERVICES_CONNECTION_DESC",
    "IDS_HELIUM_ONBOARDING_SERVICES_BANGS_DESC",
    "IDS_HELIUM_ONBOARDING_SERVICES_EXTENSIONS_DESC",
    "IDS_HELIUM_ONBOARDING_SERVICES_UBLOCK_DESC",
    "IDS_HELIUM_ONBOARDING_SERVICES_AUTOUPDATES_DESC",
    "IDS_HELIUM_ONBOARDING_SERVICES_AUTOUPDATES_DESC_LINUX",
    "IDS_HELIUM_ONBOARDING_SERVICES_SPELLCHECK_DESC",
    "IDS_HELIUM_ONBOARDING_SERVICES_INSTANCE_TITLE",
    "IDS_HELIUM_ONBOARDING_SERVICES_INSTANCE_DESC",
    "IDS_HELIUM_ONBOARDING_SEARCH_CATEGORIES_CUSTOM",
}

# grds raiz (relativos a --src) cujas mensagens são procuradas; partes (<part file=...>)
# e xtb (<translations>) saem do próprio grd. Ausentes na árvore são ignorados.
DEFAULT_ROOTS = [
    "chrome/app/chromium_strings.grd",
    "chrome/app/generated_resources.grd",
    "components/components_chromium_strings.grd",
    "components/components_strings.grd",
    "extensions/strings/extensions_strings.grd",
    "ui/strings/ui_strings.grd",
]

# Exclusões: nome de produto/serviço/tecnologia do Google que continua valendo, ou termo
# técnico (não o nome do navegador). Casadas logo depois de "Chrome"/"Chromium".
_EXCLUDE_AFTER = (
    r"(?:\s|&nbsp;)+(?:OS\b|Web\s?[Ss]tore|[Ww]ebstore|Enterprise|Labs|Remote\b|Cleanup|"
    r"Cast\b|DevTools|Dev\s?Tools|for\sTesting|Canary|Beta\b|Dev\b|Browser\sCloud|Apps?\b|apps?\b|"
    r"Dino|Updater|Nearby|Sync\sfor\b)"
)
# \w e "/" "." "-" antes: não pegar "mychrome", URLs "www.Chrome" etc. Só maiúscula inicial.
# Helium: nome do navegador-base (patches do Helium e helium-onboarding); sem exclusões.
_PRODUCT = re.compile(
    r"(?<![\w/.-])(?:(?:Google\s(?:&nbsp;)?)?Chrom(?:e|ium)(?!\w)(?!" + _EXCLUDE_AFTER + r")|Helium(?!\w))"
)
# "a Chrome" -> "an aerographene" (inglês; o nome começa com vogal)
_ARTICLE = re.compile(r"(?<![\w/.-])([Aa]) (?=(?:(?:Google\s)?Chrom(?:e|ium)(?!\w)(?!" + _EXCLUDE_AFTER + r")|Helium(?!\w)))")

_ATTR = r"""(?:[^>"']|"[^"]*"|'[^']*')*"""
# comentário ou <message ...>...</message>; comentários são pulados
_MSG = re.compile(r"<!--.*?-->|(?P<msg><message\b(?P<attrs>" + _ATTR + r")>(?P<body>.*?)</message>)", re.S)
_TAG = re.compile(r"(<[^>]+>)")
_XTB = re.compile(r'(<translation\b[^>]*?\bid=")(\d+)(")([^>]*>)(.*?)(</translation>)', re.S)
_PART = re.compile(r'<part\s+file="([^"]+)"')
_TFILE = re.compile(r'<file\s+path="([^"]+\.xtb)"\s+lang="([^"]+)"')


def rebrand_text(s, english):
    """Troca o produto em texto corrido (sem marcação). Retorna (novo, nº de trocas)."""
    if english:
        s = _ARTICLE.sub(lambda m: "an " if m.group(1) == "a" else "An ", s)
    return _PRODUCT.subn(NAME, s)


def rebrand_markup(s, english):
    """Como rebrand_text, em fragmento XML: só texto fora de tags e de <ex>...</ex>."""
    out, total, in_ex = [], 0, False
    for part in _TAG.split(s):
        if part.startswith("<"):
            if re.match(r"<ex\b", part):
                in_ex = True
            elif part.startswith("</ex"):
                in_ex = False
            out.append(part)
        elif in_ex:
            out.append(part)
        else:
            new, n = rebrand_text(part, english)
            out.append(new)
            total += n
    return "".join(out), total


class Ids:
    """Calcula ids GRIT com o grit da árvore (grd sintético, um parse por lote)."""

    def __init__(self, src):
        sys.path.insert(0, os.path.join(src, "tools", "grit"))
        from grit import grd_reader  # noqa: E402
        self.grd_reader = grd_reader
        self.tmp = tempfile.mkdtemp(prefix="aero-grit-")

    def ids(self, blocks):
        """blocks: lista de (attrs, body) de <message>. Devolve ids na mesma ordem
        (None para use_name_for_id/sem clique)."""
        drop = {"name", "custom_type", "validation_expr", "generate_xtb", "use_name_for_id"}

        def build(i, attrs, body):
            # tokeniza os atributos (sem regex solta) e reconstrói sem duplicatas
            kept = {}
            for k, v in re.findall(r"([\w:.-]+)\s*=\s*(\"[^\"]*\"|'[^']*')", attrs):
                if k not in drop:
                    kept[k] = v
            a = "".join(" %s=%s" % (k, v) for k, v in kept.items())
            return '<message name="M%d"%s>%s</message>' % (i, a, body)

        def parse(idx):
            parts = [build(i, *blocks[i]) for i in idx]
            doc = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<grit base_dir="." latest_public_release="0" current_release="1" source_lang_id="en">'
                '<release seq="1"><messages>' + "\n".join(parts) + "</messages></release></grit>"
            )
            return self.grd_reader.Parse(io.StringIO(doc), dir=self.tmp, skip_validation_checks=True)

        try:
            root = parse(range(len(blocks)))
        except Exception:
            # isola a mensagem problemática: ids dela ficam None (não reescreve xtb)
            ok = []
            for i in range(len(blocks)):
                try:
                    parse([i])
                    ok.append(i)
                except Exception as e:  # noqa: BLE001
                    print("aviso: mensagem ignorada (%s): %s" % (type(e).__name__, blocks[i][0][:80].replace("\n", " ")))
            root = parse(ok)
        res = [None] * len(blocks)
        for node in root.Preorder():
            if node.name == "message":
                m = re.fullmatch(r"M(\d+)", node.attrs["name"])
                cl = node.GetCliques()
                if m and cl:
                    res[int(m.group(1))] = cl[0].GetId()
        return res


def collect_files(root_path):
    """Raiz + partes (recursivo)."""
    seen, order, stack = set(), [], [root_path]
    while stack:
        p = stack.pop()
        if p in seen or not os.path.isfile(p):
            continue
        seen.add(p)
        order.append(p)
        txt = open(p, encoding="utf-8").read()
        txt = re.sub(r"<!--.*?-->", "", txt, flags=re.S)
        for rel in _PART.findall(txt):
            stack.append(os.path.normpath(os.path.join(os.path.dirname(p), rel)))
    return order


PTBR_NEW_TAB = re.compile(r"\b([Nn])ova guia")
_PH = re.compile(r'<ph\s+name="([^"]+)"')
_PH_XTB = re.compile(r'(<ph\s+name="[A-Za-z0-9_]+"\s*/>)')


def load_extra(path):
    """JSON nome IDS -> texto pt-BR (chaves com "_" no início são comentários)."""
    if not path:
        return {}
    data = json.load(open(path, encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def xtb_text(text):
    """Texto do JSON -> conteúdo de <translation>: escapa tudo exceto <ph name="X"/>."""
    return "".join(part if _PH_XTB.fullmatch(part) else escape(part) for part in _PH_XTB.split(text))


def inject_extra(files, contents, xtb_path, xtb_txt, extra, ids, stats, src):
    """Acrescenta ao xtb as traduções de `extra` ausentes. Devolve o xtb novo (ou None)."""
    blocks, names = [], []
    for p in files:
        for m in _MSG.finditer(contents[p]):
            if m.group("msg") is None:
                continue
            attrs = m.group("attrs")
            nm = re.search(r'\bname="([^"]*)"', attrs)
            if not nm or nm.group(1) not in extra:
                continue
            if 'use_name_for_id="true"' in attrs or 'translateable="false"' in attrs:
                continue
            want = set(_PH.findall(m.group("body")))
            got = set(_PH.findall(extra[nm.group(1)]))
            if want != got:
                print("aviso: %s: placeholders %s != %s, sem tradução" % (nm.group(1), sorted(got), sorted(want)))
                continue
            blocks.append((attrs, m.group("body")))
            names.append(nm.group(1))
    if not blocks:
        return None
    have = set(m.group(2) for m in _XTB.finditer(xtb_txt))
    add, seen = [], set()
    for name, i in zip(names, ids.ids(blocks)):
        if i and i not in have and i not in seen:
            seen.add(i)
            add.append('<translation id="%s">%s</translation>\n' % (i, xtb_text(extra[name])))
    stats["extra_found"] += len(set(names))
    if not add:
        return None
    end = xtb_txt.rindex("</translationbundle>")
    print("  extra %-6s +%d traduções  %s" % (EXTRA_LANG, len(add), os.path.relpath(xtb_path, src)))
    stats["extra_added"] += len(add)
    return xtb_txt[:end] + "".join(add) + xtb_txt[end:]


def process_root(root, ids, check, stats, src, backup, listing=False, extra=None):
    files = collect_files(root)
    if not files:
        return
    contents = {}  # path -> conteúdo atual (pós-troca)
    new_text = {}  # path -> novo conteúdo
    affected = []  # (path, attrs, old_body, new_body, name)
    for p in files:
        txt = open(p, encoding="utf-8", newline="").read()

        def repl(m):
            if m.group("msg") is None:
                return m.group(0)
            attrs, body = m.group("attrs"), m.group("body")
            nm = re.search(r'\bname="([^"]*)"', attrs)
            if nm and nm.group(1) in KEEP_NAMES:
                return m.group(0)
            nb, n = rebrand_markup(body, True)
            if not n:
                return m.group(0)
            affected.append((p, attrs, body, nb, nm.group(1) if nm else "?"))
            return m.group(0)[: m.start("body") - m.start(0)] + nb + "</message>"

        out = _MSG.sub(repl, txt)
        contents[p] = out
        if out != txt:
            new_text[p] = out

    grd_txt = open(root, encoding="utf-8").read()
    xtbs = [(os.path.normpath(os.path.join(os.path.dirname(root), rel)), lang)
            for rel, lang in _TFILE.findall(grd_txt)]
    new_xtb = {}

    if not affected:
        stats["roots_noop"] += 1
    else:
        # ids: antigos e novos, em lote; use_name_for_id/translateable=false não têm xtb
        movable = [i for i, a in enumerate(affected)
                   if 'use_name_for_id="true"' not in a[1] and 'translateable="false"' not in a[1]]
        old_ids = ids.ids([(affected[i][1], affected[i][2]) for i in movable])
        new_ids = ids.ids([(affected[i][1], affected[i][3]) for i in movable])
        idmap = {}
        for i, o, n in zip(movable, old_ids, new_ids):
            if o and n and o != n:
                idmap[o] = n
        per_file = Counter()
        for p, *_ in affected:
            per_file[p] += 1
        for p, c in sorted(per_file.items()):
            print("  msgs %-4d %s" % (c, p))
        stats["messages"] += len(affected)
        stats["ids"] += len(idmap)

        for xp, lang in xtbs:
            if not os.path.isfile(xp):
                continue
            xtxt = open(xp, encoding="utf-8", newline="").read()
            english = lang.lower().startswith("en")
            have = set(m.group(2) for m in _XTB.finditer(xtxt))
            renamed = literal = dups = 0
            emitted = set()

            def xrepl(m):
                nonlocal renamed, literal, dups
                old = m.group(2)
                if old not in idmap:
                    return m.group(0)
                new = idmap[old]
                if new in have or new in emitted:  # colisão: mantém a primeira, descarta esta
                    dups += 1
                    return ""
                emitted.add(new)
                body, n = rebrand_markup(m.group(5), english)
                literal += 1 if n else 0
                renamed += 1
                return m.group(1) + new + m.group(3) + m.group(4) + body + m.group(6)

            xout = _XTB.sub(xrepl, xtxt)
            if renamed or dups:
                new_xtb[xp] = xout
                stats["xtb_entries"] += renamed
                stats["xtb_literal"] += literal
                stats["xtb_dups"] += dups
            if lang in ("pt-BR", "en-GB") or check:
                if renamed or dups:
                    print("  xtb %-6s renomeados=%-4d com_nome_literal=%-4d duplicados=%d  %s" % (lang, renamed, literal, dups, xp))

    if extra:
        for xp, lang in xtbs:
            if lang != EXTRA_LANG or not os.path.isfile(xp):
                continue
            cur = new_xtb.get(xp)
            if cur is None:
                cur = open(xp, encoding="utf-8", newline="").read()
            out = inject_extra(files, contents, xp, cur, extra, ids, stats, src)
            if out is not None:
                new_xtb[xp] = out
    # aerographene: "Nova guia" -> "Nova aba" no pt-BR (menus, atalhos, botão da sidebar).
    for xp, lang in xtbs:
        if lang != EXTRA_LANG or not os.path.isfile(xp):
            continue
        cur = new_xtb.get(xp)
        if cur is None:
            cur = open(xp, encoding="utf-8", newline="").read()
        out, n = PTBR_NEW_TAB.subn(r"\1ova aba", cur)
        if n:
            print("  termo %-6s 'Nova guia' -> 'Nova aba' em %d traduções  %s" % (lang, n, os.path.relpath(xp, src)))
            new_xtb[xp] = out
    stats["xtb_files"] += len(new_xtb)

    if check:
        if listing:
            for p, attrs, old, new, name in affected:
                print("    %s: %s" % (os.path.relpath(p, src), name))
        return
    for path, content in list(new_xtb.items()) + list(new_text.items()):  # xtb antes do grd
        if backup:  # original (pós-patches) para o revert incremental de build/inner.sh
            dst = os.path.join(backup, os.path.relpath(path, src))
            if not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(path, dst)
        tmp = path + ".aero-tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=".", help="raiz da árvore do Chromium")
    ap.add_argument("--check", action="store_true", help="só lista mensagens afetadas e contagens; não escreve")
    ap.add_argument("--root", action="append", help="grd raiz (relativo a --src); padrão: lista embutida")
    ap.add_argument("--list", action="store_true", help="com --check, imprime cada mensagem afetada")
    ap.add_argument("--backup", help="copia aqui cada arquivo (caminho relativo a --src) antes de reescrevê-lo")
    ap.add_argument("--extra", default=EXTRA_DEFAULT, help="JSON nome IDS -> tradução pt-BR (padrão: %(default)s)")
    ap.add_argument("--no-extra", action="store_true", help="não injeta traduções extras")
    a = ap.parse_args()
    src = os.path.abspath(a.src)
    ids = Ids(src)
    stats = Counter()
    extra = {} if a.no_extra else load_extra(a.extra)
    for rel in a.root or DEFAULT_ROOTS:
        root = os.path.join(src, rel)
        if not os.path.isfile(root):
            print("== %s: ausente, ignorado" % rel)
            continue
        print("== %s" % rel)
        process_root(root, ids, a.check, stats, src, a.backup, a.list, extra)
    print("== total: mensagens=%d ids_novos=%d xtb_arquivos=%d xtb_entradas=%d (com nome literal=%d, duplicadas descartadas=%d)%s"
          % (stats["messages"], stats["ids"], stats["xtb_files"], stats["xtb_entries"],
             stats["xtb_literal"], stats["xtb_dups"], " [--check: nada escrito]" if a.check else ""))
    if extra:
        print("== extras %s: nomes no JSON=%d encontrados=%d traduções_novas=%d"
              % (EXTRA_LANG, len(extra), stats["extra_found"], stats["extra_added"]))


if __name__ == "__main__":
    main()
