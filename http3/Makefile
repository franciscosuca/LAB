.PHONY: install install-dev certs serve bench quickstart test lint clean

install:
	python3 -m venv .venv
	.venv/bin/pip install -q --upgrade pip
	.venv/bin/pip install -e ".[charts]"

install-dev:
	.venv/bin/pip install -e ".[charts,dev]"

certs:
	.venv/bin/httpbench certs

serve:
	.venv/bin/httpbench serve

bench:
	.venv/bin/httpbench bench --charts

quickstart:
	.venv/bin/httpbench quickstart --charts

test:
	.venv/bin/pytest -v

lint:
	.venv/bin/ruff check src tests

clean:
	rm -rf results/*.json results/*.csv results/*.png certs/*.pem certs/*.crt certs/*.key
	find . -name __pycache__ -exec rm -rf {} +
