<!--

Mock README.md, nothing is implemented yet so this will likely change

# Quickstart

## 1) Setup
python -m venv .venv && source .venv/bin/activate
pip install -r api/requirements.txt -r cli/requirements.txt -r tests/requirements.txt

## 2) Run server
DATA_DIR=./data uvicorn api.app:app --reload --port 8000

## 3) Use CLI
python -m cli create ./fixtures/models ./fixtures/config
python -m cli list
python -m cli download <bundle_id> --format zip

Makefile convenience:

- [ ] make run-api: uvicorn api.app:app --reload --port 8000
- [ ] make cli: python -m cli --help
- [ ] make test: pytest -q
- [ ] make fmt: black/isort/ruff

-->