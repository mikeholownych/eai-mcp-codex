"""A2A Communication Hub FastAPI application."""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.common.health_check import health
from src.common.metrics import setup_metrics_endpoint
from .message_broker import A2AMessageBroker
from .routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize broker on startup
    app.state.broker = await A2AMessageBroker.create()
    try:
        yield
    finally:
        pass


app = FastAPI(title="A2A Communication Hub", lifespan=lifespan)
app.include_router(router)

# Setup metrics endpoint
setup_metrics_endpoint(app)


## startup handled in lifespan


@app.get("/health")
async def health_check() -> dict:
    return await health()
