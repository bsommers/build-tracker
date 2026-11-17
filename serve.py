"""Serve the tracker. Usage: serve.py [--host 0.0.0.0] [--port 8791] [--dir DIR]
index.html is served from this script's dir; status.json is read from --dir (default: here)."""
import argparse, functools, http.server, pathlib, shutil
p = argparse.ArgumentParser()
p.add_argument("--host", default="0.0.0.0"); p.add_argument("--port", type=int, default=8791)
p.add_argument("--dir", default=str(pathlib.Path(__file__).parent))
a = p.parse_args()
d = pathlib.Path(a.dir).resolve()
if d != pathlib.Path(__file__).parent.resolve():
    shutil.copy(pathlib.Path(__file__).with_name("index.html"), d / "index.html")
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(d))
http.server.ThreadingHTTPServer((a.host, a.port), H).serve_forever()
