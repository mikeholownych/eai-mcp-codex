"""Verification Feedback FastAPI application."""

from fastapi import FastAPI

from src.common.logging import get_logger
from src.common.health_check import health
from src.common.metrics import setup_metrics_endpoint

from .routes import router
from .feedback_processor import initialize_feedback_processor, shutdown_feedback_processor

app = FastAPI(title="Verification Feedback")
app.include_router(router)
logger = get_logger("verification_feedback")

# Setup metrics endpoint
setup_metrics_endpoint(app)


@app.get("/health")
def health_check() -> dict:
    return health()


@app.on_event("startup")
async def startup() -> None:
    await initialize_feedback_processor()
    logger.info("Verification Feedback service started")


@app.on_event("shutdown")
async def shutdown() -> None:
    await shutdown_feedback_processor()
    logger.info("Verification Feedback service shutdown")
