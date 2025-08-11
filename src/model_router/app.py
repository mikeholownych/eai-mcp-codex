"""Model Router FastAPI application."""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.common.logging import get_logger
from src.common.health_check import health
from src.common.metrics import setup_metrics_endpoint

from .routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Model Router service started")
    try:
        yield
    finally:
        pass


app = FastAPI(title="Model Router", lifespan=lifespan)
app.include_router(router)
logger = get_logger("model_router")

# Setup metrics endpoint
setup_metrics_endpoint(app)


@app.get("/health")
async def health_check() -> dict:
    return await health()


## startup moved to lifespan
