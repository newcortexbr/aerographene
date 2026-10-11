#!/usr/bin/env python3
"""Gera os .icon do Chromium e o mapa de troca dos temas de ícone.

Fontes (versionadas ao lado deste script):
  assets/icons-v2.json  -> tema default (traço 1,5, butt/miter, sem curvas)
  pixelized/icons.html  -> tema pixelized (bitmaps 16x16, tons 100/50/22%)

Uso:
  gen_theme_icons.py icons OUT_DIR THEME   # escreve <theme>_<id>.icon em OUT_DIR
  gen_theme_icons.py map THEME             # imprime as linhas C++ do mapa
  gen_theme_icons.py sources THEME         # imprime as linhas de BUILD.gn
  gen_theme_icons.py table                 # tabela id -> nomes upstream

Sem dependências externas. Saída determinística.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HEADER = ("// Copyright 2026 The aerographene Authors\n"
          "// Use of this source code is governed by the GPL-3.0 license.\n"
          "// Gerado por theming/design-language/gen_theme_icons.py; não editar.\n\n")

# id da tabela -> nomes upstream (qualificados) e evidência de uso no src 154.
# vector_icons:: = //components/vector_icons, :: = //chrome/app/vector_icons,
# views:: = //ui/views e //ui/views/window/vector_icons, omnibox:: = omnibox.
MAP = [
    ("i-back", ["vector_icons::kArrowBackIcon",
                "vector_icons::kBackArrowChromeRefreshOldIcon",
                "::kBackArrowTouchOldIcon"],
     "views/toolbar/back_forward_button.cc:48-53"),
    ("i-fwd", ["vector_icons::kArrowForwardIcon",
               "vector_icons::kForwardArrowChromeRefreshOldIcon",
               "::kForwardArrowTouchOldIcon"],
     "views/toolbar/back_forward_button.cc:62-67"),
    ("i-rel", ["vector_icons::kRefreshIcon",
               "vector_icons::kReloadChromeRefreshOldIcon",
               "::kReloadTouchOldIcon"],
     "views/toolbar/reload_button.cc:68-73"),
    ("i-side", ["views::kMenuOpenIcon", "views::kMenuOpenOldIcon",
                "views::kMenuCloseCustomIcon"],
     "aerographene/sidebar-toggle-button.patch (sidebar_toggle_)"),
    ("i-search", ["vector_icons::kSearchIcon",
                  "vector_icons::kSearchChromeRefreshOldIcon"],
     "toolbar/app_menu_model.cc:2267, omnibox"),
    ("i-hist", ["vector_icons::kHistoryIcon", "::kHistoryIcon",
                "vector_icons::kHistoryChromeRefreshOldIcon"],
     "tabs/recent_tabs_builder.cc:247-248"),
    ("i-dl", ["vector_icons::kDownloadIcon", "::kDownloadIcon",
              "::kDownloadToolbarButtonChromeRefreshOldIcon",
              "::kDownloadToolbarButtonTouchOldIcon"],
     "views/download/bubble/download_toolbar_ui_controller.cc:698-702"),
    ("i-ext", ["vector_icons::kChromeExtensionIcon",
               "vector_icons::kExtensionChromeRefreshOldIcon"],
     "extensions/extensions_toolbar_view_model.cc:179-181"),
    ("i-more", ["::kMoreVertIcon", "::kBrowserToolsChromeRefreshOldIcon",
                "::kBrowserToolsTouchOldIcon"],
     "views/toolbar/browser_app_menu_button.cc:154-159"),
    ("i-link", ["vector_icons::kLinkIcon", "::kLinkChromeRefreshOldIcon"],
     "toolbar/app_menu_model.cc:921-922"),
    ("i-info", ["omnibox::kPageInfoCustomIcon",
                "omnibox::kSecurePageInfoChromeRefreshOldIcon"],
     "views/location_bar/location_icon_view.cc:208-211"),
    ("i-plus", ["::kAddIcon", "::kAddChromeRefreshOldIcon"],
     "views/toolbar/app_menu.cc:733, omnibox/omnibox_edit_model.cc:586"),
    ("i-close", ["views::kCloseIcon", "vector_icons::kCloseIcon",
                 "::kCloseIcon", "vector_icons::kCloseChromeRefreshOldIcon",
                 "::kCloseChromeRefreshOldIcon", "::kCloseWeight500CustomIcon",
                 "::kCloseTabChromeRefreshOldIcon",
                 "views::kWindowControlCloseOldIcon"],
     "views/tabs/tab/tab_close_button.cc:212-214, ui/views/window/frame_view_linux.cc:92-93"),
    ("i-min", ["views::kChromeMinimizeIcon", "::kChromeMinimizeIcon",
               "views::kWindowControlMinimizeOldIcon"],
     "ui/views/window/frame_view_linux.cc:99-100, views/frame/opaque_browser_frame_view.cc:173"),
    ("i-max", ["views::kChromeMaximizeIcon",
               "views::kWindowControlMaximizeOldIcon"],
     "ui/views/window/frame_view_linux.cc:106-107"),
    ("i-win", ["views::kNewWindowIcon", "::kNewWindowIcon",
               "views::kNewWindowOldIcon", "::kNewWindowOldIcon"],
     "toolbar/app_menu_model.cc:2104"),
    ("i-minus", ["::kRemoveIcon", "::kRemoveOldIcon",
                 "::kZoomMinusChromeRefreshOldIcon"],
     "views/location_bar/zoom_bubble_view.cc:291, views/zoom/zoom_view_controller.cc:80"),
    ("i-chev", ["vector_icons::kKeyboardArrowDownIcon",
                "::kKeyboardArrowDownIcon",
                "::kKeyboardArrowDownChromeRefreshOldIcon"],
     "views/find_bar_view.cc:299, views/tabs/common/tab_group_header_view.cc:566"),
    ("i-chevr", ["vector_icons::kKeyboardArrowRightFlippableIcon",
                 "vector_icons::kSubmenuArrowChromeRefreshOldIcon"],
     "ui/views/controls/menu/menu_item_view.cc:1705-1706"),
    ("i-chl", ["::kKeyboardArrowLeftIcon"],
     "views/tabs/horizontal/tab_scroll_button_container.cc:152"),
    ("i-chr", ["::kKeyboardArrowRightIcon", "::kChevronRightIcon"],
     "views/tabs/horizontal/tab_scroll_button_container.cc:166, views/download/bubble/download_bubble_row_view.cc:473"),
    ("i-up", ["::kArrowUpwardIcon"], "views/tabs/shared/drop_arrow.cc:35"),
    ("i-down", ["::kArrowDownwardIcon"], "views/tabs/shared/drop_arrow.cc:38"),
    ("i-check", ["views::kCheckIcon", "::kCheckIcon", "views::kMenuCheckOldIcon"],
     "ui/views/controls/menu/menu_item_view.cc:1713"),
    ("i-gear", ["vector_icons::kSettingsIcon", "::kSettingsIcon",
                "::kSettingsMenuOldIcon",
                "vector_icons::kSettingsChromeRefreshOldIcon"],
     "toolbar/app_menu_model.cc:2347, page_info/chrome_page_info_delegate.cc:268"),
    ("i-mon", ["vector_icons::kDesktopWindowsIcon", "::kDesktopWindowsIcon"],
     "toolbar/app_menu_model.cc:905"),
    ("i-split", ["::kSplitSceneIcon", "::kSplitSceneOldIcon"],
     "tabs/tab_menu_model.cc:347-349"),
    ("i-ext2", ["::kOpenInNewIcon", "views::kOpenInNewIcon", "::kOpenInNewOldIcon"],
     "tabs/tab_menu_model.cc:463-464"),
    ("i-folder", ["vector_icons::kFolderFlippableIcon",
                  "vector_icons::kFolderChromeRefreshOldIcon"],
     "bookmarks/bookmark_utils.cc:388-390, ui/views/controls/tree/tree_view.cc:115"),
    ("i-bell", ["vector_icons::kNotificationsIcon",
                "vector_icons::kNotificationsChromeRefreshOldIcon"],
     "page_info/page_info_view_factory.cc:353"),
    ("i-spk", ["vector_icons::kVolumeUpIcon",
               "vector_icons::kVolumeUpChromeRefreshOldIcon"],
     "tabs/alert/tab_alert_icon.cc:72"),
    ("i-spkoff", ["vector_icons::kVolumeOffIcon",
                  "vector_icons::kVolumeOffChromeRefreshOldIcon"],
     "tabs/alert/tab_alert_icon.cc:76"),
]

# Sem correspondente upstream clara: ficam fora do mapa.
UNMAPPED = {
    "i-pk": "peek é do aerographene; sem ícone upstream",
    "i-board": "board/modo terminal não existe upstream",
    "i-term": "aba t: não existe upstream",
    "i-doc": "tipo nota/arquivo da palette; sem uso upstream equivalente",
    "i-leaf": "vault/notas; sem uso upstream",
    "i-crystal": "vault -o; sem uso upstream",
    "i-vault": "cofre de notas; kLockIcon upstream é segurança de página, outro sentido",
    "i-spark": "sugestão/IA; upstream usa vários ícones de IA sem um único equivalente",
    "i-swap": "trocar painéis; sem ícone upstream equivalente",
    "i-grip": "alça de arrasto; sem ícone vetorial upstream usado na UI desktop",
    "i-rsz": "kResizeHandleOldIcon é só do picture-in-picture",
    "i-pl": "plugue/agente; sem uso upstream",
}

FLIPS_IN_RTL = {"i-chevr"}

# Escudo do uBlock (não está nas tabelas). Default: mesmo traço da tabela.
UBLOCK_DEFAULT = "M3 2.5h10V8l-5 5.5L3 8zM8 5.5v5"
# Pixelized: silhueta 16x16 (O = contorno 100%, F = preenchimento 22%);
# a sombra 50% é calculada: silhueta deslocada (+1,+1) menos a silhueta.
UBLOCK_PIXELS = [
    "................",
    "................",
    "...OOOOOOOOOO...",
    "...OFFFFFFFFO...",
    "...OFFFFFFFFO...",
    "...OFFFOOFFFO...",
    "...OFFFOOFFFO...",
    "...OFFFOOFFFO...",
    "...OFFFOOFFFO...",
    "....OFFFFFFO....",
    ".....OFFFFO.....",
    "......OFFO......",
    ".......OO.......",
    "................",
    "................",
    "................",
]
OFF_ALPHA_SCALE = 0.4  # variante off esmaecida


def fmt(v):
    v = round(v, 3)
    if v == int(v):
        return str(int(v))
    return ("%g" % v) + "f"


def alpha_hex(a):
    return "0x%02X" % max(0, min(255, int(round(a * 255))))


# ---------- default: SVG path (M/L/H/V/Z) -> comandos ----------

TOKEN = re.compile(r"[MLHVZmlhvz]|-?\d*\.?\d+(?:e-?\d+)?")


def svg_path_to_polys(d):
    toks = TOKEN.findall(d)
    i, cmd = 0, None
    x = y = sx = sy = 0.0
    out = []

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    while i < len(toks):
        t = toks[i]
        if re.match(r"[A-Za-z]", t):
            cmd = t
            i += 1
            if cmd in "Zz":
                out.append(("CLOSE",))
                x, y = sx, sy
                continue
        elif cmd is None:
            raise ValueError("path sem comando: " + d)
        if cmd in "Mm":
            nx, ny = num(), num()
            if cmd == "m":
                nx, ny = x + nx, y + ny
            out.append(("MOVE_TO", nx, ny))
            x, y = sx, sy = nx, ny
            cmd = "L" if cmd == "M" else "l"
        elif cmd in "Ll":
            nx, ny = num(), num()
            if cmd == "l":
                nx, ny = x + nx, y + ny
            out.append(("LINE_TO", nx, ny))
            x, y = nx, ny
        elif cmd in "Hh":
            nx = num()
            x = x + nx if cmd == "h" else nx
            out.append(("LINE_TO", x, y))
        elif cmd in "Vv":
            ny = num()
            y = y + ny if cmd == "v" else ny
            out.append(("LINE_TO", x, y))
        else:
            raise ValueError("comando não suportado: " + cmd)
    return out


def emit_ops(ops):
    lines = []
    for op in ops:
        if op[0] == "CLOSE":
            lines.append("CLOSE,")
        else:
            lines.append("%s, %s, %s," % (op[0], fmt(op[1]), fmt(op[2])))
    return lines


def rect_ops(x, y, w, h):
    return [("MOVE_TO", x, y), ("LINE_TO", x + w, y), ("LINE_TO", x + w, y + h),
            ("LINE_TO", x, y + h), ("CLOSE",)]


def default_icon(svg, rtl=False, alpha=1.0):
    lines = ["CANVAS_DIMENSIONS, 16,"]
    if rtl:
        lines.append("FLIPS_IN_RTL,")
    paths = re.findall(r'<path d="([^"]*)"', svg)
    rects = re.findall(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" '
                       r'height="([\d.]+)"/>', svg)
    first = True
    if paths:
        if alpha < 1:
            lines.append("PATH_COLOR_ALPHA, %s," % alpha_hex(alpha))
        lines += ["STROKE, 1.5f,", "CAP_BUTT,"]
        for d in paths:
            lines += emit_ops(svg_path_to_polys(d))
        first = False
    if rects:
        if not first:
            lines.append("NEW_PATH,")
        if alpha < 1:
            lines.append("PATH_COLOR_ALPHA, %s," % alpha_hex(alpha))
        lines.append("FILL_RULE_NONZERO,")
        for r in rects:
            lines += emit_ops(rect_ops(*map(float, r)))
    if not paths and not rects:
        raise ValueError("ícone vazio")
    return lines


# ---------- pixelized: retângulos por tom ----------

def pixel_icon(rects, rtl=False, scale=1.0):
    """rects: lista de (x, y, w, h, opacidade)."""
    lines = ["CANVAS_DIMENSIONS, 16,"]
    if rtl:
        lines.append("FLIPS_IN_RTL,")
    tones = {}
    for x, y, w, h, a in rects:
        tones.setdefault(a, []).append((x, y, w, h))
    first = True
    # tons claros primeiro; o contorno 100% por último.
    for a in sorted(tones):
        if not first:
            lines.append("NEW_PATH,")
        first = False
        eff = a * scale
        if eff < 1:
            lines.append("PATH_COLOR_ALPHA, %s," % alpha_hex(eff))
        # retângulos podem se sobrepor: non-zero, todos no mesmo sentido.
        lines += ["FILL_RULE_NONZERO,", "DISABLE_AA,"]
        for r in sorted(tones[a], key=lambda r: (r[1], r[0])):
            lines += emit_ops(rect_ops(*r))
    return lines


def load_default():
    with open(os.path.join(HERE, "assets", "icons-v2.json")) as f:
        return json.load(f)["icons"]


def load_pixelized():
    with open(os.path.join(HERE, "pixelized", "icons.html")) as f:
        s = f.read()
    syms = dict(re.findall(
        r'<symbol id="([^"]+)" viewBox="0 0 16 16">(.*?)</symbol>', s))
    out = {}
    for k, body in syms.items():
        rs = []
        for m in re.finditer(r'<rect x="(\d+)" y="(\d+)" width="(\d+)" '
                             r'height="(\d+)"(?: fill-opacity="([.\d]+)")?/>',
                             body):
            x, y, w, h = map(int, m.group(1, 2, 3, 4))
            rs.append((x, y, w, h, float(m.group(5) or 1)))
        if len(rs) != body.count("<rect"):
            raise ValueError("rect não reconhecido em " + k)
        out[k] = rs
    return out


def ublock_pixel_rects():
    grid = UBLOCK_PIXELS
    solid = {(x, y) for y, row in enumerate(grid) for x, c in enumerate(row)
             if c != "."}
    cells = {}
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c == "O":
                cells[(x, y)] = 1.0
            elif c == "F":
                cells[(x, y)] = 0.22
    for (x, y) in sorted(solid):
        p = (x + 1, y + 1)
        if p not in solid and p[0] < 16 and p[1] < 16:
            cells[p] = 0.5
    # junta corridas horizontais do mesmo tom.
    rects = []
    for y in range(16):
        x = 0
        while x < 16:
            a = cells.get((x, y))
            if a is None:
                x += 1
                continue
            w = 1
            while cells.get((x + w, y)) == a:
                w += 1
            rects.append((x, y, w, 1, a))
            x += w
    return rects


def short(i):
    return i[2:].replace("-", "_")


def icons_for(theme):
    """{nome_arquivo: linhas}"""
    out = {}
    if theme == "default":
        src = load_default()
        for i, _, _ in MAP:
            out["default_" + short(i)] = default_icon(src[i], i in FLIPS_IN_RTL)
    elif theme == "pixelized":
        src = load_pixelized()
        for i, _, _ in MAP:
            out["pixelized_" + short(i)] = pixel_icon(src[i], i in FLIPS_IN_RTL)
    elif theme == "ublock":
        svg = '<path d="%s"/>' % UBLOCK_DEFAULT
        out["default_ublock"] = default_icon(svg)
        out["default_ublock_off"] = default_icon(svg, alpha=OFF_ALPHA_SCALE)
        r = ublock_pixel_rects()
        out["pixelized_ublock"] = pixel_icon(r)
        out["pixelized_ublock_off"] = pixel_icon(r, scale=OFF_ALPHA_SCALE)
    else:
        raise SystemExit("tema desconhecido: " + theme)
    return out


def camel(name):
    return "k" + "".join(w.capitalize() for w in name.split("_")) + "Icon"


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    mode = argv[1]
    if mode == "icons":
        out_dir, theme = argv[2], argv[3]
        os.makedirs(out_dir, exist_ok=True)
        for name, lines in sorted(icons_for(theme).items()):
            with open(os.path.join(out_dir, name + ".icon"), "w") as f:
                f.write(HEADER + "\n".join(lines) + "\n")
    elif mode == "sources":
        for name in sorted(icons_for(argv[2])):
            print('    "%s.icon",' % name)
    elif mode == "map":
        theme = argv[2]
        for i, names, ev in MAP:
            target = "aerographene_theme_icons::" + camel(theme + "_" + short(i))
            print("  // %s: %s" % (i, ev))
            for n in names:
                print("  (*map)[&%s] = &%s;" % (n, target))
    elif mode == "table":
        for i, names, ev in MAP:
            print("%s\t%s\t%s" % (i, ", ".join(names), ev))
        for i, why in UNMAPPED.items():
            print("%s\t-\t%s" % (i, why))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
