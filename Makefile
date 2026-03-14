.PHONY: dev install lint clean deploy

SERVICE = yueswater-portfolio-server
REGION = asia-east1
PROJECT = yueswater-portfolio

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

deploy:
	poetry export -f requirements.txt --without-hashes -o requirements.txt
	gcloud run deploy $(SERVICE) --source . --region $(REGION) --allow-unauthenticated --port 8080 --env-vars-file env.yaml --memory 512Mi --timeout 300 --min-instances 0 --max-instances 3 --project=$(PROJECT)
