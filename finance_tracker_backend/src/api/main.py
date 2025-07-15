from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import auth_router
from .transactions import transaction_router, category_router, budget_router
from .dashboard import dashboard_router, analytics_router

openapi_tags = [
    {"name": "Authentication", "description": "User registration, login, and authentication."},
    {"name": "Transactions", "description": "Transaction CRUD and listing."},
    {"name": "Categories", "description": "Spending/income categories."},
    {"name": "Budgets", "description": "Budget creation and management."},
    {"name": "Dashboard", "description": "Recent transactions and summary endpoints."},
    {"name": "Analytics", "description": "Category and budget analytics/statistics."}
]

app = FastAPI(
    title="Finance Tracker API",
    description="Backend for mobile personal finance tracker/budgeting app.",
    version="1.0.0",
    openapi_tags=openapi_tags
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    """Health check endpoint"""
    return {"message": "Healthy"}
