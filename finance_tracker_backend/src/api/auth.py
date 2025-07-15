"""
Authentication endpoints and helpers for Finance Tracker:
- Register new user
- Login (JWT issuance)
- Dependency for JWT-protected routes
- Password hashing & JWT identity
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional

from src.api.db import get_db, User

import os

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=64, description="Password")

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")

class Token(BaseModel):
    access_token: str
    token_type: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Hash helpers
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# PUBLIC_INTERFACE
def get_current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)):
    """
    Dependency for JWT-protected endpoints.
    Returns current user or raises HTTPException.
    """
    from fastapi.security import OAuth2PasswordBearer
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
    _token = token or oauth2_scheme()
    try:
        payload = jwt.decode(_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid JWT subject")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid or expired")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# PUBLIC_INTERFACE
@router.post("/register", response_model=Token, summary="Register a new user", description="Registers a new user and returns JWT token.")
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a user if email is unique and return JWT token."""
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    u = User(email=user.email, hashed_password=get_password_hash(user.password))
    db.add(u)
    db.commit()
    db.refresh(u)
    token = create_access_token({"sub": u.id})
    return Token(access_token=token, token_type="bearer")

# PUBLIC_INTERFACE
@router.post("/login", response_model=Token, summary="Login and obtain JWT", description="User login. Returns JWT token on success.")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and issue JWT on success."""
    u = db.query(User).filter(User.email == user.email).first()
    if u is None or not verify_password(user.password, u.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": u.id})
    return Token(access_token=token, token_type="bearer")
