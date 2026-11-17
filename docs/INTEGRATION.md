# Integrating agents with the tracker

`track.py` is agent-agnostic: any agent that can run a shell command can report progress.

## Setup (once per build)

```sh
cp tasks.example.json my-build/tasks.json     # edit ids/titles
python3 track.py --dir my-build init --tasks my-build/tasks.json
python3 serve.py --dir my-build               # dashboard
```

`export BUILD_TRACKER_DIR=/path/to/my-build` (or pass `--dir`) so agents need no path flags.
Task file format: a list or `{"tasks": [...]}` of `{"id","title","model"}`; `model` is a free-text label.
Writes are atomic and lock-protected, so several agents may call `set` concurrently.

## The one command every agent runs

```sh
python3 track.py set <id> <pending|running|done|failed> "<note>"
```

Shared instruction text (used in every snippet below):

> Report progress with `python3 track.py set <task-id> running "<what you start>"` when you begin a task,
> and `done` or `failed` with a one-line note when you finish. Use the task ids from tasks.json.
> Never edit status.json by hand.

## Claude Code (verified: CLAUDE.md and hooks are standard Claude Code features)

Add to the project `CLAUDE.md`:

```markdown
## Build tracker
Report progress with `python3 track.py set <task-id> running "<note>"` when you start a task and
`done`/`failed` with a one-line note when finished. Task ids are in tasks.json. Never edit status.json.
```

Optional hook (`.claude/settings.json`). A hook cannot know the task id, so this only logs on a fixed task; prefer the CLAUDE.md instruction.

```json
{"hooks": {"SubagentStop": [{"hooks": [{"type": "command",
  "command": "python3 track.py set BUILD running \"subagent finished\""}]}]}}
```

(Hook schema not re-verified on this machine; check the Claude Code hooks docs before relying on it.)

## Cursor (UNVERIFIED: Cursor / cursor-agent is not installed on the machine this was written on)

Per Cursor's documented project rules, create `.cursor/rules/build-tracker.mdc`:

```markdown
---
description: Report build progress to the tracker
alwaysApply: true
---
Report progress with `python3 track.py set <task-id> running "<note>"` when you start a task and
`done`/`failed` with a one-line note when finished. Task ids are in tasks.json. Never edit status.json.
```

Cursor's agent must be allowed to run terminal commands (approve or allowlist `python3 track.py`).

## Antigravity (agy)

Verified locally: `agy` CLI exists (flags include `--print`, `--agent`, `--settings`,
`--dangerously-skip-permissions`); a global instruction file `~/.gemini/GEMINI.md` exists and
is loaded as global rules; existing projects here keep workspace rules as markdown files with
YAML front matter (`name`, `description`) under `.agents/rules/`.
Not verified: whether `agy` itself loads `.agents/rules/` (observed only as a convention in
existing repos, not from agy documentation); confirm in a test session.

Create `.agents/rules/build-tracker.md`:

```markdown
---
name: build-tracker
description: Report build progress to the tracker
---
Report progress with `python3 track.py set <task-id> running "<note>"` when you start a task and
`done`/`failed` with a one-line note when finished. Task ids are in tasks.json. Never edit status.json.
```

Fallback that works regardless: put the same text in the prompt, e.g.
`agy --print "Task T2: ... Report progress with python3 track.py set T2 running|done|failed '<note>'"`.
The agy permission allowlist (`command(...)` entries in its settings) must permit `python3`.
