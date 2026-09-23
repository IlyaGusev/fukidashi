# CLAUDE.md

## Git

- Do not force push.
- Create a new commit. Do not amend a commit.
- Do not remove a Git worktree unless the user asks.
- Do not push to `main`. Use a feature branch and a PR.

## Conventions

- Python 3.12+
- Strict mypy (`strict = true` in pyproject.toml)
- Ruff with `line-length = 100`
- Use async code for all tool handlers and API calls.
- Put all imports at the top of the file.
- Do not write code comments. Make the code explain itself: use clear names and
  extract named helpers. Keep only tool directives (`# noqa`, `# type:`,
  `# pragma`). Do not add a docstring that only repeats the code.
