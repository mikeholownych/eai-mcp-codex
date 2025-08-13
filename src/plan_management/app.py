"""Plan Management FastAPI application."""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.common.logging import get_logger
from src.common.health_check import health, readiness
from src.common.metrics import setup_metrics_endpoint

from .routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Plan Management service started")
    try:
        yield
    finally:
        pass


app = FastAPI(title="Plan Management", lifespan=lifespan)
app.include_router(router)
logger = get_logger("plan_management")

# Setup metrics endpoint
setup_metrics_endpoint(app)


@app.get("/health")
def health_check() -> dict:
    return health()


@app.get("/healthz")
def liveness_check() -> dict:
    return {"status": "healthy"}


@app.get("/readyz")
async def readiness_check() -> dict:
    return await readiness()


## startup moved to lifespan
