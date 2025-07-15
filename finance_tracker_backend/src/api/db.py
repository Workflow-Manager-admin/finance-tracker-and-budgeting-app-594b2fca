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
def test_db_connection():
    """
    Simple test for DB connectivity:
    - For SQLite: checks file existence and write access.
    - For other engines: tries to connect and run SELECT 1.

    Returns:
        dict: { "ok": bool, "error": str|None }
    """
    from sqlalchemy.exc import OperationalError
    import os
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite:///"):
        # Relative or absolute path
        db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "", 1)
        try:
            # Test existence
            exists = os.path.isfile(db_path)
            # Test writability
            writable = os.access(db_path, os.W_OK) if exists else os.access(os.path.dirname(db_path) or ".", os.W_OK)
            return {
                "ok": exists and writable,
                "error": None if exists and writable else (
                    "DB file does not exist" if not exists else "DB file is not writable"
                )
            }
        except Exception as ex:
            return {"ok": False, "error": f"File check failed: {ex}"}
    else:
        # Try connecting and running a trivial query
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return {"ok": True, "error": None}
        except OperationalError as oe:
            return {"ok": False, "error": f"OperationalError: {oe}"}
        except Exception as ex:
            return {"ok": False, "error": f"Error: {ex}"}

# PUBLIC_INTERFACE
def get_db() -> Generator:
    """Dependency that provides a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
