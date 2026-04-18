# Video generation service integrations for Runway and Minimax
import logging
from enum import Enum
from typing import Optional, Tuple

import httpx

from backend.app.config import settings

logger = logging.getLogger(__name__)


class VideoProvider(str, Enum):
    RUNWAY = "runway"
    MINIMAX = "minimax"


def normalize_provider_status(raw_status: Optional[str]) -> str:
    if not raw_status:
        return "unknown"

    normalized = raw_status.strip().lower()
    status_map = {
        "queued": "pending",
        "queueing": "pending",
        "pending": "pending",
        "submitted": "pending",
        "starting": "pending",
        "processing": "processing",
        "running": "processing",
        "in_progress": "processing",
        "completed": "completed",
        "complete": "completed",
        "success": "completed",
        "succeeded": "completed",
        "done": "completed",
        "failed": "failed",
        "error": "failed",
        "cancelled": "failed",
        "canceled": "failed",
    }
    return status_map.get(normalized, normalized)


def build_status_payload(
    job_id: str,
    raw_status: Optional[str],
    video_url: Optional[str] = None,
    progress: Optional[int] = None,
    error: Optional[str] = None,
) -> dict:
    status = normalize_provider_status(raw_status)

    if progress is None:
        progress = {
            "pending": 0,
            "processing": 50,
            "completed": 100,
            "failed": 0,
        }.get(status, 0)

    return {
        "job_id": job_id,
        "status": status,
        "video_url": video_url,
        "progress": progress,
        "error": error,
    }


class RunwayService:
    BASE_URL = "https://api.dev.runwayml.com/v1"
    API_VERSION = "2024-11-06"

    def __init__(self):
        self.api_key = settings.RUNWAY_API_KEY
        if not self.api_key:
            raise ValueError("RUNWAY_API_KEY not configured in environment")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": self.API_VERSION,
        }

    async def generate_video(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        duration: int = 5,
    ) -> Tuple[str, str]:
        try:
            valid_durations = [4, 6, 8]
            closest_duration = min(valid_durations, key=lambda x: abs(x - duration))

            payload = {
                "model": "veo3.1",
                "promptText": prompt,
                "ratio": "1280:720",
                "duration": closest_duration,
            }

            logger.info(f"Submitting video generation to Runway: {prompt[:80]}...")

            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{self.BASE_URL}/text_to_video",
                    headers=self.headers,
                    json=payload,
                )

                if response.status_code not in [200, 201]:
                    raise Exception(f"Runway API error: {response.status_code} - {response.text}")

                data = response.json()
                job_id = data.get("id")
                if not job_id:
                    raise Exception("No job ID returned from Runway API")

                return job_id, job_id
        except Exception:
            logger.exception("Error generating video with Runway")
            raise

    async def get_status(self, job_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.get(
                    f"{self.BASE_URL}/tasks/{job_id}",
                    headers=self.headers,
                )

                if response.status_code == 404:
                    return build_status_payload(job_id, "failed", error="Job not found")

                if response.status_code != 200:
                    raise Exception("Failed to get job status")

                data = response.json()
                status = data.get("status", "unknown")
                video_url = None
                if status == "COMPLETED":
                    output = data.get("output")
                    if output:
                        video_url = output[0] if isinstance(output, list) else output

                return build_status_payload(
                    job_id,
                    status,
                    video_url=video_url,
                    error=data.get("error"),
                )
        except Exception:
            logger.exception("Error checking Runway status")
            raise


class MinimaxService:
    BASE_URL = "https://api.minimax.chat/v1"

    def __init__(self):
        self.api_key = settings.MINIMAX_API_KEY
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY not configured in environment")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_video(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        duration: int = 5,
    ) -> Tuple[str, str]:
        try:
            payload = {
                "prompt": prompt,
                "duration": min(duration, 30),
                "model": "video-01",
            }
            if image_url:
                payload["image_url"] = image_url

            logger.info(f"Submitting video generation to Minimax: {prompt[:80]}...")

            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{self.BASE_URL}/video/generate",
                    headers=self.headers,
                    json=payload,
                )

                if response.status_code not in [200, 201]:
                    raise Exception(f"Minimax API error: {response.status_code}")

                data = response.json()
                job_id = data.get("task_id")
                return job_id, job_id
        except Exception:
            logger.exception("Error generating video with Minimax")
            raise

    async def get_status(self, job_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.get(
                    f"{self.BASE_URL}/video/query",
                    headers=self.headers,
                    params={"task_id": job_id},
                )

                if response.status_code != 200:
                    raise Exception("Failed to get job status")

                data = response.json()
                return build_status_payload(
                    job_id,
                    data.get("status"),
                    video_url=data.get("file_id") or data.get("video_url"),
                    progress=data.get("progress"),
                    error=data.get("error"),
                )
        except Exception:
            logger.exception("Error checking Minimax status")
            raise


class VideoGenerationService:
    def __init__(self, provider: VideoProvider = VideoProvider.RUNWAY):
        if provider == VideoProvider.RUNWAY:
            self.service = RunwayService()
        elif provider == VideoProvider.MINIMAX:
            self.service = MinimaxService()
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def generate(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        duration: int = 5,
    ) -> Tuple[str, str]:
        return await self.service.generate_video(prompt, image_url, duration)

    async def get_status(self, job_id: str) -> dict:
        return await self.service.get_status(job_id)
