import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_authenticated_username, get_owned_job
from backend.app.api.schemas import (
    JobInfoResponse,
    JobListItemResponse,
    StatusResponse,
    VideoGenerationRequest,
    VideoGenerationResponse,
)
from backend.app.core.auth import TokenData, get_current_user
from backend.app.config import settings
from backend.app.db.models import VideoJobModel
from backend.app.db.session import get_db
from backend.app.services.video_service import VideoGenerationService, VideoProvider

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Generation"])
PROVIDER_SUMMARIES = [
    {
        "name": "Stable Video Diffusion",
        "id": "svd",
        "model": settings.SVD_MODEL_ID,
        "max_duration": settings.MAX_VIDEO_DURATION,
        "quality": "good",
        "speed": "local_gpu",
        "description": "Free open-weight image-to-video model running locally through Diffusers",
    }
]


def serialize_job(job: VideoJobModel) -> JobInfoResponse:
    return JobInfoResponse(
        job_id=job.job_id,
        username=job.username,
        provider=job.provider,
        prompt=job.prompt,
        duration=job.duration,
        status=job.status,
        image_url=job.image_url,
        video_url=job.video_url,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def serialize_job_list_item(job: VideoJobModel) -> JobListItemResponse:
    return JobListItemResponse(
        job_id=job.job_id,
        provider=job.provider,
        prompt=job.prompt,
        status=job.status,
        duration=job.duration,
        created_at=job.created_at,
        updated_at=job.updated_at,
        video_url=job.video_url,
    )


def build_generation_response(job_id: str, provider: VideoProvider, video_url: str | None) -> VideoGenerationResponse:
    status = "completed" if provider == VideoProvider.SVD else "pending"
    message = f"Video generation completed using {provider.value}."
    return VideoGenerationResponse(
        job_id=job_id,
        status=status,
        provider=provider.value,
        video_url=video_url,
        message=message,
    )


def create_video_job_record(
    *,
    job_id: str,
    username: str,
    request: VideoGenerationRequest,
    provider_job_id: str,
    duration: int,
) -> VideoJobModel:
    is_local_provider = request.provider == VideoProvider.SVD
    return VideoJobModel(
        job_id=job_id,
        username=username,
        prompt=request.prompt,
        image_url=request.image_url,
        provider=request.provider.value,
        duration=str(duration),
        status="completed" if is_local_provider else "pending",
        video_url=provider_job_id if is_local_provider else None,
        provider_job_id=provider_job_id,
    )


@router.get("/api/v1/providers", tags=["Info"])
async def list_providers():
    return {
        "available_providers": PROVIDER_SUMMARIES,
        "default": settings.DEFAULT_VIDEO_PROVIDER,
    }


@router.post("/api/v1/generate", response_model=VideoGenerationResponse)
async def generate_video(
    request: VideoGenerationRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    job_id = str(uuid.uuid4())
    username = get_authenticated_username(current_user, db)

    try:
        duration = min(request.duration, settings.MAX_VIDEO_DURATION)
        video_service = VideoGenerationService(provider=request.provider)
        generated_job_id, _status_url = await video_service.generate(
            prompt=request.prompt,
            image_url=request.image_url,
            duration=duration,
        )

        video_job = create_video_job_record(
            job_id=job_id,
            username=username,
            request=request,
            provider_job_id=generated_job_id,
            duration=duration,
        )
        db.add(video_job)
        db.commit()
        db.refresh(video_job)

        return build_generation_response(job_id, request.provider, video_job.video_url)
    except ValueError as exc:
        logger.error("[%s] Validation error: %s", job_id, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("[%s] Error generating video: %s", job_id, exc)
        raise HTTPException(status_code=500, detail=f"Video generation failed: {exc}") from exc


@router.get("/api/v1/status/{job_id}", response_model=StatusResponse, tags=["Status"])
async def check_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    try:
        username = get_authenticated_username(current_user, db)
        job = get_owned_job(db, job_id, username)
        provider = VideoProvider(job.provider)
        video_service = VideoGenerationService(provider=provider)
        provider_status = await video_service.get_status(job.provider_job_id)

        job.status = provider_status["status"]
        job.video_url = provider_status.get("video_url")
        db.commit()

        return StatusResponse(
            job_id=job_id,
            status=provider_status["status"],
            provider=provider.value,
            video_url=provider_status.get("video_url"),
            progress=provider_status.get("progress", 0),
            error=provider_status.get("error"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error checking status for %s: %s", job_id, exc)
        raise HTTPException(status_code=500, detail=f"Failed to check status: {exc}") from exc


@router.get("/api/v1/job/{job_id}", response_model=JobInfoResponse, tags=["Job Info"])
async def get_job_info(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    username = get_authenticated_username(current_user, db)
    job = get_owned_job(db, job_id, username)
    return serialize_job(job)


@router.get("/api/v1/jobs", response_model=list[JobListItemResponse], tags=["Job Info"])
async def list_jobs(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    username = get_authenticated_username(current_user, db)
    safe_limit = min(max(limit, 1), 100)
    jobs = (
        db.query(VideoJobModel)
        .filter(VideoJobModel.username == username)
        .order_by(VideoJobModel.created_at.desc())
        .limit(safe_limit)
        .all()
    )
    return [serialize_job_list_item(job) for job in jobs]
