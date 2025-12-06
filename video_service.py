# Video generation service integrations for Runway and Minimax
import httpx
import json
import logging
from typing import Optional, Tuple
from config import settings
from enum import Enum

logger = logging.getLogger(__name__)


class VideoProvider(str, Enum):
    # Available video generation providers
    RUNWAY = "runway"
    MINIMAX = "minimax"


class RunwayService:
    # Service for generating videos using Runway API
    
    BASE_URL = "https://api.dev.runwayml.com/v1"
    API_VERSION = "2024-11-06"
    
    def __init__(self):
        self.api_key = settings.RUNWAY_API_KEY
        if not self.api_key:
            raise ValueError("RUNWAY_API_KEY not configured in environment")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": self.API_VERSION
        }
    
    async def generate_video(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        duration: int = 5
    ) -> Tuple[str, str]:
        # Generate video using Runway text-to-video API
        # Args: prompt (Video description), image_url (Optional, unused), duration (4, 6, or 8 seconds)
        # Returns: Tuple of (job_id, job_id)
        try:
            # Runway supports durations of 4, 6, or 8 seconds only
            valid_durations = [4, 6, 8]
            closest_duration = min(valid_durations, key=lambda x: abs(x - duration))
            
            payload = {
                "model": "veo3.1",
                "promptText": prompt,
                "ratio": "1280:720",
                "duration": closest_duration
            }
            
            logger.info(f"Submitting video generation to Runway: {prompt[:80]}...")
            logger.debug(f"Payload: {payload}")
            
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{self.BASE_URL}/text_to_video",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code not in [200, 201]:
                    error_detail = response.text
                    logger.error(f"Runway API error: {response.status_code} - {error_detail}")
                    raise Exception(f"Runway API error: {response.status_code} - {error_detail}")
                
                data = response.json()
                job_id = data.get("id")
                
                if not job_id:
                    logger.error(f"No job ID in response: {data}")
                    raise Exception("No job ID returned from Runway API")
                
                logger.info(f"Video generation started. Job ID: {job_id}")
                
                return job_id, job_id
                
        except Exception as e:
            logger.error(f"Error generating video with Runway: {str(e)}")
            raise
    
    async def get_status(self, job_id: str) -> dict:
        # Check status of a video generation job
        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.get(
                    f"{self.BASE_URL}/tasks/{job_id}",
                    headers=self.headers
                )
                
                if response.status_code == 404:
                    logger.error(f"Job not found: {job_id}")
                    return {
                        "job_id": job_id,
                        "status": "failed",
                        "video_url": None,
                        "progress": 0,
                        "error": "Job not found"
                    }
                
                if response.status_code != 200:
                    logger.error(f"Status check failed: {response.status_code}")
                    raise Exception("Failed to get job status")
                
                data = response.json()
                status = data.get("status", "unknown")
                
                # Runway status values: PENDING, PROCESSING, COMPLETED, FAILED
                video_url = None
                if status == "COMPLETED":
                    output = data.get("output")
                    if output:
                        video_url = output[0] if isinstance(output, list) else output
                
                return {
                    "job_id": job_id,
                    "status": status.lower(),
                    "video_url": video_url,
                    "progress": 100 if status == "COMPLETED" else 50 if status == "PROCESSING" else 0,
                    "error": data.get("error")
                }
                
        except Exception as e:
            logger.error(f"Error checking Runway status: {str(e)}")
            raise


class MinimaxService:
    # Service for generating videos using Minimax API
    
    BASE_URL = "https://api.minimax.chat/v1"
    
    def __init__(self):
        self.api_key = settings.MINIMAX_API_KEY
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY not configured in environment")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_video(
        self,
        prompt: str,
        image_url: Optional[str] = None,
        duration: int = 5
    ) -> Tuple[str, str]:
        # Generate video using Minimax
        # Args: prompt (Video description), image_url (Optional), duration (seconds, max 30)
        # Returns: Tuple of (job_id, status_url)
        try:
            payload = {
                "prompt": prompt,
                "duration": min(duration, 30),
                "model": "video-01"
            }
            
            if image_url:
                payload["image_url"] = image_url
            
            logger.info(f"Submitting video generation to Minimax: {prompt[:80]}...")
            
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{self.BASE_URL}/video/generate",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"Minimax API error: {response.status_code} - {response.text}")
                    raise Exception(f"Minimax API error: {response.status_code}")
                
                data = response.json()
                job_id = data.get("task_id")
                
                logger.info(f"Video generation started. Job ID: {job_id}")
                
                return job_id, job_id
                
        except Exception as e:
            logger.error(f"Error generating video with Minimax: {str(e)}")
            raise
    
    async def get_status(self, job_id: str) -> dict:
        # Check status of a video generation job
        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.get(
                    f"{self.BASE_URL}/video/query",
                    headers=self.headers,
                    params={"task_id": job_id}
                )
                
                if response.status_code != 200:
                    logger.error(f"Status check failed: {response.status_code}")
                    raise Exception("Failed to get job status")
                
                data = response.json()
                return {
                    "job_id": job_id,
                    "status": data.get("status"),
                    "video_url": data.get("file_id") or data.get("video_url"),
                    "progress": data.get("progress", 0),
                    "error": data.get("error")
                }
                
        except Exception as e:
            logger.error(f"Error checking Minimax status: {str(e)}")
            raise


class VideoGenerationService:
    # Factory service for video generation
    
    def __init__(self, provider: VideoProvider = VideoProvider.RUNWAY):
        self.provider = provider
        
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
        duration: int = 5
    ) -> Tuple[str, str]:
        # Generate video using the configured provider
        return await self.service.generate_video(prompt, image_url, duration)
    
    async def get_status(self, job_id: str) -> dict:
        # Get status of a video generation job
        return await self.service.get_status(job_id)
