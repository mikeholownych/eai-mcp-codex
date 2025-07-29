"""Agent Pool FastAPI application."""

from fastapi import FastAPI

from src.common.logging import get_logger
from src.common.health_check import health

from .routes import router

app = FastAPI(title="Agent Pool")
app.include_router(router)
logger = get_logger("agent_pool")


@app.get("/health")
def health_check() -> dict:
    return health()


@app.on_event("startup")
def startup() -> None:
    logger.info("Agent Pool service started")
