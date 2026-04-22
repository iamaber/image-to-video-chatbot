import logging
import asyncio

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException

from backend.app.api.schemas import (
    VideoGenerationRequest,
    VideoGenerationResponse,
)
from backend.app.config import settings
from backend.app.services.video_service import VideoGenerationService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Generation"])


def validate_generate_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    if not settings.GENERATE_API_KEY:
        return

    if x_api_key != settings.GENERATE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def build_generation_response(video_url: str) -> VideoGenerationResponse:
    return VideoGenerationResponse(
        status="completed",
        video_url=video_url,
        message="Video generation completed.",
    )


@router.post("/api/v1/generate", response_model=VideoGenerationResponse)
async def generate_video(
    request: VideoGenerationRequest,
    _api_key_check: None = Depends(validate_generate_api_key),
):

    try:
        video_service = VideoGenerationService()
        video_url = await asyncio.wait_for(
            video_service.generate(
                prompt=request.prompt,
                image_url=str(request.image_url),
                duration=request.duration,
            ),
            timeout=settings.GENERATION_TIMEOUT_SECONDS,
        )

        return build_generation_response(video_url)
    except asyncio.TimeoutError as exc:
        logger.warning("Video generation timed out")
        raise HTTPException(status_code=504, detail="Video generation timed out") from exc
    except httpx.HTTPError as exc:
        logger.warning("Image download failed: %s", exc)
        raise HTTPException(
            status_code=400,
            detail="Unable to fetch source image from image_url",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error generating video: %s", exc)
        raise HTTPException(status_code=500, detail="Video generation failed") from exc
