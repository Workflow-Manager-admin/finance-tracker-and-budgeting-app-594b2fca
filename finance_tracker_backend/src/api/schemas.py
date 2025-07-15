"""
Pydantic schemas for finance tracker models (request, response, and validation).

Defines: Base & CRUD schemas for User, Transaction, Budget, Category.

# PUBLIC_INTERFACE
Exposes all public Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
import enum

# --- ENUMS (match model enums for type safety) ---
# PUBLIC_INTERFACE
class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"

# --- CATEGORY ---
class CategoryBase(BaseModel):
    name: str = Field(..., description="Name of the category.")
    color: Optional[str] = Field(None, description="Color for UI (hex/rgb etc).")

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int

    class Config:
        from_attributes = True

# --- BUDGET ---
class BudgetBase(BaseModel):
    limit: float = Field(..., description="Spending/income limit for the period.")
    period: str = Field(..., description="Budgeting period (e.g., monthly, weekly).")
    start_date: datetime = Field(..., description="Budget start date/time.")
    end_date: Optional[datetime] = Field(None, description="Budget end date/time.")
    category_id: Optional[int] = Field(None, description="Associated category (null = general budget).")

class BudgetCreate(BudgetBase):
    pass

class BudgetOut(BudgetBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# --- TRANSACTION ---
class TransactionBase(BaseModel):
    amount: float = Field(..., description="Monetary amount (positive = income, negative = expense).")
    description: Optional[str] = Field(None, description="Optional details about transaction.")
    timestamp: Optional[datetime] = Field(None, description="When the transaction occurred (default now).")
    type: TransactionType = Field(..., description="Transaction type: income or expense.")
    category_id: int = Field(..., description="Category id for this transaction.")

class TransactionCreate(TransactionBase):
    pass

class TransactionOut(TransactionBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# --- USER ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(None, description="Full (display) name.")

class UserCreate(UserBase):
    password: str = Field(..., description="User's password (plain-text, to be hashed).")

class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- COMPLEX/NESTED SCHEMAS ---
class UserWithTransactions(UserOut):
    transactions: List[TransactionOut] = []
    budgets: List[BudgetOut] = []

class CategoryWithTransactions(CategoryOut):
    transactions: List[TransactionOut] = []

class BudgetWithCategory(BudgetOut):
    category: Optional[CategoryOut] = None

# --- Alembic migration support ---
# TODO: Add Alembic-aware versioned schemas for database migrations.
