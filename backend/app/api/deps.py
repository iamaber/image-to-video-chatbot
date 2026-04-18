from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.core.auth import Token, TokenData, create_access_token, verify_password
from backend.app.db.models import VideoJobModel
from backend.app.repositories.users import get_user


def issue_access_token(username: str, password: str, db: Session) -> Token:
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS),
    )
    return Token(access_token=access_token, token_type="bearer")


def get_authenticated_username(current_user: TokenData, db: Session) -> str:
    user = get_user(db, current_user.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user.username


def get_owned_job(db: Session, job_id: str, username: str) -> VideoJobModel:
    job = (
        db.query(VideoJobModel)
        .filter(VideoJobModel.job_id == job_id, VideoJobModel.username == username)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
