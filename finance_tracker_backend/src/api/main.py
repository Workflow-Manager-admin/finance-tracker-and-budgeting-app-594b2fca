# PUBLIC_INTERFACE
"""
Main FastAPI application entrypoint for the Finance Tracker backend.

Features:
  - Robust CORS for mobile frontend.
  - Loads config from environment variables.
  - JWT authentication (register & login).
  - SQLite database with SQLAlchemy.
  - CRUD for transactions.
  - Budget analytics endpoints.
  - Helpful API error responses.
  - OpenAPI documentation customized for frontend/mobile.
"""

import os
from fastapi import (
    FastAPI, HTTPException, status, Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
from starlette.requests import Request as StarletteRequest

from src.api.db import (
    engine, Base
)
from src.api.auth import (
    router as auth_router
)
from src.api.transactions import (
    router as transactions_router
)

# Load environment and validate required config
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET must be set in .env file!")

# App setup with OpenAPI metadata
app = FastAPI(
    title="Finance Tracker API",
    description="API backend for a mobile finance tracker and budgeting application.",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url=None,
    contact={
        "name": "Finance Tracker Support",
        "email": "support@example.com"
    }
)

# Robust CORS: Allow all, with credentials, for mobile dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to ["*"] for mobile dev. In production, restrict this!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables (Do once at startup)
@app.on_event("startup")
def on_startup():
    """Initialize DB schema on startup."""
    Base.metadata.create_all(bind=engine)

# PUBLIC_INTERFACE
@app.get("/", summary="Health Check", description="Returns server status and ok response")
async def health_check():
    """Health check endpoint.

    Returns a simple JSON payload to verify that the backend is up and running.
    """
    return JSONResponse(content={"status": "ok", "message": "Backend is running"})

# Include routers (auth, transactions, analytics)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(transactions_router, prefix="/transactions", tags=["Transactions & Analytics"])

# PUBLIC_INTERFACE
@app.get("/api-usage", summary="How to use the API & WebSocket", tags=["Docs"])
def api_usage():
    """
    Helpful API usage documentation endpoint for mobile/frontend devs.
    """
    return {
        "message": "For authentication, use /auth/register and /auth/login to obtain a JWT token. "
                   "Include 'Authorization: Bearer <token>' header for all /transactions endpoints."
    }

# PUBLIC_INTERFACE
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom validation error for frontend clarity."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

# PUBLIC_INTERFACE
@app.exception_handler(HTTPException)
async def http_exception_handler(request: StarletteRequest, exc: HTTPException):
    """Standardized HTTP error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )
