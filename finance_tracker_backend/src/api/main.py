from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from . import database
from .routes import router as api_router

load_dotenv()

openapi_tags = [
    {"name": "Authentication", "description": "User registration/login for authentication"},
    {"name": "Transactions", "description": "CRUD operations for user transactions"},
    {"name": "Dashboard", "description": "User statistics and recent activity summary"},
    {"name": "Analytics", "description": "Budget visualization and spending category breakdown"},
]

app = FastAPI(
    title="Finance Tracker API",
    description="API for personal finance tracking, budgeting, transactions, and user authentication.",
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

@app.on_event("startup")
def on_startup():
    database.create_db_and_tables()

@app.get("/", tags=["Dashboard"])
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}

app.include_router(api_router, prefix="", tags=["API"])

# PUBLIC_INTERFACE
if __name__ == "__main__":
    """
    Entrypoint for running the FastAPI app with Uvicorn.
    Usage: python -m src.api.main
    Or: uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
    """
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=3001,
        reload=True
    )
