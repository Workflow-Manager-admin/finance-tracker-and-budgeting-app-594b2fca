# PUBLIC_INTERFACE
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# The main FastAPI application entrypoint for the backend.
# This file exposes the ASGI 'app' variable as required by Uvicorn.
# It includes a health check endpoint and can be extended to include routers for authentication, transactions, etc.

app = FastAPI(
    title="Finance Tracker API",
    description="API backend for a mobile finance tracker and budgeting application.",
    version="0.1.0",
    openapi_url="/openapi.json"
)

@app.get("/", summary="Health Check", description="Returns server status and ok response")
async def health_check():
    """Health check endpoint.
    
    Returns a simple JSON payload to verify that the backend is up and running.
    """
    return JSONResponse(content={"status": "ok", "message": "Backend is running"})
