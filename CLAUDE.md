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

- `src/fukidashi/settings.py`: every setting with its default, via pydantic-settings. Env vars
  are `FUKIDASHI_<FIELD>` plus `NEBIUS_API_TOKEN`; `.env` loads through it, nothing else reads
  the environment.
- `src/fukidashi/detect.py`: VLM detection + translation of text boxes (async, streamed).
  Malformed model answers raise `BadOutput`. The client has no SDK retries and a per-read
  stall timeout (`FUKIDASHI_STALL_TIMEOUT`, default 60s).
- `src/fukidashi/store.py`: `Store`, one SQLite file `data/fukidashi.db` plus image files under
  `data/pages/` (content-addressed, one file can sit in several volumes). Tables: `volumes`
  (title), `pages` (volume, position, file, `current` translation), `translations` (one row
  per successful run: model, thinking, lang, bubbles, size, usage; rows never change). A page
  keeps every run; `current` defaults to the newest and `set_current` pins an older one. Every
  page belongs to exactly one volume; single uploads go into the `Inbox` volume. On first start
  with an empty `volumes` table the old `data/volumes/*.json`, loose `data/pages/*` and
  `data/results/*.json` are imported once (loose pages land in Inbox); the old files stay.
- `src/fukidashi/jobs.py`: job queue in the same SQLite file (tables `jobs` and `steps`). A job
  points to a volume and the run options; a step points to a page and, once done, to the
  translation it made. `FUKIDASHI_WORKERS` worker tasks (default 2) each claim the next queued
  step: one-page jobs first, then oldest job first. Each step gets `FUKIDASHI_ATTEMPTS` tries
  (default 3) with backoff on bad output, timeouts, connection, rate-limit and 5xx errors, and a
  hard `FUKIDASHI_STEP_TIMEOUT` per try (default 600s). A page gets the previous page's current
  translation as context when that page has one. Steps left running at startup go back to
  queued, so jobs resume after a restart. The UI polls `GET /jobs` (latest 30 jobs, with
  streaming progress on running steps) every second while anything is active.
  `POST /jobs/{id}/retry` resubmits the unfinished pages of a finished job. Deleting a page or
  volume with an active step returns 409.
- `src/fukidashi/render.py`: typesets a translation onto its page. Finds each bubble's white interior around
  the box, erases the ink with OpenCV inpainting and draws the translation in Comic Neue at the largest
  size that fits the largest rectangle in that interior that holds the box center. Skips `sfx`. `Store.render` caches the PNG under `data/rendered/<translation id>.png`;
  `GET /translations/{id}/rendered` serves it and the Typeset toggle in the UI shows it.
- `src/fukidashi/web.py`: FastAPI routes only. JSON bodies except uploads. Volumes, pages and
  translations are addressed by integer id.
- `tests/test_jobs.py`: queue tests with a fake translator. `tests/test_store.py`: legacy import,
  reorder, context. Run `uv run pytest`.
- `src/fukidashi/static/index.html`: the UI.
- `scripts/serve.py`: runs the app on http://localhost:8083. `scripts/detect_bubbles.py`: CLI.
- `scripts/benchmark.py`: scores Nebius vision models on OpenMantra annotations (box IoU
  P/R/F1, Japanese CER, chrF vs the English reference, latency, tokens), with thinking off and
  at `--efforts` low and medium for reasoning models. Raw runs cache under `out/bench/runs/`,
  so reruns only call models for missing pages. Needs the `bench` extra.

## Server restarts

The app is served through ngrok. ngrok keeps an open connection to port 8083, so killing
every process on the port also kills ngrok. Restart only the listener:

```
kill $(lsof -t -sTCP:LISTEN -i :8083); (setsid nohup uv run scripts/serve.py > out/serve.log 2>&1 &)
```

`make serve` does this and waits until the app answers. uvicorn gets 3s to finish open
requests, then exits, so no old process keeps working the queue. `make stop`, `make log`, `make test`
and `make check` also exist. Never use `kill $(lsof -t -i :8083)` or `pkill -f` patterns that
match ngrok.
