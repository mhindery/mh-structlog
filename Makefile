.SILENT:
.PHONY : all
all : install requirements lint format test

lint:
	pre-commit run ruff-lint --all-files

fix:
	pre-commit run ruff-fix --hook-stage manual --all-files

format:
	pre-commit run ruff-sort-imports --all-files
	pre-commit run ruff-format --all-files

# test:
# 	echo "Testing ..."
# 	pytest

compile:
	# Compile requirements from .in to .txt files
	uv pip compile requirements.in -o requirements.txt --generate-hashes -q --emit-index-url --prerelease=allow

install:
	# Install python environment, downloading python if necessary
	uv python install 3.12.5
	uv venv --allow-existing --python-preference only-managed --python 3.12.5
	# uv python pin

	# Install requirements
	uv pip install -r requirements.txt

	# Check if installed packages are all compatible
	uv pip check

	# Install precommit hooks
	# pre-commit install
