from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from backend.app.config import settings


class VideoGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=500, description="Description of the video to generate")
    image_url: HttpUrl = Field(..., description="Image URL used as the source frame")
    duration: int = Field(
        default=5,
        ge=1,
        le=settings.MAX_VIDEO_DURATION,
        description="Video duration in seconds",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt": "A beautiful sunset over mountains with golden light, camera pans left",
                "image_url": "https://example.com/source-image.png",
                "duration": 5,
            }
        }
    )


class VideoGenerationResponse(BaseModel):
    status: str = Field(..., description="Status of the generation")
    video_url: Optional[str] = Field(None, description="URL to the generated video (when completed)")
    message: str = Field(..., description="Status message")
