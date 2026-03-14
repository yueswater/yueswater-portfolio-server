.PHONY: dev install lint clean

dev:
	poetry run uvicorn app.main:app --reload

install:
	poetry install

lint:
	poetry run python -m py_compile app/main.py
	poetry run python -m py_compile app/models.py
	poetry run python -m py_compile app/schemas.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -f data.db
