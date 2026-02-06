APP=src/app.py

.PHONY: run venv install install-dev lint format test

venv:
	python3 -m venv venv

install:
	venv/bin/pip install -U pip
	venv/bin/pip install -r requirements.txt

install-dev:
	venv/bin/pip install -r requirements-dev.txt
	venv/bin/pre-commit install

run:
	venv/bin/streamlit run $(APP)

lint:
	venv/bin/ruff check .

format:
	venv/bin/ruff format .
	venv/bin/black .

test:
	venv/bin/pytest
