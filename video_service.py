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
    
    BASE_URL = "https://api.runwayml.com/v1"
    
    def __init__(self):
        self.api_key = settings.RUNWAY_API_KEY
        if not self.api_key:
            raise ValueError("RUNWAY_API_KEY not configured in environment")
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
        # Generate video using Runway
        # Args: prompt (Video description), image_url (Optional), duration (seconds, max 30)
        # Returns: Tuple of (job_id, status_url)
        try:
            payload = {
                "text": prompt,
                "duration": min(duration, 30),
                "model": "gen3"  # Runway Gen-3 model
            }
            
            if image_url:
                payload["image_url"] = image_url
            
            logger.info(f"Submitting video generation to Runway: {prompt[:80]}...")
            
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{self.BASE_URL}/generate",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"Runway API error: {response.status_code} - {response.text}")
                    raise Exception(f"Runway API error: {response.status_code}")
                
                data = response.json()
                job_id = data.get("id")
                status_url = data.get("taskId") or data.get("id")
                
                logger.info(f"Video generation started. Job ID: {job_id}")
                
                return job_id, status_url
                
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
                
                if response.status_code != 200:
                    logger.error(f"Status check failed: {response.status_code}")
                    raise Exception("Failed to get job status")
                
                data = response.json()
                return {
                    "job_id": job_id,
                    "status": data.get("status"),
                    "video_url": data.get("output", [None])[0] if data.get("output") else None,
                    "progress": data.get("progress", 0),
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
