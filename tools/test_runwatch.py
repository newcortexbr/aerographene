import importlib.machinery, importlib.util, os, unittest
from datetime import datetime, timezone

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runwatch")
loader = importlib.machinery.SourceFileLoader("runwatch", p)
spec = importlib.util.spec_from_loader("runwatch", loader)
rw = importlib.util.module_from_spec(spec); loader.exec_module(rw)

def run(status, conclusion=None, steps=(), **kw):
    r = {"databaseId": 1, "status": status, "conclusion": conclusion, "headSha": "abcdef123456",
         "headBranch": "main", "attempt": 1, "createdAt": "2026-10-10T06:00:00Z",
         "startedAt": "2026-10-10T06:00:10Z", "updatedAt": "2026-10-10T06:10:10Z",
         "jobs": [{"steps": list(steps)}]}
    r.update(kw); return r

class T(unittest.TestCase):
    def test_states(self):
        self.assertEqual(rw.state_of(run("queued")), "fila")
        self.assertEqual(rw.state_of(run("in_progress")), "rodando")
        self.assertEqual(rw.state_of(run("completed", "success")), "ok")
        self.assertEqual(rw.state_of(run("completed", "cancelled")), "cancelado")
        self.assertEqual(rw.state_of(run("completed", "failure")), "falhou")
        self.assertEqual(rw.state_of(run("completed", "failure", jobs=[])), "não iniciado")
    def test_step(self):
        r = run("in_progress", steps=[{"name": "a", "status": "completed", "conclusion": "success"},
                                      {"name": "build", "status": "in_progress"}])
        self.assertEqual(rw.current_step(r), "build")
        r = run("completed", "failure", steps=[{"name": "smoke test", "status": "completed", "conclusion": "failure"}])
        self.assertEqual(rw.current_step(r), "smoke test")
    def test_elapsed(self):
        now = datetime(2026, 10, 10, 6, 5, 10, tzinfo=timezone.utc)
        self.assertEqual(rw.elapsed(run("in_progress"), now), "5m00s")
        self.assertEqual(rw.elapsed(run("completed", "success")), "10m00s")
    def test_ninja(self):
        self.assertEqual(rw.parse_ninja("x\n[12/345] CXX a.o\n[13/345] CXX b.o"), "[13/345]")
        self.assertIsNone(rw.parse_ninja("nada"))
    def test_errors(self):
        log = "build\tstep\t2026-10-10T06:00:00.1Z FAILED: obj/a.o\nbuild\tstep\tok line\n" + \
              "\n".join(f"j\ts\terror: e{i} " + "x" * 400 for i in range(30))
        out = rw.extract_errors(log)
        self.assertEqual(len(out), 20)
        self.assertEqual(out[0], "FAILED: obj/a.o")
        self.assertTrue(all(len(l) <= 300 for l in out))
    def test_dur(self):
        self.assertEqual(rw.parse_dur("3h"), 10800); self.assertEqual(rw.parse_dur("90"), 90)
    def test_line(self):
        self.assertIn("abcdef1", rw.status_line(run("completed", "success")))

if __name__ == "__main__":
    unittest.main()
