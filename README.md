# Image-to-Video Chatbot

Simple local image-to-video app:
- FastAPI backend
- Plain HTML/CSS/JS frontend
- Stable Video Diffusion (Diffusers) for generation

## Quick Start

1) Install dependencies

```bash
uv sync --dev
```

2) Create env file

```bash
cp backend/.env.example backend/.env
```

3) Start backend

```bash
uv run uvicorn backend.app.main:app --reload
```

4) Start frontend

```bash
python -m http.server 3000 -d frontend
```

Then open the frontend in your browser.

## Required Config

In `backend/.env`, usually set:
- `SVD_DEVICE`
- `PUBLIC_BASE_URL`
- `GENERATED_MEDIA_DIR` (default `backend/generated`)

Optional but useful:
- `GENERATE_API_KEY` (if set, requests must send `X-API-Key`)
- `GENERATION_TIMEOUT_SECONDS`

## API

- `POST /api/v1/generate`

Example:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cinematic drone shot over snowy mountains at sunrise",
    "image_url": "https://example.com/source.png",
    "duration": 5
  }'
```

If `GENERATE_API_KEY` is configured, include the header:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "prompt": "A cinematic drone shot over snowy mountains at sunrise",
    "image_url": "https://example.com/source.png",
    "duration": 5
  }'
```

## Notes

- First real generation may take longer because model weights are downloaded.
- Generated videos are served from `/generated/...`.
- API docs are available at `/docs`.

## Tests

```bash
uv run pytest -q
```
