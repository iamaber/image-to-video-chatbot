# Authentication module with JWT support
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Secret key and algorithm for JWT
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"


# ==================== Data Models ====================

class Token(BaseModel):
    # JWT token response
    access_token: str
    token_type: str


class TokenData(BaseModel):
    # Token payload data
    username: Optional[str] = None


class User(BaseModel):
    # User data model
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None


class UserInDB(User):
    # User in database with hashed password
    hashed_password: str


class UserRegister(BaseModel):
    # User registration request
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    # User login request
    username: str
    password: str


# ==================== Helper Functions ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verify plain password against hashed password
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    # Hash a plain password
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # Create JWT access token
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    # Get current user from JWT token
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
        token_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    
    return token_data
