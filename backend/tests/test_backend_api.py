import importlib
import sys
import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_app():
    for module_name in list(sys.modules):
        if module_name == "backend" or module_name.startswith("backend."):
            sys.modules.pop(module_name, None)

    return importlib.import_module("backend.main")


def test_generate_creates_completed_job(monkeypatch):
    app_module = load_app()
    jobs_module = importlib.import_module("backend.app.api.routes.jobs")

    class FakeVideoService:
        async def generate(self, prompt, image_url=None, duration=5):
            del prompt, image_url, duration
            return "http://localhost:8000/generated/test.mp4"

    monkeypatch.setattr(jobs_module, "VideoGenerationService", FakeVideoService)
    client = TestClient(app_module.app)

    response = client.post(
        "/api/v1/generate",
        json={
            "prompt": "A slow cinematic flyover above mountain lake at sunrise",
            "image_url": "https://example.com/source.png",
            "duration": 5,
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["video_url"] == "http://localhost:8000/generated/test.mp4"
    assert "job_id" not in response.json()


def test_generate_requires_image_url():
    app_module = load_app()
    client = TestClient(app_module.app)

    response = client.post(
        "/api/v1/generate",
        json={
            "prompt": "A slow cinematic flyover above mountain lake at sunrise",
            "duration": 5,
        },
    )

    assert response.status_code == 422


def test_generate_rejects_invalid_image_url():
    app_module = load_app()
    client = TestClient(app_module.app)

    response = client.post(
        "/api/v1/generate",
        json={
            "prompt": "A slow cinematic flyover above mountain lake at sunrise",
            "image_url": "not-a-url",
            "duration": 5,
        },
    )

    assert response.status_code == 422


def test_generate_rejects_duration_above_max():
    app_module = load_app()
    client = TestClient(app_module.app)

    response = client.post(
        "/api/v1/generate",
        json={
            "prompt": "A slow cinematic flyover above mountain lake at sunrise",
            "image_url": "https://example.com/source.png",
            "duration": 999,
        },
    )

    assert response.status_code == 422


def test_removed_status_endpoint_returns_404():
    app_module = load_app()
    client = TestClient(app_module.app)

    response = client.get("/api/v1/status/test")
    assert response.status_code == 404


def test_generate_returns_500_on_service_error(monkeypatch):
    app_module = load_app()
    jobs_module = importlib.import_module("backend.app.api.routes.jobs")

    class FakeVideoService:
        async def generate(self, prompt, image_url=None, duration=5):
            del prompt, image_url, duration
            raise RuntimeError("upstream broke")

    monkeypatch.setattr(jobs_module, "VideoGenerationService", FakeVideoService)
    client = TestClient(app_module.app)

    response = client.post(
        "/api/v1/generate",
        json={
            "prompt": "A slow cinematic flyover above mountain lake at sunrise",
            "image_url": "https://example.com/source.png",
            "duration": 5,
        },
    )
    assert response.status_code == 500
    assert response.json()["error"] == "Video generation failed"


def test_generate_requires_api_key_when_configured(monkeypatch):
    app_module = load_app()
    jobs_module = importlib.import_module("backend.app.api.routes.jobs")

    class FakeVideoService:
        async def generate(self, prompt, image_url=None, duration=5):
            del prompt, image_url, duration
            return "http://localhost:8000/generated/test.mp4"

    monkeypatch.setattr(jobs_module, "VideoGenerationService", FakeVideoService)
    monkeypatch.setattr(jobs_module.settings, "GENERATE_API_KEY", "secret-key")

    client = TestClient(app_module.app)

    denied = client.post(
        "/api/v1/generate",
        json={
            "prompt": "A slow cinematic flyover above mountain lake at sunrise",
            "image_url": "https://example.com/source.png",
            "duration": 5,
        },
    )
    assert denied.status_code == 401

    allowed = client.post(
        "/api/v1/generate",
        headers={"X-API-Key": "secret-key"},
        json={
            "prompt": "A slow cinematic flyover above mountain lake at sunrise",
            "image_url": "https://example.com/source.png",
            "duration": 5,
        },
    )
    assert allowed.status_code == 200


def test_generate_timeout_returns_504(monkeypatch):
    app_module = load_app()
    jobs_module = importlib.import_module("backend.app.api.routes.jobs")

    class SlowVideoService:
        async def generate(self, prompt, image_url=None, duration=5):
            del prompt, image_url, duration
            await asyncio.sleep(0.02)
            return "http://localhost:8000/generated/test.mp4"

    monkeypatch.setattr(jobs_module, "VideoGenerationService", SlowVideoService)
    monkeypatch.setattr(jobs_module.settings, "GENERATION_TIMEOUT_SECONDS", 0.001)

    client = TestClient(app_module.app)
    response = client.post(
        "/api/v1/generate",
        json={
            "prompt": "A slow cinematic flyover above mountain lake at sunrise",
            "image_url": "https://example.com/source.png",
            "duration": 5,
        },
    )
    assert response.status_code == 504
    assert response.json()["error"] == "Video generation timed out"
