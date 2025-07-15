import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import auth_router
from .transactions import transaction_router, category_router, budget_router
from .dashboard import dashboard_router, analytics_router

# Ensure DB tables exist for dev/test: create SQLite schema if missing
from .db import Base, engine

openapi_tags = [
    {"name": "Authentication", "description": "User registration, login, and authentication."},
    {"name": "Transactions", "description": "Transaction CRUD and listing."},
    {"name": "Categories", "description": "Spending/income categories."},
    {"name": "Budgets", "description": "Budget creation and management."},
    {"name": "Dashboard", "description": "Recent transactions and summary endpoints."},
    {"name": "Analytics", "description": "Category and budget analytics/statistics."},
    {"name": "Health", "description": "API health/status checks."}
]

# Get frontend CORS allowed origins from env, fallback to wildcard for dev
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "*")
origins = (
    [x.strip() for x in CORS_ALLOWED_ORIGINS.split(",")] if CORS_ALLOWED_ORIGINS != "*" else ["*"]
)

app = FastAPI(
    title="Finance Tracker API",
    description="Backend API for mobile personal finance tracker and budgeting app. Features user authentication, secure JWT-protected endpoints, robust validation, and user data separation.",
    version="1.0.0",
    openapi_tags=openapi_tags,
    swagger_ui_parameters={"persistAuthorization": True}
)

@app.on_event("startup")
def create_db_and_tables():
    """
    Ensures all SQLAlchemy tables exist in dev/test (SQLite): runs on app startup.
    In prod, migrations should be used instead.
    """
    Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(transaction_router)
app.include_router(category_router)
app.include_router(budget_router)
app.include_router(dashboard_router)
app.include_router(analytics_router)

@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint. Used for liveness/readiness probes and CI checks."""
    return {"message": "Healthy"}
