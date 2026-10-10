#!/usr/bin/env python3
"""Testes das funções puras do aero-top (stdlib unittest)."""
import importlib.machinery
import importlib.util
import os
import unittest

_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aero-top")
_spec = importlib.util.spec_from_loader("aero_top", importlib.machinery.SourceFileLoader("aero_top", _p))
at = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(at)

LOG = """[2026-10-10 05:49:59Z INFO Terminal] WRITE LINE: 2026-10-10 05:49:59Z: Running job: build
   at System.Foo
[2026-10-10 05:53:34Z INFO Terminal] WRITE LINE: 2026-10-10 05:53:34Z: Job build completed with result: Failed
[2026-10-10 06:01:03Z INFO Terminal] WRITE LINE: 2026-10-10 06:01:03Z: Running job: build
"""


class T(unittest.TestCase):
    def test_quota(self):
        self.assertEqual(at.parse_quota("12s"), 12.0)
        self.assertAlmostEqual(at.parse_quota("800ms"), 0.8)
        self.assertIsNone(at.parse_quota("infinity"))

    def test_runner_log(self):
        runs = at.parse_runner_log(LOG)
        self.assertEqual(len(runs), 2)
        self.assertEqual(runs[0][2:], ["build", "Failed"])
        self.assertEqual(runs[0][1] - runs[0][0], 215)
        self.assertIsNone(runs[1][3])

    def test_clean_line(self):
        raw = "2026-10-10T06:23:10.9Z \x1b[32m##[group]hello\x1b[0m\n2026-10-10T06:23:11.0Z\n"
        self.assertEqual(at.clean_log_line(raw), "hello")

    def test_worker_head(self):
        h = at.parse_worker_head('"k": "repository",\n "v": "a/b"\n"jobDisplayName": "build",')
        self.assertEqual((h["repo"], h["job"]), ("a/b", "build"))

    def test_fmt(self):
        self.assertEqual(at.fmt_dur(3725), "1h02m")
        self.assertEqual(at.fmt_dur(75), "1m15s")

    def test_render_fits(self):
        st = at.Sampler()
        st.tick()
        cv = at.Canvas(80, 24)
        at.render(cv, st, at.Charset(False, False))
        self.assertTrue(all(len(r) <= 80 for r in cv.rows()))


if __name__ == "__main__":
    unittest.main()
