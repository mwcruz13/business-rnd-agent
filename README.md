# BMI Consultant App

Containerized prototype for the 8-step BMI consultant workflow.

## Services

- `bmi-postgres`: PostgreSQL + pgvector state store managed by this compose stack
- `bmi-backend`: FastAPI + LangGraph runtime + CLI entrypoint
- `bmi-frontend`: Streamlit UI

## Quick Start

1. Create `backend/.env` locally with the required application, database, and model settings. Do not commit environment files.
2. Run `make up`.
3. The compose stack will start PostgreSQL, the backend, and the frontend together.
4. Visit `http://localhost:8501` for the UI or run `make cli -- run --input <path>`.
