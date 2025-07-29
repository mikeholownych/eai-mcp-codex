"""A2A Communication Hub FastAPI application."""

from fastapi import FastAPI

from src.common.logging import get_logger
from src.common.health_check import health

from .routes import router

app = FastAPI(title="A2A Communication Hub")
app.include_router(router)
logger = get_logger("a2a_communication")


@app.get("/health")
def health_check() -> dict:
    return health()


@app.on_event("startup")
def startup() -> None:
    logger.info("A2A Communication Hub service started")