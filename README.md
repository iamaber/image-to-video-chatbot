# Image-to-Video Chatbot

Image-to-video app with FastAPI backend and plain HTML/CSS/JS frontend. Backend handles auth, job creation, local video generation, and job history. Frontend gives simple local control surface for register, login, generate, status checks, and job history.

## Project Structure

```text
backend/
  app/                 FastAPI app code
  alembic/             DB migrations
  tests/               Backend tests
  main.py              Backend entrypoint
  init_db.py           Local DB bootstrap
frontend/
  index.html           Static UI
  styles.css           UI styles
  app.js               API client logic
```

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, JWT auth
- Model: Stable Video Diffusion via Diffusers
- Frontend: HTML, CSS, vanilla JavaScript
- DB: PostgreSQL
- Tooling: `uv`, `pytest`

## Setup

1. Install deps:

```bash
uv sync --dev
```

2. Create env file:

```bash
cp backend/.env.example backend/.env
```

3. Update `backend/.env`:

- `DATABASE_URL`
- `SECRET_KEY`
- `SVD_DEVICE`
- `PUBLIC_BASE_URL`

4. Install local model runtime:

```bash
uv add torch diffusers transformers accelerate "imageio[ffmpeg]"
```

Stable Video Diffusion is a free open-weight model, not a free hosted API. You run it locally, download the weights, and need enough disk/GPU memory for inference.

## Run Backend

Apply migrations:

```bash
uv run alembic -c backend/alembic.ini upgrade head
```

Start API:

```bash
uv run uvicorn backend.app.main:app --reload
```

Docs:

- `/docs` on your local backend server

## Run Frontend

Serve static files:

```bash
python -m http.server 3000 -d frontend
```

Open:

- your local frontend URL from the static server

Default frontend backend URL:

- your local backend base URL

## Main API Endpoints

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/token`
- `GET /auth/me`
- `GET /api/v1/providers`
- `POST /api/v1/generate`
- `GET /api/v1/status/{job_id}`
- `GET /api/v1/job/{job_id}`
- `GET /api/v1/jobs`

## Typical Flow

1. Register user.
2. Login and get bearer token.
3. Submit generation request.
4. Poll job status or open returned video URL.
5. Load user job history.

## Testing

Run backend tests:

```bash
uv run pytest -q
```

## Notes

- Backend enforces job ownership per authenticated user.
- Frontend is intentionally framework-free and easy to modify.
- CORS defaults already allow common local frontend ports.
- Generated local videos are served from `/generated/...`.
