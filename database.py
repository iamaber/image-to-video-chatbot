# User database operations with PostgreSQL
from sqlalchemy.orm import Session
from auth import UserInDB, get_password_hash
from db import UserModel


def create_user(db: Session, username: str, email: str, password: str, full_name: str = None) -> UserModel:
    # Create a new user and store in PostgreSQL database
    hashed_password = get_password_hash(password)
    user = UserModel(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, username: str) -> UserModel | None:
    # Get user from PostgreSQL database by username
    return db.query(UserModel).filter(UserModel.username == username).first()


def user_exists(db: Session, username: str) -> bool:
    # Check if user already exists in database
    return db.query(UserModel).filter(UserModel.username == username).first() is not None


def get_user_by_email(db: Session, email: str) -> UserModel | None:
    # Get user from database by email
    return db.query(UserModel).filter(UserModel.email == email).first()

