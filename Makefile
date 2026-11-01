.PHONY: all test benchmark starter repro lint check dev server clean

PYTHON ?= python3
NPM ?= npm

all: test check

server:
	$(PYTHON) api_server.py --port 8000

dev:
	$(PYTHON) dev_server.py

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

benchmark:
	$(PYTHON) erl_rma_benchmark.py --seed 20261022 --scale 1.0 --out ./erl_rma_export

starter:
	$(PYTHON) erl_rma_benchmark.py --seed 20261022 --scale 0.1 --out ./erl_rma_export_starter

repro:
	$(PYTHON) erl_rma_benchmark.py --seed 20261022 --scale 0.1 --repro-check

lint:
	@which ruff >/dev/null 2>&1 && ruff check . || echo "ruff not installed, skipping Python lint"
	@which mypy >/dev/null 2>&1 && mypy core/ tests/ api_server.py erl_rma_benchmark.py || echo "mypy not installed, skipping typecheck"
	$(NPM) run lint || true

check: test
	$(NPM) run typecheck
	$(NPM) run build

clean:
	rm -rf dist /tmp/baseline_* /tmp/repro_*
