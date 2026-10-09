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
        for (r, l), b in before.items():
            a = self.count(r, l)
            self.assertEqual(set(a), set(b), r)
            self.assertEqual(sum(a.values()), sum(b.values()), "traduções perdidas em %s %s" % (r, l))
            self.assertGreater(sum(a.values()), 0, "sem traduções carregadas em %s %s" % (r, l))
        # o texto inglês mudou de fato
        s = open(os.path.join(self.tmp, "chrome/app/chromium_strings.grd"), encoding="utf-8").read()
        self.assertIn("aerographene", s)
        # e a tradução pt-BR trocou o nome
        x = open(os.path.join(self.tmp, "chrome/app/resources/chromium_strings_pt-BR.xtb"), encoding="utf-8").read()
        self.assertIn("o aerographene usa os servidores do Google", x)


if __name__ == "__main__":
    unittest.main()
