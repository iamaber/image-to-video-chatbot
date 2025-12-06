# Database configuration and models
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings

# Create database engine with Neon DB support
# Neon requires SSL, pool settings for serverless
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# ==================== Database Models ====================

class UserModel(Base):
    # User database model
    __tablename__ = "users"
    
    username = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoJobModel(Base):
    # Video generation job tracking
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create all tables
Base.metadata.create_all(bind=engine)


# ==================== Dependency Functions ====================

def get_db():
    # Get database session
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
