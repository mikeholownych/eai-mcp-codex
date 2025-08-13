"""Agent Pool FastAPI application."""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.common.logging import get_logger
from src.common.health_check import health

from .routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Agent Pool service started")
    try:
        yield
    finally:
        pass


app = FastAPI(title="Agent Pool", lifespan=lifespan)
app.include_router(router)
logger = get_logger("agent_pool")


@app.get("/health")
async def health_check() -> dict:
    return await health()


## startup moved to lifespan
