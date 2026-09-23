# CLAUDE.md

## Git

- Do not force push.
- Create a new commit. Do not amend a commit.
- Do not remove a Git worktree unless the user asks.

## Conventions

- Python 3.12+
- Strict mypy (`strict = true` in pyproject.toml)
- Ruff with `line-length = 100`
- Use async code for all tool handlers and API calls.
- Put all imports at the top of the file.
- Do not write code comments. Make the code explain itself: use clear names and
  extract named helpers. Keep only tool directives (`# noqa`, `# type:`,
  `# pragma`). Do not add a docstring that only repeats the code.

## Project

Manga/comic translation. VLM calls go to Nebius Token Factory, token in `.env` as
`NEBIUS_API_TOKEN`.

- `src/panelogue/settings.py`: every setting with its default, via pydantic-settings. Env vars
  are `PANELOGUE_<FIELD>` plus `NEBIUS_API_TOKEN`; `.env` loads through it, nothing else reads
  the environment.
- `src/panelogue/detect.py`: VLM detection + translation of text boxes (async, streamed).
  Malformed model answers raise `BadOutput`. The client has no SDK retries and a per-read
  stall timeout (`PANELOGUE_STALL_TIMEOUT`, default 60s).
- `src/panelogue/store.py`: page, result and volume files under `data/`; `translate_page`.
- `src/panelogue/jobs.py`: job queue. Every page of a job is its own task; a semaphore caps
  concurrent VLM calls at `PANELOGUE_WORKERS` (default 2). Each page gets `PANELOGUE_ATTEMPTS`
  tries (default 3) with backoff on bad output, timeouts, connection, rate-limit and 5xx errors,
  and a hard `PANELOGUE_STEP_TIMEOUT` per try (default 600s). A page gets the previous page's
  text as context only when that result is already on disk. Jobs persist under `data/jobs/`
  and resume after a restart; the UI follows them over SSE at `/events`.
  `POST /jobs/{id}/retry` resubmits the unfinished pages of a finished job.
- `src/panelogue/web.py`: FastAPI routes only.
- `tests/test_jobs.py`: queue tests with a fake translator. Run `uv run pytest`.
- `src/panelogue/static/index.html`: the UI.
- `scripts/serve.py`: runs the app on http://localhost:8083. `scripts/detect_bubbles.py`: CLI.
- `scripts/benchmark.py`: scores Nebius vision models on OpenMantra annotations (box IoU
  P/R/F1, Japanese CER, chrF vs the English reference, latency, tokens). Raw runs cache under
  `out/bench/runs/`, so reruns only call models for missing pages. Needs the `bench` extra.

## Server restarts

The app is served through ngrok. ngrok keeps an open connection to port 8083, so killing
every process on the port also kills ngrok. Restart only the listener:

```
kill $(lsof -t -sTCP:LISTEN -i :8083); (setsid nohup uv run scripts/serve.py > out/serve.log 2>&1 &)
```

`make serve` does this and waits until the app answers. `make stop`, `make log`, `make test`
and `make check` also exist. Never use `kill $(lsof -t -i :8083)` or `pkill -f` patterns that
match ngrok.
