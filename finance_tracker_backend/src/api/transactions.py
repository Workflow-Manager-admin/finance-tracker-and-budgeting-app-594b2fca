"""
Transaction and analytics API endpoints for Finance Tracker.
Exposes CRUD for transactions and simple budget analytics for the user.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from src.api.db import get_db, Transaction
from src.api.auth import get_current_user

router = APIRouter()

class TransactionBase(BaseModel):
    amount: float = Field(..., description="Transaction amount (positive for income, negative for expenses)")
    category: str = Field(..., description="Spending/income category")
    description: Optional[str] = Field("", description="Description/note")
    date: datetime = Field(default_factory=datetime.utcnow, description="Date of transaction")
    type: str = Field(..., description="Type: income or expense")

class TransactionCreate(TransactionBase):
    pass

class TransactionOut(TransactionBase):
    id: int

# PUBLIC_INTERFACE
@router.get("/", response_model=List[TransactionOut], summary="Get user transactions", description="Returns all transactions for current user.")
def get_transactions(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Transaction).filter(Transaction.user_id == user.id).order_by(Transaction.date.desc()).all()

# PUBLIC_INTERFACE
@router.post("/", response_model=TransactionOut, summary="Create new transaction", description="Add a new transaction for current user.")
def create_transaction(txn: TransactionCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    obj = Transaction(
        user_id=user.id,
        amount=txn.amount,
        category=txn.category,
        description=txn.description,
        date=txn.date,
        type=txn.type
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# PUBLIC_INTERFACE
@router.delete("/{txn_id}", summary="Delete a transaction", description="Delete by transaction id")
def delete_transaction(txn_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    obj = db.query(Transaction).filter(Transaction.id == txn_id, Transaction.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(obj)
    db.commit()
    return {"success": True}

# PUBLIC_INTERFACE
@router.put("/{txn_id}", response_model=TransactionOut, summary="Update transaction", description="Update an existing transaction.")
def update_transaction(txn_id: int, txn: TransactionCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    obj = db.query(Transaction).filter(Transaction.id == txn_id, Transaction.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Transaction not found")
    obj.amount = txn.amount
    obj.category = txn.category
    obj.description = txn.description
    obj.date = txn.date
    obj.type = txn.type
    db.commit()
    db.refresh(obj)
    return obj

# PUBLIC_INTERFACE
@router.get("/analytics/summary", summary="Budget analytics summary", description="Return total income, expenses and per-category stats for current user.")
def analytics_summary(db: Session = Depends(get_db), user=Depends(get_current_user)):
    total_income = sum([t.amount for t in db.query(Transaction).filter(Transaction.user_id == user.id, Transaction.type == "income").all()])
    total_expense = sum([t.amount for t in db.query(Transaction).filter(Transaction.user_id == user.id, Transaction.type == "expense").all()])
    # Per-category breakdown
    cat_stats = {}
    for t in db.query(Transaction).filter(Transaction.user_id == user.id).all():
        cat_stats.setdefault(t.category, 0)
        cat_stats[t.category] += t.amount
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "per_category": cat_stats
    }
