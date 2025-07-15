from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date

# PUBLIC_INTERFACE
class UserBase(BaseModel):
    """
    Base model for user with email field.
    """
    email: EmailStr = Field(..., description="Unique user email")

# PUBLIC_INTERFACE
class UserCreate(UserBase):
    """
    Model for creating a new user.
    """
    password: str = Field(..., min_length=6, description="User password")

# PUBLIC_INTERFACE
class UserLogin(UserBase):
    """
    Model for user login.
    """
    password: str = Field(..., description="User password for login")

# PUBLIC_INTERFACE
class UserOut(UserBase):
    """
    Model for returning user info to client.
    """
    id: int

    model_config = {
        "from_attributes": True
    }

# PUBLIC_INTERFACE
class Token(BaseModel):
    """
    Authentication token response model.
    """
    access_token: str
    token_type: str

# PUBLIC_INTERFACE
class TransactionBase(BaseModel):
    """
    Base transaction model with required fields.
    """
    amount: float = Field(description="Amount of the transaction")
    category: str = Field(description="Spending category")
    type: str = Field(description="Transaction type: income/expense")
    date: date = Field(description="Date of transaction")
    description: Optional[str] = Field(default=None, description="Optional transaction description")

# PUBLIC_INTERFACE
class TransactionCreate(TransactionBase):
    """
    Model for creating a transaction.
    """
    pass

# PUBLIC_INTERFACE
class TransactionUpdate(BaseModel):
    """
    Model for updating an existing transaction.
    All fields optional.
    """
    amount: Optional[float] = None
    category: Optional[str] = None
    type: Optional[str] = None
    date: Optional[date] = None
    description: Optional[str] = None

# PUBLIC_INTERFACE
class TransactionOut(TransactionBase):
    """
    Output model for transactions, used in responses.
    """
    id: int
    user_id: int

    model_config = {
        "from_attributes": True
    }

# PUBLIC_INTERFACE
class BudgetAnalytics(BaseModel):
    """
    Model for analytics of a budget category.
    """
    category: str
    total_spent: float
    budget: Optional[float] = None
    percent_of_budget: Optional[float] = None

# PUBLIC_INTERFACE
class DashboardStats(BaseModel):
    """
    Overall dashboard stats.
    """
    total_income: float
    total_expense: float
    recent_transactions: List[TransactionOut]

