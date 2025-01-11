.SILENT:
.PHONY: lint fix format test tests compile install documentation models dbdocs precommit pre-commit all clean
all: install test

lint:
	pre-commit run ruff-lint --all-files

fix:
	pre-commit run ruff-fix --hook-stage manual --all-files

format:
	pre-commit run ruff-sort-imports --all-files
	pre-commit run ruff-format --all-files

test:
	echo "Testing ..."
	docker compose up --build -d postgres
	pytest -s --pdb --pdbcls=IPython.terminal.debugger:Pdb

tests:
	make test

compile:
	pre-commit run uv-lock --all-files

install:
	uv self update
	uv sync --python-preference only-managed --python 3.12 --frozen --compile-bytecode --all-extras --group dev --group tests --group pages
	pre-commit install
	make precommit

documentation:
	mkdocs serve --open

precommit:
	pre-commit run --all-files

pre-commit:
	make precommit
