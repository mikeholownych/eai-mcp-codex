"""Feedback processing business logic implementation."""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.common.database import (
    DatabaseManager,
    deserialize_datetime,
    deserialize_json_field,
    serialize_datetime,
    serialize_json_field,
)
from src.common.logging import get_logger

from .config import settings
from .models import (
    Feedback,
    FeedbackRequest,
    FeedbackSeverity,
    FeedbackType,
)

logger = get_logger("feedback_processor")


class FeedbackProcessor:
    """Core business logic for feedback handling."""

    def __init__(self, dsn: str = settings.database_url) -> None:
        self.db_manager = DatabaseManager("verification_feedback")
        self.db_manager.dsn = dsn
        self._in_memory: Optional[Dict[str, Feedback]] = (
            {} if os.getenv("TESTING_MODE") == "true" else None
        )

    async def initialize_database(self) -> None:
        """Initialize database connection and ensure schema."""
        if self._in_memory is not None:
            return
        await self.db_manager.connect()
        await self._ensure_database()

    async def shutdown_database(self) -> None:
        """Shutdown database resources."""
        if self._in_memory is not None:
            self._in_memory.clear()
            return
        await self.db_manager.disconnect()

    async def _ensure_database(self) -> None:
        """Create feedback table if it does not exist."""
        script = """
        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY,
            feedback_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            target_type TEXT,
            target_id TEXT,
            tags JSONB DEFAULT '[]',
            metadata JSONB DEFAULT '{}',
            is_resolved BOOLEAN DEFAULT FALSE,
            resolution_notes TEXT,
            resolved_by TEXT,
            resolved_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_feedback_target
            ON feedback(target_type, target_id);
        """
        await self.db_manager.execute_script(script)
        logger.info("Database tables ensured.")

    async def submit_feedback(
        self, request: FeedbackRequest, source: str = "system"
    ) -> Feedback:
        """Persist new feedback and return stored record."""
        now = datetime.utcnow()
        feedback = Feedback(
            id=str(uuid.uuid4()),
            feedback_type=request.feedback_type,
            severity=request.severity,
            title=request.title,
            content=request.content,
            source=source,
            target_type=request.target_type,
            target_id=request.target_id,
            tags=request.tags,
            metadata=request.metadata,
            created_at=now,
            updated_at=now,
        )

        if self._in_memory is not None:
            self._in_memory[feedback.id] = feedback
            return feedback

        query = """
            INSERT INTO feedback (
                id, feedback_type, severity, title, content, source, target_type,
                target_id, tags, metadata, is_resolved, created_at, updated_at
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
        """
        values = (
            feedback.id,
            feedback.feedback_type.value,
            feedback.severity.value,
            feedback.title,
            feedback.content,
            feedback.source,
            feedback.target_type,
            feedback.target_id,
            serialize_json_field(feedback.tags),
            serialize_json_field(feedback.metadata),
            feedback.is_resolved,
            serialize_datetime(feedback.created_at),
            serialize_datetime(feedback.updated_at),
        )
        await self.db_manager.execute_update(query, values)
        logger.info("Created feedback %s", feedback.id)
        return feedback

    async def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """Retrieve feedback by id."""
        if self._in_memory is not None:
            return self._in_memory.get(feedback_id)

        query = "SELECT * FROM feedback WHERE id=$1"
        rows = await self.db_manager.execute_query(query, (feedback_id,))
        if not rows:
            return None
        return self._row_to_feedback(rows[0])

    async def list_feedback(self, limit: int = 100) -> List[Feedback]:
        """List most recent feedback entries."""
        if self._in_memory is not None:
            values = sorted(
                self._in_memory.values(),
                key=lambda f: f.created_at,
                reverse=True,
            )
            return values[:limit]

        query = "SELECT * FROM feedback ORDER BY created_at DESC LIMIT $1"
        rows = await self.db_manager.execute_query(query, (limit,))
        return [self._row_to_feedback(r) for r in rows]

    async def resolve_feedback(
        self, feedback_id: str, notes: str, resolved_by: str = "system"
    ) -> Optional[Feedback]:
        """Mark feedback as resolved."""
        feedback = await self.get_feedback(feedback_id)
        if not feedback:
            return None

        feedback.is_resolved = True
        feedback.resolution_notes = notes
        feedback.resolved_by = resolved_by
        feedback.resolved_at = datetime.utcnow()
        feedback.updated_at = feedback.resolved_at

        if self._in_memory is not None:
            self._in_memory[feedback.id] = feedback
            return feedback

        await self._update_feedback(feedback)
        return feedback

    async def _update_feedback(self, feedback: Feedback) -> None:
        """Update existing feedback record."""
        query = """
            UPDATE feedback SET
                feedback_type=$2, severity=$3, title=$4, content=$5, source=$6,
                target_type=$7, target_id=$8, tags=$9, metadata=$10,
                is_resolved=$11, resolution_notes=$12, resolved_by=$13,
                resolved_at=$14, updated_at=$15
            WHERE id=$1
        """
        values = (
            feedback.id,
            feedback.feedback_type.value,
            feedback.severity.value,
            feedback.title,
            feedback.content,
            feedback.source,
            feedback.target_type,
            feedback.target_id,
            serialize_json_field(feedback.tags),
            serialize_json_field(feedback.metadata),
            feedback.is_resolved,
            feedback.resolution_notes,
            feedback.resolved_by,
            serialize_datetime(feedback.resolved_at),
            serialize_datetime(feedback.updated_at),
        )
        await self.db_manager.execute_update(query, values)

    def _row_to_feedback(self, row: Dict[str, Any]) -> Feedback:
        """Convert database row into Feedback model."""
        return Feedback(
            id=row["id"],
            feedback_type=FeedbackType(row["feedback_type"]),
            severity=FeedbackSeverity(row["severity"]),
            title=row["title"],
            content=row["content"],
            source=row["source"],
            target_type=row["target_type"],
            target_id=row["target_id"],
            tags=deserialize_json_field(row["tags"]),
            metadata=deserialize_json_field(row["metadata"]),
            is_resolved=bool(row["is_resolved"]),
            resolution_notes=row["resolution_notes"],
            resolved_by=row["resolved_by"],
            resolved_at=deserialize_datetime(row["resolved_at"]),
            created_at=deserialize_datetime(row["created_at"]),
            updated_at=deserialize_datetime(row["updated_at"]),
        )


_feedback_processor: Optional[FeedbackProcessor] = None


async def initialize_feedback_processor() -> None:
    """Initialize the global feedback processor."""
    global _feedback_processor
    if _feedback_processor is None:
        _feedback_processor = FeedbackProcessor()
        await _feedback_processor.initialize_database()


def get_feedback_processor() -> FeedbackProcessor:
    """Get the feedback processor instance."""
    if _feedback_processor is None:
        raise RuntimeError(
            "Feedback processor not initialized. Call initialize_feedback_processor() first."
        )
    return _feedback_processor


async def shutdown_feedback_processor() -> None:
    """Shutdown and clear the global feedback processor."""
    global _feedback_processor
    if _feedback_processor is not None:
        await _feedback_processor.shutdown_database()
        _feedback_processor = None
