"""
Dashboard and analytics endpoints for finance tracker app.

Endpoints:
    - /dashboard/recent-transactions: latest N transactions
    - /dashboard/summary: income/expense totals, weekly/monthly aggregates
    - /analytics/category-spending: spending totals per category (for charts)
    - /analytics/budget-usage: budget progress stats for current period

All endpoints are protected (require authentication).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func
from datetime import datetime

from .db import get_db
from .models import Transaction, Category, Budget, TransactionType, User
from .schemas import TransactionOut
from .auth import get_current_user

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])

@dashboard_router.get("/recent-transactions", response_model=List[TransactionOut], summary="Recent transactions")
# PUBLIC_INTERFACE
def recent_transactions(n: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Get the most recent N transactions for current user."""
    return db.query(Transaction).filter(Transaction.user_id == user.id).order_by(Transaction.timestamp.desc()).limit(n).all()

@dashboard_router.get("/summary", summary="Dashboard financial summary")
# PUBLIC_INTERFACE
def dashboard_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Get summary for dashboard: total income/expense, totals for current month.
    """
    now = datetime.utcnow()
    this_month_start = datetime(now.year, now.month, 1)
    income_total = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == TransactionType.income
    ).scalar() or 0
    expense_total = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == TransactionType.expense
    ).scalar() or 0
    month_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == TransactionType.income,
        Transaction.timestamp >= this_month_start
    ).scalar() or 0
    month_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == TransactionType.expense,
        Transaction.timestamp >= this_month_start
    ).scalar() or 0
    return {
        "income_total": income_total,
        "expense_total": expense_total,
        "month_income": month_income,
        "month_expense": month_expense
    }

@analytics_router.get("/category-spending", summary="Spending by category for chart")
# PUBLIC_INTERFACE
def category_spending(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get spending totals grouped by category, for current user, for analytics/charts.
    Optionally filtered by date range.
    """
    q = db.query(
        Category.name,
        func.sum(Transaction.amount).label("total_spent")
    ).join(Transaction, Transaction.category_id == Category.id
    ).filter(
        Transaction.user_id == user.id,
        Transaction.type == TransactionType.expense
    )
    if start_date:
        q = q.filter(Transaction.timestamp >= start_date)
    if end_date:
        q = q.filter(Transaction.timestamp <= end_date)
    q = q.group_by(Category.id)
    results = q.all()
    return [{"category": name, "total_spent": spent} for (name, spent) in results]

@analytics_router.get("/budget-usage", summary="Budget progress for current period")
# PUBLIC_INTERFACE
def budget_usage(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Get current budget progress for all budgets of current user.
    Returns actual spending vs. budget limit for current period (e.g., month).
    """
    budgets = db.query(Budget).filter(Budget.user_id == user.id).all()
    analytics = []
    for budget in budgets:
        # Only consider transactions within this budget period/category
        txn_q = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.expense,
            Transaction.timestamp >= budget.start_date
        )
        if budget.end_date:
            txn_q = txn_q.filter(Transaction.timestamp <= budget.end_date)
        if budget.category_id:
            txn_q = txn_q.filter(Transaction.category_id == budget.category_id)
        spent = txn_q.scalar() or 0
        analytics.append({
            "budget_id": budget.id,
            "category_id": budget.category_id,
            "period": budget.period,
            "limit": budget.limit,
            "start_date": budget.start_date,
            "end_date": budget.end_date,
            "spent": spent
        })
    return analytics

