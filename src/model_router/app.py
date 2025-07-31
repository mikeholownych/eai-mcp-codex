"""Model Router FastAPI application."""

from fastapi import FastAPI

from src.common.logging import get_logger
from src.common.health_check import health
from src.common.metrics import setup_metrics_endpoint

from .routes import router

app = FastAPI(title="Model Router")
app.include_router(router)
logger = get_logger("model_router")

# Setup metrics endpoint
setup_metrics_endpoint(app)


@app.get("/health")
def health_check() -> dict:
    return health()


@app.on_event("startup")
def startup() -> None:
    logger.info("Model Router service started")
