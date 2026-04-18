import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.jobs import router as jobs_router
from backend.app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if settings.SECRET_KEY == "change-me-in-.env":
    logger.warning("Using placeholder SECRET_KEY. Set SECRET_KEY in .env before deployment.")

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Image-to-Video Generation Chatbot",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(jobs_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Image-to-Video Generation Chatbot",
        "version": settings.API_VERSION,
        "status": "active",
        "endpoints": {
            "generate": "POST /api/v1/generate",
            "status": "GET /api/v1/status/{job_id}",
            "providers": "GET /api/v1/providers",
            "docs": "/docs",
        },
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error("HTTP Exception: %s", exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )
