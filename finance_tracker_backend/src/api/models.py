"""
SQLAlchemy ORM Models for the finance tracker app.

Defines: User, Transaction, Budget, Category and their relationships.

# PUBLIC_INTERFACE
Exposes all ORM model classes for use in CRUD/database operations.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .db import Base

class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"

# PUBLIC_INTERFACE
class User(Base):
    """User entity (for authentication; users have many transactions and budgets)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")

# PUBLIC_INTERFACE
class Category(Base):
    """Spending/income category for transactions (e.g., Food, Rent, Salary)."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    color = Column(String, nullable=True)  # Optional for UI

    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")

# PUBLIC_INTERFACE
class Budget(Base):
    """
    Budget entity — tracked for a user, optionally associated with a category.
    If category_id is null, it's a general budget for the user.
    """
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    limit = Column(Float, nullable=False)
    period = Column(String, nullable=False, default="monthly")  # Could be monthly/weekly/etc.
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")

# PUBLIC_INTERFACE
class Transaction(Base):
    """Transaction record (belongs to user and category)."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    type = Column(Enum(TransactionType), nullable=False)

    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

# --- Alembic migration support ---
# TODO: Add Alembic revision scripts for migrations.
