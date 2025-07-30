from unittest.mock import AsyncMock

import pytest

from src.common.database import DatabaseManager
from src.common.service_registry import ServiceRegistry


@pytest.mark.asyncio
async def test_register_service() -> None:
    db = DatabaseManager("postgresql://user:pass@localhost/db")
    db.execute_update = AsyncMock(return_value=1)  # type: ignore[assignment]
    registry = ServiceRegistry(db)

    result = await registry.register_service("svc", "http://svc", {"a": 1})
    assert result
    db.execute_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_heartbeat() -> None:
    db = DatabaseManager("postgresql://user:pass@localhost/db")
    db.execute_update = AsyncMock(return_value=1)  # type: ignore[assignment]
    registry = ServiceRegistry(db)

    result = await registry.heartbeat("svc")
    assert result
    db.execute_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_service() -> None:
    db = DatabaseManager("postgresql://user:pass@localhost/db")
    db.execute_query = AsyncMock(  # type: ignore[assignment]
        return_value=[
            {
                "service_name": "svc",
                "service_url": "http://svc",
                "health_status": "healthy",
                "last_heartbeat": "2024-01-01T00:00:00",
                "metadata": "{}",
            }
        ]
    )
    registry = ServiceRegistry(db)

    service = await registry.get_service("svc")
    assert service is not None
    assert service.service_name == "svc"
    db.execute_query.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_services_empty() -> None:
    db = DatabaseManager("postgresql://user:pass@localhost/db")
    db.execute_query = AsyncMock(return_value=[])  # type: ignore[assignment]
    registry = ServiceRegistry(db)

    result = await registry.list_services()
    assert result == []
    db.execute_query.assert_awaited_once()
