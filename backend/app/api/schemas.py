from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.app.services.video_service import VideoProvider


class VideoGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=500, description="Description of the video to generate")
    image_url: Optional[str] = Field(None, description="Image URL used as the source frame")
    provider: VideoProvider = Field(default=VideoProvider.SVD, description="Video provider")
    duration: int = Field(default=5, ge=1, le=30, description="Video duration in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt": "A beautiful sunset over mountains with golden light, camera pans left",
                "image_url": "https://example.com/source-image.png",
                "provider": "svd",
                "duration": 5,
            }
        }
    )


class VideoGenerationResponse(BaseModel):
    job_id: str = Field(..., description="Unique job ID for tracking")
    status: str = Field(..., description="Status of the generation (pending, processing, completed, failed)")
    provider: str = Field(..., description="Video generation provider used")
    video_url: Optional[str] = Field(None, description="URL to the generated video (when completed)")
    message: str = Field(..., description="Status message")


class StatusResponse(BaseModel):
    job_id: str
    status: str
    provider: str
    video_url: Optional[str] = None
    progress: int = 0
    error: Optional[str] = None


class JobInfoResponse(BaseModel):
    job_id: str
    username: str
    provider: str
    prompt: str
    duration: str
    status: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class JobListItemResponse(BaseModel):
    job_id: str
    provider: str
    prompt: str
    status: str
    duration: str
    created_at: datetime
    updated_at: datetime
    video_url: Optional[str] = None
