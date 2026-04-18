from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.config import settings


def create_db_engine(database_url: str):
    # Build engine for Postgres in prod and SQLite in tests/local dev
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
        )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
        },
    )


engine = create_db_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
