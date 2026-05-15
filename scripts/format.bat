poetry run python -c "import app"
poetry run pytest -s
poetry run python -m ruff check --fix
poetry run python -m ruff format
poetry run python scripts/commit.py