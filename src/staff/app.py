"""Staff Management FastAPI application."""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from src.common.logging import get_logger
from src.common.health_check import health, readiness

from .routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Staff Management service started")
    try:
        yield
    finally:
        logger.info("Staff Management service shutting down")


app = FastAPI(
    title="Staff Management Service",
    description="Administrative interface for user and system management",
    version="1.0.0",
    lifespan=lifespan,
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
async def health_check() -> dict:
    """Health check endpoint."""
    # Staff tests expect 'healthy'
    return {"status": "healthy"}


@app.get("/healthz")
async def liveness_check() -> dict:
    return {"status": "healthy"}


@app.get("/readyz")
async def readiness_check() -> dict:
    return await readiness()


