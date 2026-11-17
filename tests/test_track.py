import json, os, pathlib, subprocess, sys, tempfile, unittest

TRACK = pathlib.Path(__file__).resolve().parent.parent / "track.py"


def run(d, *args, check=True):
    r = subprocess.run([sys.executable, str(TRACK), "--dir", str(d), *args],
                       capture_output=True, text=True)
    if check:
        assert r.returncode == 0, r.stderr
    return r


class TrackTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.d = pathlib.Path(self._t.name)
        self.tasks = self.d / "my-tasks.json"
        self.tasks.write_text(json.dumps({"tasks": [{"id": "A", "title": "a"}, {"id": "B", "title": "b", "model": "x"}]}))
        self.addCleanup(self._t.cleanup)

    def status(self):
        return json.loads((self.d / "status.json").read_text())

    def test_init_and_set(self):
        run(self.d, "init", "--tasks", str(self.tasks))
        s = self.status()
        self.assertEqual([t["id"] for t in s["tasks"]], ["A", "B"])
        run(self.d, "set", "A", "running", "going")
        run(self.d, "set", "A", "done", "all", "good")
        t = self.status()["tasks"][0]
        self.assertEqual((t["state"], t["note"]), ("done", "all good"))
        self.assertTrue(t["start"] and t["end"])
        self.assertEqual(len(self.status()["log"]), 2)

    def test_default_tasks_json_and_lazy_init(self):
        (self.d / "tasks.json").write_text(json.dumps([["Z", "zed", "m"]]))
        run(self.d, "set", "Z", "running")
        self.assertEqual(self.status()["tasks"][0]["model"], "m")

    def test_init_refuses_overwrite(self):
        run(self.d, "init", "--tasks", str(self.tasks))
        self.assertNotEqual(run(self.d, "init", "--tasks", str(self.tasks), check=False).returncode, 0)
        run(self.d, "init", "--tasks", str(self.tasks), "--force")

    def test_bad_input(self):
        run(self.d, "init", "--tasks", str(self.tasks))
        self.assertNotEqual(run(self.d, "set", "NOPE", "done", check=False).returncode, 0)
        self.assertNotEqual(run(self.d, "set", "A", "bogus", check=False).returncode, 0)
        self.assertNotEqual(run(self.d, "init", "--force", "--tasks", str(self.d / "missing.json"), check=False).returncode, 0)

    def test_no_stray_files(self):
        run(self.d, "init", "--tasks", str(self.tasks))
        run(self.d, "set", "B", "failed", "x")
        names = {p.name for p in self.d.iterdir()}
        self.assertEqual(names, {"status.json", "my-tasks.json"})

    def test_concurrent_writers(self):
        ids = ["T%d" % i for i in range(12)]
        self.tasks.write_text(json.dumps([{"id": i, "title": i} for i in ids]))
        run(self.d, "init", "--tasks", str(self.tasks))
        procs = [subprocess.Popen([sys.executable, str(TRACK), "--dir", str(self.d), "set", i, "done", "n" + i])
                 for i in ids for _ in range(2)]
        self.assertTrue(all(p.wait() == 0 for p in procs))
        s = self.status()  # must be valid JSON, no lost updates
        self.assertTrue(all(t["state"] == "done" and t["note"] == "n" + t["id"] for t in s["tasks"]))
        self.assertEqual(len(s["log"]), 24)


if __name__ == "__main__":
    unittest.main()
