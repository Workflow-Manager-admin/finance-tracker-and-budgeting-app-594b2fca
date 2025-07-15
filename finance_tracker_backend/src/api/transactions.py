"""
Endpoints for transaction CRUD and analytics: add/list/update/delete transactions for authenticated user;
summaries for dashboards and category analytics.

Routers:
    - /transactions/* (CRUD, listing, filter by type/category)
    - /categories/* (CRUD)
    - /budgets/* (CRUD)
    - /analytics/ dashboards

Relies on authentication dependency, SQLAlchemy models and pydantic schemas.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func

from .db import get_db
from .models import Transaction, Category, Budget, User
from .schemas import (
    TransactionCreate, TransactionOut,
    CategoryCreate, CategoryOut,
    BudgetCreate, BudgetOut
)
from .auth import get_current_user

transaction_router = APIRouter(prefix="/transactions", tags=["Transactions"])
category_router = APIRouter(prefix="/categories", tags=["Categories"])
budget_router = APIRouter(prefix="/budgets", tags=["Budgets"])

# TRANSACTION ROUTES

@transaction_router.post("/", response_model=TransactionOut, summary="Create a transaction")
# PUBLIC_INTERFACE
def create_transaction(
    transaction_in: TransactionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Create a new transaction for the authenticated user."""
    category = db.query(Category).filter(Category.id == transaction_in.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    txn = Transaction(
        user_id=user.id,
        category_id=transaction_in.category_id,
        amount=transaction_in.amount,
        description=transaction_in.description,
        type=transaction_in.type,
        timestamp=transaction_in.timestamp or func.now()
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn

@transaction_router.get("/", response_model=List[TransactionOut], summary="List transactions (all/my)")
# PUBLIC_INTERFACE
def list_transactions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List (paginated) transactions for current user."""
    return db.query(Transaction).filter(Transaction.user_id == user.id).order_by(Transaction.timestamp.desc()).offset(skip).limit(limit).all()

@transaction_router.get("/{transaction_id}", response_model=TransactionOut, summary="Get transaction by ID")
# PUBLIC_INTERFACE
def get_transaction(transaction_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Get a transaction by ID (must belong to current user)."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.user_id == user.id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn

@transaction_router.put("/{transaction_id}", response_model=TransactionOut, summary="Update a transaction")
# PUBLIC_INTERFACE
def update_transaction(transaction_id: int, req: TransactionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Update a transaction (must belong to current user)."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.user_id == user.id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    txn.category_id = req.category_id
    txn.amount = req.amount
    txn.description = req.description
    txn.type = req.type
    txn.timestamp = req.timestamp or txn.timestamp
    db.commit()
    db.refresh(txn)
    return txn

@transaction_router.delete("/{transaction_id}", status_code=204, summary="Delete a transaction")
# PUBLIC_INTERFACE
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Delete a transaction (must belong to current user)."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.user_id == user.id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(txn)
    db.commit()
    return

# --- CATEGORY ROUTES ---

@category_router.get("/", response_model=List[CategoryOut], summary="List all categories")
# PUBLIC_INTERFACE
def list_categories(db: Session = Depends(get_db)):
    """List all transaction categories."""
    return db.query(Category).order_by(Category.name.asc()).all()

@category_router.post("/", response_model=CategoryOut, summary="Create a new category")
# PUBLIC_INTERFACE
def create_category(category_in: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category. Name must be unique."""
    existing = db.query(Category).filter(Category.name == category_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category name already exists")
    category = Category(name=category_in.name, color=category_in.color)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

# --- BUDGET ROUTES ---

@budget_router.get("/", response_model=List[BudgetOut], summary="List budgets (my)")
# PUBLIC_INTERFACE
def list_budgets(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """List all budgets for current user."""
    return db.query(Budget).filter(Budget.user_id == user.id).order_by(Budget.start_date.desc()).all()

@budget_router.post("/", response_model=BudgetOut, summary="Create a new budget")
# PUBLIC_INTERFACE
def create_budget(budget_in: BudgetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Create a new budget for current user."""
    # Validate category if provided
    if budget_in.category_id is not None:
        category = db.query(Category).filter(Category.id == budget_in.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    budget = Budget(
        user_id=user.id,
        category_id=budget_in.category_id,
        limit=budget_in.limit,
        period=budget_in.period,
        start_date=budget_in.start_date,
        end_date=budget_in.end_date
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget

@budget_router.delete("/{budget_id}", status_code=204, summary="Delete a budget")
# PUBLIC_INTERFACE
def delete_budget(budget_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Delete a budget (must belong to current user)."""
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()
    return

@budget_router.get("/{budget_id}", response_model=BudgetOut, summary="Get budget by ID")
# PUBLIC_INTERFACE
def get_budget(budget_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Get a budget by ID (must belong to current user)."""
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget

@budget_router.put("/{budget_id}", response_model=BudgetOut, summary="Update a budget")
# PUBLIC_INTERFACE
def update_budget(budget_id: int, req: BudgetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Update a budget (must belong to current user)."""
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user.id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    budget.category_id = req.category_id
    budget.limit = req.limit
    budget.period = req.period
    budget.start_date = req.start_date
    budget.end_date = req.end_date
    db.commit()
    db.refresh(budget)
    return budget

