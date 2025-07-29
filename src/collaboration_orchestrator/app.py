"""Collaboration Orchestrator FastAPI application."""

from fastapi import FastAPI

from src.common.logging import get_logger
from src.common.health_check import health

from .routes import router

app = FastAPI(title="Collaboration Orchestrator")
app.include_router(router)
logger = get_logger("collaboration_orchestrator")


@app.get("/health")
def health_check() -> dict:
    return health()


@app.on_event("startup")
def startup() -> None:
    logger.info("Collaboration Orchestrator service started")