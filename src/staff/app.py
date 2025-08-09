"""Staff Management FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.logging import get_logger
from src.common.health_check import health

from .routes import router

app = FastAPI(
    title="Staff Management Service",
    description="Administrative interface for user and system management",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
logger = get_logger("staff_service")


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
def startup() -> None:
    """Startup event handler."""
    logger.info("Staff Management service started")


@app.on_event("shutdown")
def shutdown() -> None:
    """Shutdown event handler."""
    logger.info("Staff Management service shutting down")
