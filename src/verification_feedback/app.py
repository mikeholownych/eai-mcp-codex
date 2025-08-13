"""Verification Feedback FastAPI application."""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.common.logging import get_logger
from src.common.health_check import health
from src.common.metrics import setup_metrics_endpoint

from .routes import router
from .feedback_processor import (
    initialize_feedback_processor,
    shutdown_feedback_processor,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_feedback_processor()
    logger.info("Verification Feedback service started")
    try:
        yield
    finally:
        await shutdown_feedback_processor()
        logger.info("Verification Feedback service shutdown")


app = FastAPI(title="Verification Feedback", lifespan=lifespan)
app.include_router(router)
logger = get_logger("verification_feedback")

# Setup metrics endpoint
setup_metrics_endpoint(app)


@app.get("/health")
async def health_check() -> dict:
    return await health()


## startup/shutdown handled in lifespan
