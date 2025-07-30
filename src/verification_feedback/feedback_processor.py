"""Feedback Processing business logic implementation."""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.common.logging import get_logger
from src.common.database import DatabaseManager
from .models import Feedback, FeedbackType, FeedbackSeverity
from .config import settings

logger = get_logger("feedback_processor")

# Global instance
_feedback_processor = None


class FeedbackProcessor:
    """Core business logic for feedback processing."""

    def __init__(self, dsn: str = settings.database_url):
        self.db_manager = DatabaseManager(dsn)
        self.dsn = dsn

    async def initialize_database(self):
        """Initialize database connection and create tables if they don't exist."""
        await self.db_manager.connect()
        await self._ensure_database()

    async def shutdown_database(self):
        """Shutdown database connection pool."""
        await self.db_manager.disconnect()

    async def _ensure_database(self):
        """Create database and tables if they don't exist."""
        script = """
        CREATE TABLE IF NOT EXISTS feedback (
            id VARCHAR(255) PRIMARY KEY,
            feedback_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            metadata JSONB DEFAULT '{}',
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
        CREATE INDEX IF NOT EXISTS idx_feedback_severity ON feedback(severity);
        CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
        CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);
        """
        
        await self.db_manager.execute_script(script)

    async def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """Get feedback by ID."""
        query = """
        SELECT id, feedback_type, severity, title, description, metadata, status, created_at, updated_at
        FROM feedback WHERE id = $1
        """
        
        try:
            row = await self.db_manager.execute_query(query, (feedback_id,))
            if row:
                return Feedback(
                    id=row[0],
                    feedback_type=FeedbackType(row[1]),
                    severity=FeedbackSeverity(row[2]),
                    title=row[3],
                    description=row[4],
                    metadata=row[5] or {},
                    status=row[6],
                    created_at=row[7],
                    updated_at=row[8]
                )
            return None
        except Exception as e:
            logger.error(f"Error getting feedback {feedback_id}: {e}")
            return None

    async def create_feedback(self, feedback_data: Dict[str, Any]) -> Feedback:
        """Create new feedback entry."""
        feedback_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        query = """
        INSERT INTO feedback (id, feedback_type, severity, title, description, metadata, status, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        
        values = (
            feedback_id,
            feedback_data.get('feedback_type', 'general'),
            feedback_data.get('severity', 'medium'),
            feedback_data.get('title', ''),
            feedback_data.get('description', ''),
            feedback_data.get('metadata', {}),
            'pending',
            now,
            now
        )
        
        await self.db_manager.execute_update(query, values)
        
        return Feedback(
            id=feedback_id,
            feedback_type=FeedbackType(values[1]),
            severity=FeedbackSeverity(values[2]),
            title=values[3],
            description=values[4],
            metadata=values[5],
            status=values[6],
            created_at=values[7],
            updated_at=values[8]
        )

    async def list_feedback(self, limit: int = 100, offset: int = 0) -> List[Feedback]:
        """List feedback entries."""
        query = """
        SELECT id, feedback_type, severity, title, description, metadata, status, created_at, updated_at
        FROM feedback 
        ORDER BY created_at DESC 
        LIMIT $1 OFFSET $2
        """
        
        try:
            rows = await self.db_manager.execute_query(query, (limit, offset))
            return [
                Feedback(
                    id=row[0],
                    feedback_type=FeedbackType(row[1]),
                    severity=FeedbackSeverity(row[2]),
                    title=row[3],
                    description=row[4],
                    metadata=row[5] or {},
                    status=row[6],
                    created_at=row[7],
                    updated_at=row[8]
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error listing feedback: {e}")
            return []


async def initialize_feedback_processor():
    """Initialize the global feedback processor."""
    global _feedback_processor
    if _feedback_processor is None:
        _feedback_processor = FeedbackProcessor()
        await _feedback_processor.initialize_database()


def get_feedback_processor() -> FeedbackProcessor:
    """Get the feedback processor instance."""
    if _feedback_processor is None:
        raise RuntimeError("Feedback processor not initialized. Call initialize_feedback_processor() first.")
    return _feedback_processor


async def shutdown_feedback_processor():
    """Shutdown the feedback processor."""
    global _feedback_processor
    if _feedback_processor is not None:
        await _feedback_processor.shutdown_database()
        _feedback_processor = None