# build-tracker
Tiny live dashboard for parallel-agent builds, driven by Claude Code, Antigravity (agy), Cursor or any agent that can run a shell command.

- `track.py init --tasks tasks.json` creates `status.json` (see `tasks.example.json`).
- `track.py set <id> <pending|running|done|failed> "<note>"` updates a task (atomic, safe for concurrent agents).
- `serve.py` serves `index.html` + `status.json` (default 0.0.0.0:8791, no auth - LAN only).
- Use `--dir` (or `BUILD_TRACKER_DIR`) to point at the build's tracker folder.
- Agent setup snippets: `docs/INTEGRATION.md`. Tests: `python3 -m unittest discover -s tests`.
