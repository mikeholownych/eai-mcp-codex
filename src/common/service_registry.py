"""Database-backed service registry utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .database import DatabaseManager
from .logging import get_logger

logger = get_logger("service_registry")


@dataclass
class ServiceInfo:
    """Representation of a registered service."""

    service_name: str
    service_url: str
    health_status: str
    last_heartbeat: datetime
    metadata: Dict[str, Any]


class ServiceRegistry:
    """High-level interface for the ``service_registry`` table."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    async def register_service(
        self,
        service_name: str,
        service_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Insert or update a service record."""
        metadata_json = json.dumps(metadata or {})
        query = (
            "INSERT INTO service_registry (service_name, service_url, metadata) "
            "VALUES ($1, $2, $3) "
            "ON CONFLICT (service_name) DO UPDATE SET "
            "service_url = EXCLUDED.service_url, metadata = EXCLUDED.metadata, "
            "updated_at = CURRENT_TIMESTAMP"
        )
        try:
            rows = await self.db.execute_update(
                query, (service_name, service_url, metadata_json)
            )
            return rows > 0
        except Exception as exc:  # pragma: no cover - unexpected DB errors
            logger.error("Failed to register service %s: %s", service_name, exc)
            return False

    async def heartbeat(self, service_name: str, status: str = "healthy") -> bool:
        """Update heartbeat timestamp and status for a service."""
        query = (
            "UPDATE service_registry SET health_status = $1, last_heartbeat = CURRENT_TIMESTAMP, "
            "updated_at = CURRENT_TIMESTAMP WHERE service_name = $2"
        )
        try:
            rows = await self.db.execute_update(query, (status, service_name))
            return rows > 0
        except Exception as exc:  # pragma: no cover - unexpected DB errors
            logger.error("Failed to update heartbeat for %s: %s", service_name, exc)
            return False

    async def get_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Retrieve a registered service by name."""
        query = (
            "SELECT service_name, service_url, health_status, last_heartbeat, metadata "
            "FROM service_registry WHERE service_name = $1"
        )
        try:
            rows = await self.db.execute_query(query, (service_name,))
            if not rows:
                return None
            row = rows[0]
            return ServiceInfo(
                service_name=row["service_name"],
                service_url=row["service_url"],
                health_status=row["health_status"],
                last_heartbeat=row["last_heartbeat"],
                metadata=json.loads(row["metadata"] or "{}"),
            )
        except Exception as exc:  # pragma: no cover - unexpected DB errors
            logger.error("Failed to fetch service %s: %s", service_name, exc)
            return None

    async def list_services(self) -> List[ServiceInfo]:
        """Return all registered services."""
        query = "SELECT service_name, service_url, health_status, last_heartbeat, metadata FROM service_registry"
        try:
            rows = await self.db.execute_query(query)
            result = []
            for row in rows:
                result.append(
                    ServiceInfo(
                        service_name=row["service_name"],
                        service_url=row["service_url"],
                        health_status=row["health_status"],
                        last_heartbeat=row["last_heartbeat"],
                        metadata=json.loads(row["metadata"] or "{}"),
                    )
                )
            return result
        except Exception as exc:  # pragma: no cover - unexpected DB errors
            logger.error("Failed to list services: %s", exc)
            return []
