# build-tracker
Tiny live dashboard for parallel-agent builds. `track.py set <id> <state> [note]` updates status.json
(edit TASKS in track.py); `serve.py` serves index.html + status.json (default 0.0.0.0:8791, no auth — LAN only).
Run track.py/serve.py with --dir pointing at the project's tracker folder.
