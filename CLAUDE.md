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
- `src/fukidashi/prompts/`: jinja2 templates for the VLM prompts. `detect.jinja` takes `w`,
  `h`, `lang`, `context` (previous page lines) and `characters` (name to description).
- `src/fukidashi/detect.py`: VLM detection + translation of text boxes (async, streamed). The
  same call also returns `characters` (name as used in the translation, or a visual label when
  no name is known yet, plus a short description) for the major characters on the page. When a
  page reveals a labelled character's name, `was` holds the old label. Malformed model answers
  raise `BadOutput`. The client has no SDK retries and a per-read stall timeout
  (`FUKIDASHI_STALL_TIMEOUT`, default 60s).
- `src/fukidashi/store.py`: page, result and volume files under `data/`; `translate_page`.
  `volume_characters` merges the `characters` of every page result in the volume, in page order,
  later pages refining earlier descriptions and `was` dropping the replaced label.
  `GET /volumes/{name}/characters` serves it and the Volume tab shows it under Characters.
- `src/fukidashi/jobs.py`: job queue on SQLite (`data/jobs.db`, tables `jobs` and `steps`).
  `FUKIDASHI_WORKERS` worker tasks (default 2) each claim the next queued step: single pages
  first, then volume pages, oldest job first. Each step gets `FUKIDASHI_ATTEMPTS` tries (default
  3) with backoff on bad output, timeouts, connection, rate-limit and 5xx errors, and a hard
  `FUKIDASHI_STEP_TIMEOUT` per try (default 600s). A page gets the previous page's text as
  context only when that result is already on disk. A page in a volume job also gets the
  volume's character compendium as it is on disk when the page starts. Steps left running at
  startup go back to queued, so jobs resume after a restart. The UI polls `GET /jobs` (latest 30
  jobs, with streaming progress on running steps) every second while anything is active.
  `POST /jobs/{id}/retry` resubmits the unfinished pages of a finished job.
- `src/fukidashi/render.py`: typesets a result onto its page. Finds each bubble's white interior around
  the box, erases the ink with OpenCV inpainting and draws the translation in Comic Neue at the largest
  size that fits. Skips `sfx`. `store.render_page` caches the PNG under `data/rendered/`;
  `GET /pages/{name}/rendered` serves it and the Typeset toggle in the UI shows it.
- `src/fukidashi/web.py`: FastAPI routes only.
- `tests/test_jobs.py`: queue tests with a fake translator. Run `uv run pytest`.
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
