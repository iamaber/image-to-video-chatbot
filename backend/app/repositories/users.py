from typing import Optional

from sqlalchemy.orm import Session

from backend.app.core.auth import get_password_hash
from backend.app.db.models import UserModel


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    full_name: str = None,
) -> UserModel:
    hashed_password = get_password_hash(password)
    user = UserModel(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, username: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.username == username).first()


def user_exists(db: Session, username: str) -> bool:
    return db.query(UserModel).filter(UserModel.username == username).first() is not None


def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.email == email).first()
