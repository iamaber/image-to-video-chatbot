from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def utcnow() -> datetime:
    # Keep naive UTC timestamps for compatibility with existing schema
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserModel(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class VideoJobModel(Base):
    __tablename__ = "video_jobs"

    job_id = Column(String, primary_key=True, index=True)
    username = Column(String, index=True)
    prompt = Column(String)
    image_url = Column(String, nullable=True)
    provider = Column(String)
    duration = Column(String)
    status = Column(String, default="pending")
    video_url = Column(String, nullable=True)
    provider_job_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
