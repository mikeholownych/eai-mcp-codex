"""Collaboration Orchestrator FastAPI application."""

from fastapi import FastAPI

from src.common.logging import get_logger
from src.common.health_check import health

from .routes import router
from .multi_developer_routes import router as multi_dev_router
from .orchestrator import CollaborationOrchestrator
from .multi_developer_orchestrator import MultiDeveloperOrchestrator
from .developer_profile_manager import DeveloperProfileManager
from .intelligent_conflict_resolver import IntelligentConflictResolver
from src.common.redis_client import get_redis_connection
from src.a2a_communication.message_broker import A2AMessageBroker
from src.common.database import DatabaseManager

app = FastAPI(
    title="Collaboration Orchestrator",
    description="Advanced multi-agent collaboration and multi-developer coordination system",
    version="2.0.0",
)

# Include both the original collaboration routes and new multi-developer routes
app.include_router(router, prefix="/collaboration")
app.include_router(multi_dev_router)

logger = get_logger("collaboration_orchestrator")


@app.get("/health")
def health_check() -> dict:
    return health()


@app.on_event("startup")
async def startup() -> None:
    app.state.orchestrator = CollaborationOrchestrator()
    await app.state.orchestrator.initialize()
    logger.info("Collaboration Orchestrator service started")

    # Initialize Multi-Developer Coordination components
    redis_conn = await get_redis_connection()
    message_broker_instance = await A2AMessageBroker.create()
    db_manager = DatabaseManager('multi_developer_orchestrator')
    await db_manager.connect()
    postgres_pool = db_manager._pool

    app.state.developer_profile_manager = await DeveloperProfileManager.create(redis=redis_conn, postgres_pool=postgres_pool)
    app.state.intelligent_conflict_resolver = await IntelligentConflictResolver.create(profile_manager=app.state.developer_profile_manager, message_broker=message_broker_instance, postgres_pool=postgres_pool, redis=redis_conn)
    app.state.multi_developer_orchestrator = await MultiDeveloperOrchestrator.create(redis=redis_conn, message_broker=message_broker_instance, postgres_pool=postgres_pool)
