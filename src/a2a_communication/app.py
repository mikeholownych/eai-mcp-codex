"""A2A Communication Hub FastAPI application."""

from fastapi import FastAPI

from src.common.health_check import health
from src.common.metrics import setup_metrics_endpoint
from .message_broker import A2AMessageBroker
from .routes import router

app = FastAPI(title="A2A Communication Hub")
app.include_router(router)

# Setup metrics endpoint
setup_metrics_endpoint(app)


@app.on_event("startup")
async def startup() -> None:
    """Create and store the message broker on startup."""
    app.state.broker = await A2AMessageBroker.create()


@app.get("/health")
def health_check() -> dict:
    return health()
