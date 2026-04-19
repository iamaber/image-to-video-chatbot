import importlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_app(tmp_path: Path):
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'

    for module_name in list(sys.modules):
        if module_name == "backend" or module_name.startswith(("backend.", "app.", "db", "config", "database", "auth", "video_service")):
            sys.modules.pop(module_name, None)

    app_module = importlib.import_module("backend.main")
    db_module = importlib.import_module("backend.app.db.session")
    models_module = importlib.import_module("backend.app.db.models")
    models_module.Base.metadata.create_all(bind=db_module.engine)
    return app_module


def register_and_login(client: TestClient, username: str) -> str:
    register_res = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "secret123",
            "full_name": username.title(),
        },
    )
    assert register_res.status_code == 200

    login_res = client.post(
        "/auth/login",
        json={"username": username, "password": "secret123"},
    )
    assert login_res.status_code == 200
    return login_res.json()["access_token"]


def test_generate_requires_auth(tmp_path):
    app_module = load_app(tmp_path)
    client = TestClient(app_module.app)

    response = client.post(
        "/api/v1/generate",
        json={
            "prompt": "A slow cinematic flyover above mountain lake at sunrise",
            "provider": "svd",
            "image_url": "https://example.com/source.png",
            "duration": 5,
        },
    )

    assert response.status_code == 401


def test_oauth_token_endpoint_returns_bearer_token(tmp_path):
    app_module = load_app(tmp_path)
    client = TestClient(app_module.app)
    register_and_login(client, "alice")

    response = client.post(
        "/auth/token",
        data={"username": "alice", "password": "secret123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_jobs_are_owned_and_listed_per_user(tmp_path, monkeypatch):
    app_module = load_app(tmp_path)
    jobs_module = importlib.import_module("backend.app.api.routes.jobs")

    class FakeVideoService:
        def __init__(self, provider):
            self.provider = provider

        async def generate(self, prompt, image_url=None, duration=5):
            return (f"{self.provider.value}-provider-job", "unused-status-url")

        async def get_status(self, job_id):
            return {
                "job_id": job_id,
                "status": "completed",
                "video_url": "http://127.0.0.1:8000/generated/test.mp4",
                "progress": 100,
                "error": None,
            }

    monkeypatch.setattr(jobs_module, "VideoGenerationService", FakeVideoService)
    client = TestClient(app_module.app)

    alice_token = register_and_login(client, "alice")
    bob_token = register_and_login(client, "bob")

    alice_job = client.post(
        "/api/v1/generate",
        headers={"Authorization": f"Bearer {alice_token}"},
        json={
            "prompt": "A slow cinematic flyover above mountain lake at sunrise",
            "provider": "svd",
            "image_url": "https://example.com/source.png",
            "duration": 5,
        },
    )
    assert alice_job.status_code == 200
    alice_job_id = alice_job.json()["job_id"]
    assert alice_job.json()["status"] == "completed"

    bob_job = client.post(
        "/api/v1/generate",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={
            "prompt": "Robot drummer on neon stage with moving camera and smoke",
            "provider": "svd",
            "image_url": "https://example.com/other-source.png",
            "duration": 6,
        },
    )
    assert bob_job.status_code == 200
    bob_job_id = bob_job.json()["job_id"]

    alice_jobs = client.get(
        "/api/v1/jobs",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert alice_jobs.status_code == 200
    assert [job["job_id"] for job in alice_jobs.json()] == [alice_job_id]

    forbidden_read = client.get(
        f"/api/v1/job/{bob_job_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert forbidden_read.status_code == 404


def test_status_normalization():
    from backend.app.services.video_service import normalize_provider_status

    assert normalize_provider_status("PROCESSING") == "processing"
    assert normalize_provider_status("queued") == "pending"
    assert normalize_provider_status("succeeded") == "completed"
    assert normalize_provider_status("canceled") == "failed"
