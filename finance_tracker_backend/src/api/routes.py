from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import auth
from .database import User, Transaction, SessionLocal, get_password_hash, verify_password
from .models import (
    UserCreate, UserLogin, UserOut,
    Token, TransactionCreate, TransactionUpdate, TransactionOut,
    DashboardStats, BudgetAnalytics
)

router = APIRouter()

# ---- AUTH ROUTES ----
@router.post('/auth/register', response_model=UserOut, tags=["Authentication"], summary="Register a new user")
def register(user: UserCreate, db: Session = Depends(SessionLocal)):
    """Registers a new user."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # Always return as Pydantic model, not ORM object
    return UserOut.model_validate(new_user)

@router.post('/auth/login', response_model=Token, tags=["Authentication"], summary="Authenticate user and get JWT")
def login(user: UserLogin, db: Session = Depends(SessionLocal)):
    """Authenticate user and return JWT token."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user is None or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    access_token = auth.create_access_token(data={"sub": str(db_user.id)})
    return Token(access_token=access_token, token_type="bearer")

# ---- TRANSACTION CRUD ----
@router.post("/transactions/", response_model=TransactionOut, tags=["Transactions"], summary="Add a transaction")
def create_transaction(transaction: TransactionCreate, db: Session = Depends(SessionLocal),
                       current_user: User = Depends(auth.get_current_user)):
    """Create a new transaction for the logged-in user."""
    db_trx = Transaction(**transaction.model_dump(), user_id=current_user.id)
    db.add(db_trx)
    db.commit()
    db.refresh(db_trx)
    return TransactionOut.model_validate(db_trx)

@router.get("/transactions/", response_model=List[TransactionOut], tags=["Transactions"], summary="Get user transactions")
def list_transactions(db: Session = Depends(SessionLocal),
                      current_user: User = Depends(auth.get_current_user),
                      skip: int = 0, limit: int = 30):
    """Get a list of all transactions for the logged-in user."""
    trxs = db.query(Transaction).filter(Transaction.user_id == current_user.id).order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
    return [TransactionOut.model_validate(t) for t in trxs]

@router.get("/transactions/{trx_id}", response_model=TransactionOut, tags=["Transactions"], summary="Get a transaction by ID")
def get_transaction(trx_id: int, db: Session = Depends(SessionLocal), current_user: User = Depends(auth.get_current_user)):
    """Get a transaction by its ID."""
    trx = db.query(Transaction).filter(Transaction.id == trx_id, Transaction.user_id == current_user.id).first()
    if not trx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionOut.model_validate(trx)

@router.put("/transactions/{trx_id}", response_model=TransactionOut, tags=["Transactions"], summary="Update a transaction")
def update_transaction(trx_id: int, update: TransactionUpdate, db: Session = Depends(SessionLocal), current_user: User = Depends(auth.get_current_user)):
    """Update a transaction by its ID."""
    trx = db.query(Transaction).filter(Transaction.id == trx_id, Transaction.user_id == current_user.id).first()
    if not trx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for k, v in update.model_dump(exclude_unset=True).items():
        setattr(trx, k, v)
    db.commit()
    db.refresh(trx)
    return TransactionOut.model_validate(trx)

@router.delete("/transactions/{trx_id}", status_code=204, tags=["Transactions"], summary="Delete a transaction")
def delete_transaction(trx_id: int, db: Session = Depends(SessionLocal), current_user: User = Depends(auth.get_current_user)):
    """Delete a transaction by its ID."""
    trx = db.query(Transaction).filter(Transaction.id == trx_id, Transaction.user_id == current_user.id).first()
    if not trx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(trx)
    db.commit()
    return

# --- DASHBOARD & ANALYTICS ---

@router.get("/dashboard/", response_model=DashboardStats, tags=["Dashboard"], summary="Get dashboard stats")
def dashboard(db: Session = Depends(SessionLocal), current_user: User = Depends(auth.get_current_user)):
    """Get total income, total expense, and 5 most recent transactions."""
    income = db.query(Transaction).filter(Transaction.user_id == current_user.id, Transaction.type == 'income').with_entities(Transaction.amount).all()
    total_income = sum([t[0] for t in income]) if income else 0.0
    expense = db.query(Transaction).filter(Transaction.user_id == current_user.id, Transaction.type == 'expense').with_entities(Transaction.amount).all()
    total_expense = sum([t[0] for t in expense]) if expense else 0.0
    recent = db.query(Transaction).filter(Transaction.user_id == current_user.id).order_by(Transaction.date.desc()).limit(5).all()
    return DashboardStats(
        total_income=total_income,
        total_expense=total_expense,
        recent_transactions=[TransactionOut.model_validate(r) for r in recent]
    )

@router.get("/analytics/budget/", response_model=List[BudgetAnalytics], tags=["Analytics"], summary="Analytics for budgeting per category")
def budget_analytics(db: Session = Depends(SessionLocal),
                     current_user: User = Depends(auth.get_current_user)):
    """Analytics: spending per category for the current user."""
    # For demo: budgets are static; could be extended to allow per-user/category budgets.
    category_budgets = {"Groceries": 400, "Dining": 200, "Transport": 150, "Entertainment": 100, "Other": 300}
    results = []
    all_cats = db.query(Transaction.category).filter(Transaction.user_id == current_user.id).distinct()
    for cat_row in all_cats:
        cat = cat_row[0]
        spent = db.query(Transaction).filter(
            Transaction.user_id == current_user.id,
            Transaction.category == cat,
            Transaction.type == 'expense'
        ).with_entities(Transaction.amount).all()
        total_spent = sum([t[0] for t in spent]) if spent else 0.0
        budget = category_budgets.get(cat, None)
        percent = (total_spent / budget) * 100 if budget else None
        results.append(BudgetAnalytics(category=cat, total_spent=total_spent, budget=budget, percent_of_budget=percent))
    return results

