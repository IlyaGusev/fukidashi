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
  Malformed model answers raise `BadOutput`; `RETRYABLE` lists the errors worth another try. The
  client has no SDK retries and a per-read stall timeout (`FUKIDASHI_STALL_TIMEOUT`, default 60s).
- `src/fukidashi/store.py`: page, result, volume and story-memory files under `data/`;
  `translate_page`. With `FUKIDASHI_VOLUME_MEMORY` (default true) a volume page is translated with
  the story memory saved after the nearest earlier page of that volume, then read into the memory
  (speakers go onto its bubbles). The translation is saved before the memory update, the update's
  tokens are added to the page's usage, and a failed update is marked `memoryFailed`. Memory lives
  in `data/memory/<volume>__<model>__<lang>.json`, one snapshot per page. A volume can continue
  another (`continues` in its volume file, set with `POST /volumes/{name}/continues`); until it has
  notes of its own, its pages start from the other volume's latest notes through `carry_over`.
  Single pages keep the previous page's text as context.
- `src/fukidashi/jobs.py`: job queue on SQLite (`data/jobs.db`, tables `jobs` and `steps`).
  `FUKIDASHI_WORKERS` worker tasks (default 2) each claim the next queued step: single pages
  first, then volume pages, oldest job first. Each step gets `FUKIDASHI_ATTEMPTS` tries (default
  3) with backoff on bad output, timeouts, connection, rate-limit and 5xx errors, and a hard
  `FUKIDASHI_STEP_TIMEOUT` per try (default 600s). A page gets the previous page's text as
  context only when that result is already on disk. With volume memory on, a volume's pages run one
  at a time in order while other jobs use the other workers, and each volume page gets twice
  `FUKIDASHI_STEP_TIMEOUT` because it makes two calls. Steps left running at startup go back to
  queued, so jobs resume after a restart. The UI polls `GET /jobs` (latest 30 jobs, with
  streaming progress on running steps) every second while anything is active.
  `POST /jobs/{id}/retry` resubmits the unfinished pages of a finished job.
- `src/fukidashi/render.py`: typesets a result onto its page. Finds each bubble's white interior around
  the box, erases the ink with OpenCV inpainting and draws the translation in Comic Neue at the largest
  size that fits the largest rectangle in that interior that holds the box center. Skips `sfx`. `store.render_page` caches the PNG under `data/rendered/`;
  `GET /pages/{name}/rendered` serves it and the Typeset toggle in the UI shows it.
- `src/fukidashi/memory.py`: story memory for whole-book translation. Per page the model returns
  a PATCH (new or changed characters, glossary, threads, questions, plus speakers), never the whole
  memory, and `apply_patch` merges it by key, so an entry the model leaves out is kept. Fields are
  clipped on merge, and `memory_view` renders the memory for prompts within
  `FUKIDASHI_MEMORY_CHARS` (default 16000) by stepping down `VIEW_LEVELS`. Once the whole glossary
  no longer fits, the view shows the terms found in the current page's text, then the earliest
  terms that fit; if even the last level is too long, whole lines are cut from the end so the view
  never exceeds the budget. `carry_over` seeds the next chapter with the cast, glossary and open threads.
- `src/fukidashi/book.py`: `translate_book` reads pages in order (memory update, then first-pass
  translation with that memory), checkpoints after every page, records a failed page in its stats
  and snapshot instead of silently keeping the old memory, and can run a second pass with the final
  memory (`second_pass`, off by default: it revised 0 lines in every run). Checkpoints are written
  atomically. A rerun on the same checkpoint translates pages whose translation failed again, with the
  memory saved for that page. `BookOptions` switches the memory off, adds the lines and translations of the last
  `recent_pages` pages to the translation prompt, or skips the second pass.
  `scripts/translate_book.py` runs it on an OpenMantra book (`--first`, `--count`, `--seed` a
  previous volume JSON, `--seed_after` a page of it instead of its last, `--memory=False`,
  `--recent_pages N`, `--second_pass=True`, `--effort low` to let the model think a little,
  `--memory_model` and `--memory_effort` to read pages with a different model than the one that
  translates) and writes `out/books/<name>.json`, which records `first` and `count`. Page numbers
  in a run start at 1 from `--first`.
- `scripts/audit_book.py`: for one volume JSON, lists glossary terms the translations do not
  always render as the glossary says, and the lines with the lowest sentence chrF. Writes
  `out/audit/<name>.md`. Needs the `bench` extra.
- `scripts/paper_score.py`: pooled, case-sensitive corpus chrF over volume JSONs, the protocol of
  Lippmann et al. (COLING 2025), whose best OpenMantra test-set score (boureisougi, rasetugari,
  tencho_isoro) is 36.8 with GPT-4 Turbo. Needs the `bench` extra.
- `src/fukidashi/compare.py` and `scripts/compare_books.py`: score volume JSONs on the pages they
  share: starting confidence, glossary adherence (names kept as the run's own final glossary),
  agreement with the professional renderings of glossary terms, and chrF vs the reference, each
  also on the first `--first` pages. Needs the `bench` extra.
- `src/fukidashi/web.py`: FastAPI routes only.
- `tests/test_jobs.py`: queue tests with a fake translator. Run `uv run pytest`.
- `src/fukidashi/static/index.html`: the UI. The Volume tab picks the volume a volume continues,
  shows the story notes (`GET /volumes/{name}/memory`, or the carried-over notes before the first
  page) and each box its speaker.
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
