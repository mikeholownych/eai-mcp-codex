"""Marketing Service FastAPI application."""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from src.common.logging import get_logger
from src.common.health_check import health
from src.common.redis_client import get_redis
from src.common.database import DatabaseManager
from src.common.fastapi_auth import get_current_user, verify_staff_access

from .sales_funnel import SalesFunnelManager
from .automation import MarketingAutomation
from .lead_management import LeadManager
from .email_service import EmailService
from .analytics import MarketingAnalytics
from .a_b_testing import ABTesting
from .crm_integration import CRMIntegration

logger = get_logger("marketing_service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Marketing Service...")
    
    # Initialize Redis and database connections
    redis_client = await get_redis()
    db_manager = DatabaseManager("mcp")
    
    # Initialize marketing components
    app.state.sales_funnel_manager = SalesFunnelManager(redis_client, db_manager)
    app.state.automation = MarketingAutomation(redis_client, db_manager)
    app.state.lead_manager = LeadManager(redis_client, db_manager)
    app.state.email_service = EmailService(redis_client, {})
    app.state.analytics = MarketingAnalytics(redis_client, db_manager)
    app.state.ab_testing = ABTesting(redis_client, db_manager)
    app.state.crm_integration = CRMIntegration(redis_client, {})
    
    logger.info("Marketing Service started successfully")
    
    try:
        yield
    finally:
        logger.info("Shutting down Marketing Service...")
        await redis_client.close()
        await db_manager.disconnect()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="MCP Marketing Service",
        description="Marketing automation, sales funnel, and lead management service",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8080"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routes
    from .routes import router
    app.include_router(router, prefix="/api/marketing", tags=["marketing"])
    
    # Add health check
    @app.get("/health")
    async def health_check():
        """Service health check."""
        return await health()
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("SERVICE_PORT", "8008"))
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    
    logger.info(f"Starting Marketing Service on {host}:{port}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
