# fastapi-user-service

Internal user management REST API built with FastAPI.

## Setup
pip install -r requirements.txt
uvicorn main:app --reload

## Running Tests
pytest tests/ -v

## Authentication
Include Authorization: Bearer dev-token-123 in all /api/ requests.
