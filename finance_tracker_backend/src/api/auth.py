"""
Auth endpoints: User registration, login, JWT-based authentication for finance tracker app.

Implements secure password hashing (passlib), JWT access token handling, and authentication dependencies.

Routers:
    - /auth/register (POST): Register a new user
    - /auth/login (POST): Login and receive JWT access token

Depends on models and schemas in models.py and schemas.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .db import get_db
from .models import User
from .schemas import UserCreate, UserOut

import os

SECRET_KEY = os.environ.get("SECRET_KEY", "devsecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Password helpers
def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def hash_password(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# PUBLIC_INTERFACE
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

@auth_router.post("/register", response_model=UserOut, summary="Register a new user")
# PUBLIC_INTERFACE
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (must have unique email)."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists with this email")
    hashed_pw = hash_password(user_in.password)
    user = User(email=user_in.email, full_name=user_in.full_name, hashed_password=hashed_pw)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@auth_router.post("/login", summary="Login and get JWT token")
# PUBLIC_INTERFACE
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return JWT access token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "created_at": user.created_at}}

