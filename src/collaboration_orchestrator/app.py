"""Collaboration Orchestrator FastAPI application."""

from fastapi import FastAPI

from src.common.logging import get_logger
from src.common.health_check import health

from .routes import router
from .multi_developer_routes import router as multi_dev_router

app = FastAPI(
    title="Collaboration Orchestrator",
    description="Advanced multi-agent collaboration and multi-developer coordination system",
    version="2.0.0"
)

# Include both the original collaboration routes and new multi-developer routes
app.include_router(router, prefix="/collaboration")
app.include_router(multi_dev_router)

logger = get_logger("collaboration_orchestrator")


@app.get("/health")
def health_check() -> dict:
    return health()


@app.on_event("startup")
def startup() -> None:
    logger.info("Collaboration Orchestrator service started")
