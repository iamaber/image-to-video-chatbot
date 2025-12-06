# FastAPI backend for image-to-video generation chatbot

from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import logging
import uuid
from datetime import timedelta
from sqlalchemy.orm import Session

from config import settings
from video_service import VideoGenerationService, VideoProvider
from auth import (
    Token, TokenData, User, UserRegister, UserLogin,
    get_current_user, create_access_token, verify_password
)
from database import create_user, get_user, user_exists
from db import get_db, VideoJobModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Image-to-Video Generation Chatbot"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Data Models ====================

class VideoGenerationRequest(BaseModel):
    # User request for video generation
    prompt: str = Field(..., min_length=10, max_length=500, description="Description of the video to generate")
    image_url: Optional[str] = Field(None, description="Optional image to use as base")
    provider: VideoProvider = Field(default=VideoProvider.RUNWAY, description="Video provider (runway or minimax)")
    duration: int = Field(default=5, ge=1, le=30, description="Video duration in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "A beautiful sunset over mountains with golden light, camera pans left",
                "provider": "runway",
                "duration": 5
            }
        }


class VideoGenerationResponse(BaseModel):
    # Response containing video generation result
    job_id: str = Field(..., description="Unique job ID for tracking")
    status: str = Field(..., description="Status of the generation (pending, processing, completed, failed)")
    provider: str = Field(..., description="Video generation provider used")
    video_url: Optional[str] = Field(None, description="URL to the generated video (when completed)")
    message: str = Field(..., description="Status message")


class StatusResponse(BaseModel):
    # Response for checking video generation status
    job_id: str
    status: str
    provider: str
    video_url: Optional[str] = None
    progress: int = 0
    error: Optional[str] = None


# ==================== In-Memory Job Tracking ====================
# In production, use a database like PostgreSQL or Redis

# ==================== In-Memory Job Tracking ====================
# Now using PostgreSQL database for job tracking


# ==================== API Routes ====================

# ==================== Authentication Routes ====================

@app.post("/auth/register", response_model=User, tags=["Authentication"])
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Register a new user
    if user_exists(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    user = create_user(
        db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    logger.info(f"New user registered: {user_data.username}")
    
    return User(
        username=user.username,
        email=user.email,
        full_name=user.full_name
    )


@app.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    # Login user and return JWT token
    user = get_user(db, user_data.username)
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in: {user_data.username}")
    
    return Token(access_token=access_token, token_type="bearer")


@app.get("/auth/me", response_model=User, tags=["Authentication"])
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get current user information
    user = get_user(db, current_user.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return User(
        username=user.username,
        email=user.email,
        full_name=user.full_name
    )


# ==================== Video Generation Routes ====================

@app.get("/", tags=["Health"])
async def root():
    # Health check endpoint
    return {
        "service": "Image-to-Video Generation Chatbot",
        "version": settings.API_VERSION,
        "status": "active",
        "endpoints": {
            "generate": "POST /api/v1/generate",
            "status": "GET /api/v1/status/{job_id}",
            "providers": "GET /api/v1/providers",
            "docs": "/docs"
        }
    }


@app.get("/api/v1/providers", tags=["Info"])
async def list_providers():
    # List available video generation providers
    return {
        "available_providers": [
            {
                "name": "Runway",
                "id": "runway",
                "model": "Gen-3",
                "max_duration": 30,
                "quality": "very_high",
                "speed": "medium",
                "description": "State-of-the-art video generation with exceptional quality"
            },
            {
                "name": "Minimax",
                "id": "minimax",
                "model": "Video-01",
                "max_duration": 30,
                "quality": "high",
                "speed": "fast",
                "description": "Fast and consistent video generation"
            }
        ],
        "default": settings.DEFAULT_VIDEO_PROVIDER
    }


@app.post("/api/v1/generate", response_model=VideoGenerationResponse, tags=["Generation"])
async def generate_video(
    request: VideoGenerationRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Generate video from user prompt (requires authentication)
    # Steps: Generate video using selected provider (Runway/Minimax)
    # Return job ID for status tracking
    job_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{job_id}] Video generation request from user: {current_user.username}")
        
        # Use the duration from request
        duration = min(request.duration, settings.MAX_VIDEO_DURATION)
        
        # Initialize video generation service
        video_service = VideoGenerationService(provider=request.provider)
        
        # Submit video generation request
        logger.info(f"[{job_id}] Submitting to {request.provider.value} for video generation...")
        
        generated_job_id, status_url = await video_service.generate(
            prompt=request.prompt,
            image_url=request.image_url,
            duration=duration
        )
        
        # Store job info in PostgreSQL database
        video_job = VideoJobModel(
            job_id=job_id,
            username=current_user.username,
            prompt=request.prompt,
            image_url=request.image_url,
            provider=request.provider.value,
            duration=str(duration),
            status="pending",
            provider_job_id=generated_job_id
        )
        db.add(video_job)
        db.commit()
        db.refresh(video_job)
        
        logger.info(f"[{job_id}] Video generation initiated successfully")
        
        return VideoGenerationResponse(
            job_id=job_id,
            status="pending",
            provider=request.provider.value,
            message=f"Video generation started using {request.provider.value}. Provider Job ID: {generated_job_id}"
        )
        
    except ValueError as e:
        logger.error(f"[{job_id}] Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[{job_id}] Error generating video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@app.get("/api/v1/status/{job_id}", response_model=StatusResponse, tags=["Status"])
async def check_status(job_id: str, db: Session = Depends(get_db)):
    # Check status of a video generation job
    # Status values: pending, processing, completed, failed
    try:
        # Get job from database
        job = db.query(VideoJobModel).filter(VideoJobModel.job_id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        provider = VideoProvider(job.provider)
        provider_job_id = job.provider_job_id
        
        # Get status from the video provider
        video_service = VideoGenerationService(provider=provider)
        provider_status = await video_service.get_status(provider_job_id)
        
        # Update job status in database
        job.status = provider_status["status"]
        job.video_url = provider_status.get("video_url")
        db.commit()
        
        return StatusResponse(
            job_id=job_id,
            status=provider_status["status"],
            provider=provider.value,
            video_url=provider_status.get("video_url"),
            progress=provider_status.get("progress", 0),
            error=provider_status.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking status for {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check status: {str(e)}")


@app.get("/api/v1/job/{job_id}", tags=["Job Info"])
async def get_job_info(job_id: str, db: Session = Depends(get_db)):
    # Get detailed information about a video generation job
    job = db.query(VideoJobModel).filter(VideoJobModel.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "username": job.username,
        "provider": job.provider,
        "prompt": job.prompt,
        "duration": job.duration,
        "status": job.status,
        "image_url": job.image_url,
        "video_url": job.video_url,
        "created_at": job.created_at,
        "updated_at": job.updated_at
    }


# ==================== Lifecycle Events ====================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("🚀 Image-to-Video Chatbot API Starting")
    logger.info(f"   Provider: {settings.DEFAULT_VIDEO_PROVIDER.upper()}")
    logger.info(f"   LLM Model: {settings.LLM_MODEL}")
    logger.info(f"   API: http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"   Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Chatbot API shut down")


# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    # Handle HTTP exceptions
    logger.error(f"HTTP Exception: {exc.detail}")
    return {"error": exc.detail, "status_code": exc.status_code}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
