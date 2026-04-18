# Repository Guidelines

## Project Structure & Module Organization
This repo is split by delivery surface. `backend/` contains the FastAPI service, Alembic migrations, and Python tests. Main app code lives in `backend/app/`, with routes in `backend/app/api/routes/`, shared schemas in `backend/app/api/schemas.py`, auth/config in `backend/app/core/` and `backend/app/config.py`, DB models/session code in `backend/app/db/`, and provider integrations in `backend/app/services/`. `frontend/` is a static HTML/CSS/JS client that talks to the API directly.

## Build, Test, and Development Commands
Use `uv` for backend work.

- `uv sync --dev`: install backend dependencies.
- `uv run uvicorn backend.app.main:app --reload`: run API locally.
- `uv run python backend/init_db.py`: create tables for local development.
- `uv run alembic -c backend/alembic.ini upgrade head`: apply DB migrations.
- `uv run pytest -q`: run backend tests from `backend/tests/`.
- `python -m http.server 3000 -d frontend`: serve frontend at `http://127.0.0.1:3000`.

## Coding Style & Naming Conventions
Follow existing Python style: 4-space indentation, `snake_case` for functions/variables, `PascalCase` for models and schemas, and uppercase settings names. Keep backend modules narrow by layer: routes should orchestrate, repositories should query, services should call external providers. Frontend stays framework-free; keep selectors simple, functions small, and CSS organized around layout strips instead of component stacks.

## Testing Guidelines
Add backend tests under `backend/tests/` with `test_*.py` names. Prefer FastAPI route coverage, auth flow checks, and provider-service normalization tests. Use SQLite-backed test setup when possible so tests stay fast and isolated.

## Commit & Pull Request Guidelines
Use short, imperative commit messages. Keep each commit scoped to one logical change. PRs should call out API changes, new env vars, migration requirements, and frontend behavior changes. Include screenshots when UI layout or interaction changes.

## Security & Configuration Tips
Keep secrets in `.env`, never in code. Use `backend/.env.example` as template. Review `CORS_ORIGINS`, `SECRET_KEY`, provider API keys, and `DATABASE_URL` before deployment.
