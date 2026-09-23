PORT ?= 8083
LOG  := out/serve.log

.PHONY: serve stop log test check

# Kill only the listener. ngrok holds a client connection to the port and must survive.
serve:
	@mkdir -p out
	@pids=$$(lsof -t -sTCP:LISTEN -i :$(PORT)); [ -z "$$pids" ] || kill $$pids
	@sleep 1
	@(setsid nohup uv run scripts/serve.py --port $(PORT) > $(LOG) 2>&1 &)
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		curl -sf -o /dev/null localhost:$(PORT)/jobs && echo "up on http://localhost:$(PORT)" && exit 0; \
		sleep 1; \
	done; echo "did not start, see $(LOG)"; tail -20 $(LOG); exit 1

stop:
	@pids=$$(lsof -t -sTCP:LISTEN -i :$(PORT)); [ -z "$$pids" ] || kill $$pids

log:
	tail -f $(LOG)

test:
	uv run pytest

check:
	uv run ruff check src tests scripts
	uv run ruff format --check src tests scripts
	uv run mypy src tests scripts
