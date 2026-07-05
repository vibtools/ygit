.PHONY: install dev test smoke lint typecheck security run worker docker-up docker-down
install:
	pip install -e ".[dev]"
dev:
	uvicorn backend.app.main:app --reload
test:
	pytest
smoke:
	python scripts/smoke_test.py --skip-db
lint:
	ruff check .
typecheck:
	mypy backend
security:
	bandit -r backend
	pip-audit
run:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
worker:
	python -m backend.workers.main
docker-up:
	docker compose up --build
docker-down:
	docker compose down
