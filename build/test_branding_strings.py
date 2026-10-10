#!/usr/bin/env python3
"""Testes de build/branding_strings.py.

Unitários: sempre rodam. Integração: precisa de arquivos reais do Chromium 154.0.8037.97
(chrome/app/*.grd(p), chrome/app/resources/*_{pt-BR,en-GB}.xtb, components/..., tools/grit);
aponte AERO_TEST_SRC para um espelho/árvore. A prova: o grit da árvore carrega o grd e os
xtb reescritos e acha a MESMA quantidade de traduções que antes (nenhuma cai em inglês).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import branding_strings as bs  # noqa: E402

SRC = os.environ.get("AERO_TEST_SRC")
DEFINES = {
    "_is_chrome_for_testing_branded": False, "_google_chrome": False,
    "chrome_root_store_cert_management_ui": True, "enable_extensions": True,
    "enable_extensions_core": True, "enable_pdf": True, "enable_printing": True,
    "enable_print_preview": True, "enable_vr": False, "enable_webui_ntp": True,
    "is_cfm": False, "reven": False, "toolkit_views": True, "use_titlecase": False,
}


class Unit(unittest.TestCase):
    def t(self, s, english=True):
        return bs.rebrand_markup(s, english)[0]

    def test_basic(self):
        self.assertEqual(self.t("Chromium needs Chrome"), "aerographene needs aerographene")
        self.assertEqual(self.t("&amp;Chromium"), "&amp;aerographene")
        self.assertEqual(self.t("Google Chrome"), "aerographene")
        self.assertEqual(self.t("Open in a Chromium window"), "Open in an aerographene window")
        self.assertEqual(self.t("a Chromium", english=False), "a aerographene")

    def test_exclusions(self):
        for s in ["Chrome Web Store", "Chrome Enterprise", "ChromeOS", "Chrome OS", "ChromiumOS",
                  "ChromeVox", "Chromebook", "Chrome Remote Desktop", "Chrome DevTools",
                  "Chrome apps", "Chrome Apps", "Chrome Labs", "chrome://flags", "www.Chrome.com"]:
            self.assertEqual(self.t(s), s, s)

    def test_markup_untouched(self):
        s = '<ph name="X">$1<ex>Chromium</ex></ph> Chromium'
        self.assertEqual(self.t(s), '<ph name="X">$1<ex>Chromium</ex></ph> aerographene')

    def test_idempotent(self):
        s = self.t("Chromium is a Chrome")
        self.assertEqual(self.t(s), s)

    def test_helium(self):
        self.assertEqual(self.t("Meet Helium"), "Meet aerographene")
        self.assertEqual(self.t("a Helium window"), "an aerographene window")
        for s in ["helium://settings", "HeliumX", "chrome/helium.cc"]:
            self.assertEqual(self.t(s), s, s)

    def test_xtb_text(self):
        self.assertEqual(bs.xtb_text('A & B <ph name="X"/> <b>'), 'A &amp; B <ph name="X"/> &lt;b&gt;')

    def test_extra_json(self):
        extra = bs.load_extra(bs.EXTRA_DEFAULT)
        self.assertIn("IDS_SETTINGS_APPEARANCE_AND_BEHAVIOR", extra)
        self.assertFalse(any(k.startswith("_") for k in extra))
        for k, v in extra.items():
            self.assertTrue(k.startswith("IDS_"), k)
            if k not in bs.KEEP_NAMES:
                self.assertNotIn("Helium", v, k)


@unittest.skipUnless(SRC and os.path.isdir(os.path.join(SRC, "tools/grit")), "AERO_TEST_SRC não definido")
class Integration(unittest.TestCase):
    ROOTS = ["chrome/app/chromium_strings.grd", "chrome/app/generated_resources.grd",
             "components/components_chromium_strings.grd"]
    LANGS = ["pt-BR", "en-GB"]

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="aero-bs-test-")
        for d in ("chrome", "components", "tools/grit"):
            shutil.copytree(os.path.join(SRC, d), os.path.join(cls.tmp, d), dirs_exist_ok=True)
        sys.path.insert(0, os.path.join(cls.tmp, "tools", "grit"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def count(self, root, lang):
        """Carrega o grd (só o xtb de `lang`) com o grit real; devolve {nome: traduzido?}."""
        from grit import grd_reader
        path = os.path.join(self.tmp, root)
        txt = open(path, encoding="utf-8").read()
        txt = re.sub(r'<file path="[^"]+\.xtb" lang="(?!%s")[^"]+" */>' % re.escape(lang), "", txt)
        tmp = os.path.join(os.path.dirname(path), "_aero_test.grd")
        open(tmp, "w", encoding="utf-8").write(txt)
        try:
            r = grd_reader.Parse(tmp, defines=DEFINES, target_platform="linux", skip_validation_checks=True)
            r.SetOutputLanguage(lang)
            r.RunGatherers()
            res = {}
            for n in r.ActiveDescendants():
                if n.name == "message" and n.IsTranslateable() and n.GetCliques():
                    res[n.attrs.get("name")] = n.GetCliques()[0].HasTranslation(lang, "OTHER")
            return res
        finally:
            os.remove(tmp)

    def test_translations_survive(self):
        before = {(r, l): self.count(r, l) for r in self.ROOTS for l in self.LANGS}
        cmd = [sys.executable, os.path.join(HERE, "branding_strings.py"), "--src", self.tmp]
        out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
        out2 = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout  # idempotência
        self.assertIn("mensagens=0 ids_novos=0", out2)
        self.assertIn("mensagens=", out)
        self.assertIn("traduções_novas=0", out2)
        extra = bs.load_extra(bs.EXTRA_DEFAULT)
        for (r, l), b in before.items():
            a = self.count(r, l)
            self.assertEqual(set(a), set(b), r)
            self.assertGreater(sum(a.values()), 0, "sem traduções carregadas em %s %s" % (r, l))
            # nenhuma tradução existente se perde; em pt-BR as do JSON passam a existir
            lost = [n for n in a if b[n] and not a[n]]
            self.assertEqual(lost, [], "traduções perdidas em %s %s" % (r, l))
            gained = {n for n in a if a[n] and not b[n]}
            if l == bs.EXTRA_LANG:
                self.assertEqual(gained, {n for n in a if n in extra and not b[n]}, r)
            else:
                self.assertEqual(gained, set(), r)
        if os.path.isfile(os.path.join(self.tmp, "chrome/app/settings_strings.grdp")) and \
                "IDS_SETTINGS_APPEARANCE_AND_BEHAVIOR" in self.count("chrome/app/generated_resources.grd", "pt-BR"):
            pt = self.count("chrome/app/generated_resources.grd", "pt-BR")
            self.assertTrue(pt["IDS_SETTINGS_APPEARANCE_AND_BEHAVIOR"])
            g = open(os.path.join(self.tmp, "chrome/app/settings_strings.grdp"), encoding="utf-8").read()
            # "Helium" só sobra nas mensagens de KEEP_NAMES (serviços operados pelo Helium)
            left = {m.group(1) for m in re.finditer(r'<message\b[^>]*\bname="([^"]+)"[^>]*>((?:(?!</message>).)*)</message>', g, re.S)
                    if re.search(r"\bHelium\b", re.sub(r"<[^>]+>", "", m.group(2)))}
            self.assertTrue(left <= bs.KEEP_NAMES, left - bs.KEEP_NAMES)
            self.assertIn("IDS_SETTINGS_HELIUM_SERVICES", left)
        # o texto inglês mudou de fato
        s = open(os.path.join(self.tmp, "chrome/app/chromium_strings.grd"), encoding="utf-8").read()
        self.assertIn("aerographene", s)
        # e a tradução pt-BR trocou o nome
        x = open(os.path.join(self.tmp, "chrome/app/resources/chromium_strings_pt-BR.xtb"), encoding="utf-8").read()
        self.assertIn("o aerographene usa os servidores do Google", x)


if __name__ == "__main__":
    unittest.main()
