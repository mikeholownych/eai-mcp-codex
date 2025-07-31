"""Feedback Processing business logic implementation."""
# ruff: noqa

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.common.logging import get_logger
from src.common.database import (
    DatabaseManager,
    serialize_json_field,
    serialize_datetime,
)
from .models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    FeedbackRequest,
    FeedbackSummary,
    ProcessingResult,
)
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
        logger.info("Database tables ensured.")

    async def submit_feedback(
        self, request: FeedbackRequest, source: str = "system"
    ) -> Feedback:
        """Submit new feedback."""
        feedback_id = str(uuid.uuid4())
        now = datetime.utcnow()

        query = """
        SELECT id, feedback_type, severity, title, description, metadata, status, created_at, updated_at
        FROM feedback WHERE id = $1
        """
        
        try:
            # Determine processing actions based on feedback type and severity
            actions_taken = []

            if feedback.feedback_type == FeedbackType.ERROR_REPORT:
                actions_taken.extend(await self._process_error_report(feedback))
            elif feedback.feedback_type == FeedbackType.PERFORMANCE_METRIC:
                actions_taken.extend(await self._process_performance_metric(feedback))
            elif feedback.feedback_type == FeedbackType.QUALITY_ASSESSMENT:
                actions_taken.extend(await self._process_quality_assessment(feedback))
            elif feedback.feedback_type == FeedbackType.USER_FEEDBACK:
                actions_taken.extend(await self._process_user_feedback(feedback))
            else:
                actions_taken.append("Applied general processing")

            # Handle severity-specific actions
            if feedback.severity == FeedbackSeverity.CRITICAL:
                actions_taken.extend(await self._handle_critical_feedback(feedback))
            elif feedback.severity == FeedbackSeverity.HIGH:
                actions_taken.extend(
                    await self._handle_high_priority_feedback(feedback)
                )

            # Update feedback processing timestamp
            feedback.updated_at = datetime.utcnow()
            await self._update_feedback(feedback)

            # Log successful processing
            await self._log_processing(
                feedback.id,
                "processed",
                f"Successfully processed by {processor}. Actions: {', '.join(actions_taken)}",
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return ProcessingResult(
                success=True,
                message=f"Feedback processed successfully. Actions taken: {', '.join(actions_taken)}",
                processed_items=1,
                execution_time_ms=execution_time,
                metadata={"actions_taken": actions_taken},
            )

        except Exception as e:
            error_msg = f"Failed to process feedback: {str(e)}"
            logger.error(error_msg)

            # Log failed processing
            await self._log_processing(feedback.id, "processing_failed", error_msg)

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return ProcessingResult(
                success=False,
                message=error_msg,
                processed_items=0,
                errors=[error_msg],
                execution_time_ms=execution_time,
            )

    async def _auto_process_feedback(self, feedback: Feedback):
        """Automatically process feedback based on rules."""
        # Auto-assign tags based on content
        content_lower = feedback.content.lower()
        auto_tags = []

        if any(
            word in content_lower for word in ["bug", "error", "crash", "exception"]
        ):
            auto_tags.append("bug")

        if any(
            word in content_lower for word in ["slow", "performance", "timeout", "lag"]
        ):
            auto_tags.append("performance")

        if any(
            word in content_lower
            for word in ["security", "vulnerable", "exploit", "hack"]
        ):
            auto_tags.append("security")

        if any(word in content_lower for word in ["ui", "ux", "interface", "design"]):
            auto_tags.append("ui-ux")

        # Add auto-generated tags
        feedback.tags.extend([tag for tag in auto_tags if tag not in feedback.tags])

        # Auto-escalate critical issues
        if feedback.severity == FeedbackSeverity.CRITICAL:
            await self._escalate_feedback(feedback)

    async def _process_error_report(self, feedback: Feedback) -> List[str]:
        """Process error report feedback."""
        actions = []

        # Extract error information
        error_info = self._extract_error_info(feedback.content)
        if error_info:
            feedback.metadata.update({"error_analysis": error_info})
            actions.append("Extracted error information")

        # Check for known issues
        if await self._is_known_issue(feedback):
            actions.append("Matched to known issue")
        else:
            actions.append("Flagged as new issue")

        # Create automated ticket if critical
        if feedback.severity in [FeedbackSeverity.CRITICAL, FeedbackSeverity.HIGH]:
            actions.append("Created automated support ticket")

        return actions

    async def _process_performance_metric(self, feedback: Feedback) -> List[str]:
        """Process performance metric feedback."""
        actions = []

        # Extract metrics
        metrics = self._extract_metrics(feedback.content)
        if metrics:
            feedback.metadata.update({"performance_metrics": metrics})
            actions.append("Extracted performance metrics")

        # Check against thresholds
        if self._metrics_exceed_threshold(metrics):
            actions.append("Performance thresholds exceeded")
            if feedback.severity != FeedbackSeverity.CRITICAL:
                feedback.severity = FeedbackSeverity.HIGH
                actions.append("Escalated severity to HIGH")

        return actions

    async def _process_quality_assessment(self, feedback: Feedback) -> List[str]:
        """Process quality assessment feedback."""
        actions = []

        # Extract quality scores
        quality_data = self._extract_quality_data(feedback.content)
        if quality_data:
            feedback.metadata.update({"quality_assessment": quality_data})
            actions.append("Extracted quality assessment data")

        # Generate improvement suggestions
        suggestions = self._generate_quality_suggestions(quality_data)
        if suggestions:
            feedback.metadata.update({"improvement_suggestions": suggestions})
            actions.append("Generated improvement suggestions")

        return actions

    async def _process_user_feedback(self, feedback: Feedback) -> List[str]:
        """Process user feedback."""
        actions = []

        # Sentiment analysis (simplified)
        sentiment = self._analyze_sentiment(feedback.content)
        feedback.metadata.update({"sentiment": sentiment})
        actions.append(f"Analyzed sentiment: {sentiment}")

        # Categorize feedback
        category = self._categorize_user_feedback(feedback.content)
        if category and "category" not in feedback.tags:
            feedback.tags.append(category)
            actions.append(f"Categorized as: {category}")

        return actions

    async def _handle_critical_feedback(self, feedback: Feedback) -> List[str]:
        """Handle critical severity feedback."""
        actions = []

        # Immediate notification
        actions.append("Sent immediate notification")

        # Create urgent ticket
        actions.append("Created urgent support ticket")

        # Flag for immediate review
        feedback.metadata["requires_immediate_attention"] = True
        actions.append("Flagged for immediate attention")

        return actions

    async def _handle_high_priority_feedback(self, feedback: Feedback) -> List[str]:
        """Handle high priority feedback."""
        actions = []

        # Schedule for review within 24 hours
        actions.append("Scheduled for priority review")

        # Create standard ticket
        actions.append("Created priority support ticket")

        return actions

    async def resolve_feedback(
        self, feedback_id: str, resolution_notes: str, resolved_by: str = "system"
    ) -> Optional[Feedback]:
        """Mark feedback as resolved."""
        try:
            feedback = await self.get_feedback(feedback_id)
            if not feedback:
                return None
        except Exception as e:
            logger.error(f"Error getting feedback {feedback_id}: {e}")
            return None

        return self._row_to_feedback(row[0])

    async def list_feedback(
        self,
        feedback_type: Optional[str] = None,
        severity: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Feedback]:
        """List feedback with optional filtering."""
        query = "SELECT * FROM feedback WHERE 1=1"
        params = []
        param_idx = 1

        if feedback_type:
            query += f" AND feedback_type = ${param_idx}"
            params.append(feedback_type)
            param_idx += 1

        if severity:
            query += f" AND severity = ${param_idx}"
            params.append(severity)
            param_idx += 1

        if target_type:
            query += f" AND target_type = ${param_idx}"
            params.append(target_type)
            param_idx += 1

        if target_id:
            query += f" AND target_id = ${param_idx}"
            params.append(target_id)
            param_idx += 1

        if resolved is not None:
            query += f" AND is_resolved = ${param_idx}"
            params.append(resolved)
            param_idx += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_idx}"
        params.append(limit)

        rows = await self.db_manager.execute_query(query, tuple(params))
        return [self._row_to_feedback(row) for row in rows]

    async def get_feedback_summary(
        self, target_type: Optional[str] = None, target_id: Optional[str] = None
    ) -> FeedbackSummary:
        """Get feedback summary for a target."""
        # Get all relevant feedback
        feedback_list = await self.list_feedback(
            target_type=target_type, target_id=target_id, limit=1000
        )

        if not target_type and not target_id:
            target_type = "all"
            target_id = "all"

        # Calculate statistics
        total_feedback = len(feedback_list)
        by_type = {}
        by_severity = {}
        resolved_count = 0

        for feedback in feedback_list:
            # Count by type
            type_key = feedback.feedback_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # Count by severity
            severity_key = feedback.severity.value
            by_severity[severity_key] = by_severity.get(severity_key, 0) + 1

            # Count resolved
            if feedback.is_resolved:
                resolved_count += 1

        unresolved_count = total_feedback - resolved_count

        # Get latest feedback
        latest_feedback = feedback_list[0] if feedback_list else None

        # Calculate average resolution time
        resolved_feedback = [
            f for f in feedback_list if f.is_resolved and f.resolved_at
        ]
        if resolved_feedback:
            total_resolution_time = sum(
                (f.resolved_at - f.created_at).total_seconds() / 3600
                for f in resolved_feedback
            )
            average_resolution_time_hours = total_resolution_time / len(
                resolved_feedback
            )
        else:
            average_resolution_time_hours = None

        return FeedbackSummary(
            target_type=target_type,
            target_id=target_id,
            total_feedback=total_feedback,
            by_type=by_type,
            by_severity=by_severity,
            resolved_count=resolved_count,
            unresolved_count=unresolved_count,
            latest_feedback=latest_feedback,
            average_resolution_time_hours=average_resolution_time_hours,
        )

    async def process_batch(
        self, feedback_ids: List[str], processor: str = "system"
    ) -> ProcessingResult:
        """Process multiple feedback items in batch."""
        start_time = datetime.utcnow()

        processed_count = 0
        errors = []
        warnings = []

        for feedback_id in feedback_ids:
            try:
                feedback = await self.get_feedback(feedback_id)
                if not feedback:
                    warnings.append(f"Feedback not found: {feedback_id}")
                    continue

                result = await self.process(feedback, processor)
                if result.success:
                    processed_count += 1
                else:
                    errors.extend(result.errors)

            except Exception as e:
                error_msg = f"Failed to process feedback {feedback_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ProcessingResult(
            success=len(errors) == 0,
            message=f"Processed {processed_count}/{len(feedback_ids)} feedback items",
            processed_items=processed_count,
            errors=errors,
            warnings=warnings,
            execution_time_ms=execution_time,
        )

    def _extract_error_info(self, content: str) -> Dict[str, Any]:
        """Extract error information from content."""
        error_info = {}

        # Look for stack traces
        if "Traceback" in content or "Exception" in content:
            error_info["has_stack_trace"] = True

        # Look for error codes
        error_codes = re.findall(r"error code:?\s*(\d+)", content, re.IGNORECASE)
        if error_codes:
            error_info["error_codes"] = error_codes

        # Look for common error patterns
        if "null pointer" in content.lower():
            error_info["error_type"] = "null_pointer"
        elif "timeout" in content.lower():
            error_info["error_type"] = "timeout"
        elif "memory" in content.lower():
            error_info["error_type"] = "memory"

        return error_info

    def _extract_metrics(self, content: str) -> Dict[str, Any]:
        """Extract performance metrics from content."""
        metrics = {}

        # Look for common metrics patterns
        # Response time
        response_times = re.findall(
            r"response time:?\s*(\d+(?:\.\d+)?)\s*ms", content, re.IGNORECASE
        )
        if response_times:
            metrics["response_time_ms"] = float(response_times[0])

        # CPU usage
        cpu_usage = re.findall(r"cpu:?\s*(\d+(?:\.\d+)?)\s*%", content, re.IGNORECASE)
        if cpu_usage:
            metrics["cpu_usage_percent"] = float(cpu_usage[0])

        # Memory usage
        memory_usage = re.findall(
            r"memory:?\s*(\d+(?:\.\d+)?)\s*(?:mb|gb)", content, re.IGNORECASE
        )
        if memory_usage:
            metrics["memory_usage"] = float(memory_usage[0])

        return metrics

    def _extract_quality_data(self, content: str) -> Dict[str, Any]:
        """Extract quality assessment data from content."""
        quality_data = {}

        # Look for scores
        scores = re.findall(r"score:?\s*(\d+(?:\.\d+)?)", content, re.IGNORECASE)
        if scores:
            quality_data["overall_score"] = float(scores[0])

        # Look for ratings
        ratings = re.findall(r"rating:?\s*(\d+)/(\d+)", content, re.IGNORECASE)
        if ratings:
            rating, max_rating = ratings[0]
            quality_data["rating"] = f"{rating}/{max_rating}"
            quality_data["normalized_rating"] = float(rating) / float(max_rating)

        return quality_data

    def _analyze_sentiment(self, content: str) -> str:
        """Simple sentiment analysis."""
        content_lower = content.lower()

        positive_words = ["good", "great", "excellent", "love", "awesome", "perfect"]
        negative_words = ["bad", "terrible", "awful", "hate", "horrible", "worst"]

        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _categorize_user_feedback(self, content: str) -> str:
        """Categorize user feedback."""
        content_lower = content.lower()

        if any(
            word in content_lower
            for word in ["feature", "enhancement", "request", "add"]
        ):
            return "feature_request"
        elif any(word in content_lower for word in ["bug", "error", "broken", "issue"]):
            return "bug_report"
        elif any(
            word in content_lower for word in ["ui", "design", "interface", "layout"]
        ):
            return "ui_feedback"
        elif any(
            word in content_lower for word in ["slow", "fast", "performance", "speed"]
        ):
            return "performance_feedback"
        else:
            return "general"

    async def _is_known_issue(self, feedback: Feedback) -> bool:
        """Check if this is a known issue."""
        # This would typically check against a knowledge base
        # For now, we'll do a simple check
        known_patterns = ["connection timeout", "database locked", "memory leak"]

        content_lower = feedback.content.lower()
        return any(pattern in content_lower for pattern in known_patterns)

    def _metrics_exceed_threshold(self, metrics: Dict[str, Any]) -> bool:
        """Check if metrics exceed acceptable thresholds."""
        thresholds = {
            "response_time_ms": 5000,  # 5 seconds
            "cpu_usage_percent": 80,  # 80%
            "memory_usage": 1024,  # 1GB
        }

        for metric, value in metrics.items():
            if metric in thresholds and value > thresholds[metric]:
                return True

        return False

    def _generate_quality_suggestions(self, quality_data: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions based on quality data."""
        suggestions = []

        overall_score = quality_data.get("overall_score", 0)
        if overall_score < 0.7:
            suggestions.append("Consider code review to improve overall quality")

        if overall_score < 0.5:
            suggestions.append("Significant refactoring may be needed")

        normalized_rating = quality_data.get("normalized_rating", 1.0)
        if normalized_rating < 0.6:
            suggestions.append("Address user satisfaction concerns")

        return suggestions

    async def _escalate_feedback(self, feedback: Feedback):
        """Escalate critical feedback."""
        feedback.metadata["escalated"] = True
        feedback.metadata["escalated_at"] = datetime.utcnow().isoformat()

        # In a real system, this would trigger notifications, create tickets, etc.
        logger.warning(f"CRITICAL FEEDBACK ESCALATED: {feedback.id} - {feedback.title}")

    async def _update_feedback(self, feedback: Feedback):
        """Update feedback in database."""
        query = """
            UPDATE feedback SET
                verification_id = $1, feedback_type = $2, severity = $3, title = $4, content = $5, source = $6,
                target_type = $7, target_id = $8, tags = $9, attachments = $10, is_resolved = $11, resolution_notes = $12,
                resolved_by = $13, resolved_at = $14, created_at = $15, updated_at = $16, metadata = $17
            WHERE id = $18
        """
        values = (
            feedback.verification_id,
            feedback.feedback_type.value,
            feedback.severity.value,
            feedback.title,
            feedback.content,
            feedback.source,
            feedback.target_type,
            feedback.target_id,
            serialize_json_field(feedback.tags),
            serialize_json_field(feedback.attachments),
            feedback.is_resolved,
            feedback.resolution_notes,
            feedback.resolved_by,
            serialize_datetime(feedback.resolved_at),
            serialize_datetime(feedback.created_at),
            serialize_datetime(feedback.updated_at),
            serialize_json_field(feedback.metadata),
            feedback.id,
        )
        await self.db_manager.execute_update(query, values)

    async def _log_processing(
        self,
        feedback_id: str,
        action: str,
        result: str,
        error_message: Optional[str] = None,
    ):
        """Log feedback processing action."""
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


    return True
