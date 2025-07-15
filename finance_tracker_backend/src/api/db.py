"""
Database, SQLAlchemy session, and models for Finance Tracker.
Handles SQLite engine/config (env-controlled), session context, and ORM models for users/transactions.

Environment variables required:
  - DB_URL (default: sqlite:///./finance_tracker.db if not set)
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.engine import Engine

DB_URL = os.getenv("DB_URL") or "sqlite:///./finance_tracker.db"

engine: Engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Session getter for dependency injection
# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """Yields a database session for a FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SQLAlchemy ORM Models ---

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
import datetime

class User(Base):
    """User entity for authentication"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    transactions = relationship("Transaction", back_populates="owner", cascade="all, delete-orphan")

class Transaction(Base):
    """Spending/income transaction entity"""
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(String(500))
    date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    type = Column(String(50), nullable=False)  # e.g., "income" or "expense"
    owner = relationship("User", back_populates="transactions")
