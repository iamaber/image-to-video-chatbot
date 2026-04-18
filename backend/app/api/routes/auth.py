import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.api.deps import issue_access_token
from backend.app.core.auth import Token, TokenData, User, UserLogin, UserRegister, get_current_user
from backend.app.db.session import get_db
from backend.app.repositories.users import create_user, get_user, user_exists

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])


@router.post("/auth/register", response_model=User)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    if user_exists(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    user = create_user(
        db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
    )
    logger.info("New user registered: %s", user_data.username)
    return User(username=user.username, email=user.email, full_name=user.full_name)


@router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    return issue_access_token(user_data.username, user_data.password, db)


@router.post("/auth/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return issue_access_token(form_data.username, form_data.password, db)


@router.get("/auth/me", response_model=User)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = get_user(db, current_user.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return User(username=user.username, email=user.email, full_name=user.full_name)
