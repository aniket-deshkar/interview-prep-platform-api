.PHONY: install run lint format test migrate migration worker beat up down

install:
	python -m pip install -e '.[dev]'

run:
	uvicorn interview_prep.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check .
	ruff format --check .
	mypy src

format:
	ruff check --fix .
	ruff format .

test:
	pytest

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(name)"

worker:
	celery -A interview_prep.worker.celery_app worker --loglevel=INFO

beat:
	celery -A interview_prep.worker.celery_app beat --loglevel=INFO

up:
	docker compose up --build -d

down:
	docker compose down

