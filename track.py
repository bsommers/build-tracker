#!/usr/bin/env python3
"""Agent-agnostic build tracker (stdlib only).

  track.py init [--tasks FILE] [--force]       create status.json from a task list
  track.py set <id> <state> [note...]          update one task
  track.py show                                print current status

States: pending running done failed
Options (before or after the command): --dir DIR (default: this script's folder,
or $BUILD_TRACKER_DIR), --tasks FILE (default: DIR/tasks.json, or $BUILD_TRACKER_TASKS).

tasks.json: a list, or {"tasks": [...]}, of {"id","title","model"?}; "model" is
an optional free-text label for whichever agent/model owns the task.
status.json is rewritten atomically under a lock, so concurrent agents are safe.
"""
import argparse, contextlib, json, os, pathlib, sys, tempfile, time

STATES = ("pending", "running", "done", "failed")
LOCK_STALE = 30.0


def load_tasks(path):
    data = json.loads(pathlib.Path(path).read_text())
    items = data["tasks"] if isinstance(data, dict) else data
    out, seen = [], set()
    for it in items:
        if isinstance(it, (list, tuple)):
            it = dict(zip(("id", "title", "model"), it))
        tid = str(it["id"])
        if tid in seen:
            raise ValueError("duplicate task id: " + tid)
        seen.add(tid)
        out.append({"id": tid, "title": str(it.get("title", tid)), "model": str(it.get("model", "")),
                    "state": "pending", "note": "", "start": None, "end": None})
    if not out:
        raise ValueError("task list is empty")
    return out


@contextlib.contextmanager
def lock(d):
    """Cross-platform advisory lock via O_EXCL lock file; breaks stale locks."""
    lp = d / ".status.lock"
    deadline = time.time() + 15
    while True:
        try:
            fd = os.open(lp, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - lp.stat().st_mtime > LOCK_STALE:
                    lp.unlink()
                    continue
            except FileNotFoundError:
                continue
            if time.time() > deadline:
                raise TimeoutError("could not acquire " + str(lp))
            time.sleep(0.01)
    try:
        yield
    finally:
        with contextlib.suppress(FileNotFoundError):
            lp.unlink()


def atomic_write(path, obj):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".status.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise


def tasks_path(a, d):
    return pathlib.Path(a.tasks or os.environ.get("BUILD_TRACKER_TASKS") or d / "tasks.json")


def fresh(a, d):
    return {"tasks": load_tasks(tasks_path(a, d)), "log": [], "updated": time.time()}


def main(argv=None):
    p = argparse.ArgumentParser(prog="track.py", description=__doc__.split("\n")[0])
    p.add_argument("--dir"); p.add_argument("--tasks")
    sub = p.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("init"); pi.add_argument("--force", action="store_true")
    pi.add_argument("--tasks", dest="tasks2")
    ps = sub.add_parser("set"); ps.add_argument("id"); ps.add_argument("state", choices=STATES)
    ps.add_argument("note", nargs="*")
    sub.add_parser("show")
    a = p.parse_args(argv)
    if getattr(a, "tasks2", None):
        a.tasks = a.tasks2
    d = pathlib.Path(a.dir or os.environ.get("BUILD_TRACKER_DIR") or pathlib.Path(__file__).resolve().parent)
    d.mkdir(parents=True, exist_ok=True)
    F = d / "status.json"
    try:
        with lock(d):
            if a.cmd == "init":
                if F.exists() and not a.force:
                    print("status.json exists; use --force to overwrite", file=sys.stderr)
                    return 1
                atomic_write(F, fresh(a, d))
                return 0
            st = json.loads(F.read_text()) if F.exists() else fresh(a, d)
            if a.cmd == "show":
                for t in st["tasks"]:
                    print(t["id"], t["state"], t["title"], t["note"])
                return 0
            for t in st["tasks"]:
                if t["id"] == a.id:
                    break
            else:
                print("unknown task id: " + a.id, file=sys.stderr)
                return 1
            now = time.time()
            t["state"], t["note"] = a.state, " ".join(a.note)
            if a.state == "running":
                t["start"], t["end"] = now, None
            elif a.state in ("done", "failed"):
                t["end"] = now
            st["log"].append([now, a.id, a.state, t["note"]])
            st["updated"] = now
            atomic_write(F, st)
    except (OSError, ValueError, KeyError, TimeoutError) as e:
        print("track.py: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
