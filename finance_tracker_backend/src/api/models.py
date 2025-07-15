from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date

# PUBLIC_INTERFACE
class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Unique user email")

# PUBLIC_INTERFACE
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="User password")

# PUBLIC_INTERFACE
class UserLogin(UserBase):
    password: str = Field(..., description="User password for login")

# PUBLIC_INTERFACE
class UserOut(UserBase):
    id: int
    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class Token(BaseModel):
    access_token: str
    token_type: str

# PUBLIC_INTERFACE
class TransactionBase(BaseModel):
    amount: float = Field(..., description="Amount of the transaction")
    category: str = Field(..., description="Spending category")
    type: str = Field(..., description="Transaction type: income/expense")
    date: date = Field(..., description="Date of transaction")
    description: Optional[str] = Field(None, description="Optional transaction description")

# PUBLIC_INTERFACE
class TransactionCreate(TransactionBase):
    pass

# PUBLIC_INTERFACE
class TransactionUpdate(BaseModel):
    amount: Optional[float]
    category: Optional[str]
    type: Optional[str]
    date: Optional[date]
    description: Optional[str]

# PUBLIC_INTERFACE
class TransactionOut(TransactionBase):
    id: int
    user_id: int
    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class BudgetAnalytics(BaseModel):
    category: str
    total_spent: float
    budget: Optional[float]
    percent_of_budget: Optional[float]

# PUBLIC_INTERFACE
class DashboardStats(BaseModel):
    total_income: float
    total_expense: float
    recent_transactions: List[TransactionOut]

