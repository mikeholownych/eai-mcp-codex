"""FastAPI application for Authentication Service."""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routes import router
from ..common.logging import get_logger
from ..common.consul_client import ConsulClient
from ..common.exceptions import setup_exception_handlers

logger = get_logger("auth_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Auth Service...")
    
    # Register with Consul
    consul_client = ConsulClient()
    
    service_name = os.getenv("SERVICE_NAME", "auth-service")
    service_port = int(os.getenv("SERVICE_PORT", "8007"))
    service_host = os.getenv("SERVICE_HOST", "0.0.0.0")
    
    await consul_client.register_service(
        name=service_name,
        port=service_port,
        host=service_host,
        health_check_path="/health",
        tags=["auth", "security", "api"]
    )
    
    logger.info(f"Auth Service started on port {service_port}")
    
    yield
    
    logger.info("Shutting down Auth Service...")
    await consul_client.deregister_service(f"{service_name}-{service_port}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="MCP Authentication Service",
        description="Authentication and user management service for MCP platform",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include routes
    app.include_router(router, prefix="/api/auth", tags=["authentication"])
    
    # Add health check at root level
    @app.get("/health")
    async def health_check():
        """Service health check."""
        return {
            "status": "healthy",
            "service": "auth-service",
            "version": "1.0.0"
        }
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("SERVICE_PORT", "8007"))
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    
    logger.info(f"Starting Auth Service on {host}:{port}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )