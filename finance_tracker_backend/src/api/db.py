"""
Database connectivity and session management for the finance tracker backend.

This module sets up the SQLAlchemy engine, session, and base for ORM usage.
It uses SQLite for local development.
Secrets/connection info should be configured using environment variables.

# PUBLIC_INTERFACE
Provides:
    - SQLALCHEMY_DATABASE_URL (from env, fallback to sqlite)
    - engine, SessionLocal, Base
    - get_db (dependency for FastAPI routes)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

# Do NOT read the dotenv/.env directly. It's loaded by process manager outside this code.
SQLALCHEMY_DATABASE_URL = os.environ.get("DB_CONNECTION_STRING", "sqlite:///./finance_tracker.db")

# If using SQLite, must set check_same_thread=False if threading used (Starlette/FastAPI/Uvicorn)
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# PUBLIC_INTERFACE
def get_db() -> Generator:
    """Dependency that provides a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
