help:
	@echo "-----------------HELP-----------------"
	@echo "this project requires poetry for building."
	@echo "make install: installs the project dependencies (no dev)."
	@echo "make install-dev: installs the project dependencies (with dev)."
	@echo "make run: runs the project".
	@echo "make lint: uses linting tools to check the code."
	@echo "make format: formats the code to pass required standards."
	@echo "make type: tests types with mypy."
	@echo "make test: runs tests."
	@echo "make test-cov: runs tests with coverage and writes report."
	@echo "--------------------------------------"


install: poetry.lock
	poetry install --no-dev

install-dev: poetry.lock
	poetry install

run:
	poetry run uvicorn src.main:app

migrations:
	poetry run alembic revision --autogenerate

migrate:
	poetry run alembic upgrade head

lint:
	poetry run flake8 src tests

format:
	poetry run black src tests
	poetry run isort src tests

security:
	poetry run bandit -r src tests

type:
	poetry run mypy -p src -p tests

test:
	poetry run pytest

test-cov:
	poetry run coverage run -m pytest
	poetry run coverage report
	poetry run coverage html
