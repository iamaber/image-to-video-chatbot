# Image-to-Video Chatbot

Image-to-video app with FastAPI backend and plain HTML/CSS/JS frontend. Backend handles local video generation. Frontend is a minimal control surface for submitting an image and prompt, then opening the generated result.

## Project Structure

```text
backend/
  app/                 FastAPI app code
  tests/               Backend tests
  main.py              Backend entrypoint
frontend/
  index.html           Static UI
  styles.css           UI styles
  app.js               API client logic
```

## Tech Stack

- Backend: FastAPI
- Model: Stable Video Diffusion via Diffusers
- Frontend: HTML, CSS, vanilla JavaScript
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

- `SVD_DEVICE`
- `PUBLIC_BASE_URL`
- `GENERATE_API_KEY` (optional, recommended outside local dev)
- `GENERATION_TIMEOUT_SECONDS` (request timeout guard for long generation jobs)

Stable Video Diffusion runtime dependencies are installed by `uv sync --dev`. The first real generation run will still download model weights locally.

Stable Video Diffusion is a free open-weight model, not a free hosted API. You run it locally and need enough disk/GPU memory for inference.

## Run Backend

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

- `POST /api/v1/generate`

`POST /api/v1/generate` accepts optional `X-API-Key` when `GENERATE_API_KEY` is configured.

## Typical Flow

1. Submit a prompt, source image URL, and duration.
2. Receive generation status and a generated video URL.
3. Open the returned video URL.

## Testing

Run backend tests:

```bash
uv run pytest -q
```

## Notes

- Frontend is intentionally framework-free and easy to modify.
- CORS defaults already allow common local frontend ports.
- Generated local videos are served from `/generated/...`.
