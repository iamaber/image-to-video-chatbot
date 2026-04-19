# Video generation service integrations
import asyncio
import logging
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

import httpx
from PIL import Image

from backend.app.config import settings

logger = logging.getLogger(__name__)
STATUS_ALIASES = {
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
DEFAULT_PROGRESS_BY_STATUS = {
    "pending": 0,
    "processing": 50,
    "completed": 100,
    "failed": 0,
}


class VideoProvider(str, Enum):
    SVD = "svd"


def normalize_provider_status(raw_status: Optional[str]) -> str:
    if not raw_status:
        return "unknown"

    normalized = raw_status.strip().lower()
    return STATUS_ALIASES.get(normalized, normalized)


def build_status_payload(
    job_id: str,
    raw_status: Optional[str],
    video_url: Optional[str] = None,
    progress: Optional[int] = None,
    error: Optional[str] = None,
) -> dict:
    status = normalize_provider_status(raw_status)

    if progress is None:
        progress = DEFAULT_PROGRESS_BY_STATUS.get(status, 0)

    return {
        "job_id": job_id,
        "status": status,
        "video_url": video_url,
        "progress": progress,
        "error": error,
    }


class StableVideoDiffusionService:
    def __init__(self):
        self.model_id = settings.SVD_MODEL_ID
        self.device = settings.SVD_DEVICE
        self.output_dir = Path(settings.GENERATED_MEDIA_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._pipeline = None

    @property
    def uses_cpu(self) -> bool:
        return self.device == "cpu"

    def _get_pipeline(self):
        if self._pipeline is not None:
            return self._pipeline

        try:
            import torch
            from diffusers import StableVideoDiffusionPipeline
        except ImportError as exc:
            raise ValueError(
                "Stable Video Diffusion dependencies missing. Install torch, diffusers, transformers, accelerate, and imageio[ffmpeg]."
            ) from exc

        torch_dtype = torch.float16 if not self.uses_cpu else torch.float32
        pipe = StableVideoDiffusionPipeline.from_pretrained(
            self.model_id,
            torch_dtype=torch_dtype,
            variant="fp16" if torch_dtype == torch.float16 else None,
        )

        if self.uses_cpu:
            pipe.to("cpu")
        else:
            pipe.enable_model_cpu_offload()

        self._pipeline = pipe
        return pipe

    async def _download_image(self, image_url: str) -> Image.Image:
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
            response = await client.get(image_url)
            response.raise_for_status()

        image = Image.open(BytesIO(response.content)).convert("RGB")
        return image.resize((1024, 576))

    def _generate_sync(self, image: Image.Image) -> str:
        import imageio.v2 as imageio
        import torch

        pipeline = self._get_pipeline()
        generator = torch.manual_seed(42)
        frames = pipeline(
            image,
            decode_chunk_size=settings.SVD_DECODE_CHUNK_SIZE,
            generator=generator,
            num_frames=settings.SVD_NUM_FRAMES,
        ).frames[0]

        filename = f"{uuid4()}.mp4"
        output_path = self.output_dir / filename
        imageio.mimsave(output_path, frames, fps=settings.SVD_FPS)
        return self._build_public_video_url(filename)

    def _build_public_video_url(self, filename: str) -> str:
        return f"{settings.PUBLIC_BASE_URL.rstrip('/')}/generated/{filename}"

    async def generate_video(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        duration: int = 5,
    ) -> Tuple[str, str]:
        del prompt, duration

        if not image_url:
            raise ValueError("image_url is required for the free SVD image-to-video provider")

        try:
            image = await self._download_image(image_url)
            video_url = await asyncio.to_thread(self._generate_sync, image)
            return video_url, video_url
        except Exception:
            logger.exception("Error generating video with Stable Video Diffusion")
            raise

    async def get_status(self, job_id: str) -> dict:
        return build_status_payload(job_id, "completed", video_url=job_id, progress=100)


class VideoGenerationService:
    def __init__(self, provider: VideoProvider = VideoProvider.SVD):
        if provider != VideoProvider.SVD:
            raise ValueError(f"Unknown provider: {provider}")
        self.service = StableVideoDiffusionService()

    async def generate(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        duration: int = 5,
    ) -> Tuple[str, str]:
        return await self.service.generate_video(prompt, image_url, duration)

    async def get_status(self, job_id: str) -> dict:
        return await self.service.get_status(job_id)
