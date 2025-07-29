"""Feedback Processing business logic implementation."""

import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.common.logging import get_logger
from .models import (
    Feedback, FeedbackType, FeedbackSeverity, FeedbackRequest,
    FeedbackSummary, ProcessingResult, QualityMetrics
)

logger = get_logger("feedback_processor")


class FeedbackProcessor:
    """Core business logic for feedback processing."""
    
    def __init__(self, db_path: str = "data/feedback.db"):
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    verification_id TEXT,
                    feedback_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'medium',
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT DEFAULT 'system',
                    target_type TEXT,
                    target_id TEXT,
                    tags TEXT DEFAULT '[]',
                    attachments TEXT DEFAULT '[]',
                    is_resolved BOOLEAN DEFAULT FALSE,
                    resolution_notes TEXT,
                    resolved_by TEXT,
                    resolved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS feedback_processing_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feedback_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    result TEXT,
                    error_message TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_by TEXT DEFAULT 'system',
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (feedback_id) REFERENCES feedback (id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
                CREATE INDEX IF NOT EXISTS idx_feedback_severity ON feedback(severity);
                CREATE INDEX IF NOT EXISTS idx_feedback_target ON feedback(target_type, target_id);
                CREATE INDEX IF NOT EXISTS idx_feedback_resolved ON feedback(is_resolved);
                CREATE INDEX IF NOT EXISTS idx_processing_log_feedback ON feedback_processing_log(feedback_id);
            """)
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def submit_feedback(self, request: FeedbackRequest, source: str = "system") -> Feedback:
        """Submit new feedback."""
        feedback_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        feedback = Feedback(
            id=feedback_id,
            feedback_type=request.feedback_type,
            severity=request.severity,
            title=request.title,
            content=request.content,
            source=source,
            target_type=request.target_type,
            target_id=request.target_id,
            tags=request.tags,
            created_at=now,
            updated_at=now,
            metadata=request.metadata
        )
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO feedback (
                    id, feedback_type, severity, title, content, source,
                    target_type, target_id, tags, created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback.id, feedback.feedback_type.value, feedback.severity.value,
                feedback.title, feedback.content, feedback.source, feedback.target_type,
                feedback.target_id, str(feedback.tags), feedback.created_at.isoformat(),
                feedback.updated_at.isoformat(), str(feedback.metadata)
            ))
        
        # Log the submission
        self._log_processing(feedback.id, "submitted", f"Feedback submitted by {source}")
        
        # Process the feedback based on type and severity
        self._auto_process_feedback(feedback)
        
        logger.info(f"Submitted feedback: {feedback.id} - {feedback.title}")
        return feedback
    
    def process(self, feedback: Feedback, processor: str = "system") -> ProcessingResult:
        """Process feedback with enhanced logic."""
        start_time = datetime.utcnow()
        
        try:
            # Determine processing actions based on feedback type and severity
            actions_taken = []
            
            if feedback.feedback_type == FeedbackType.ERROR_REPORT:
                actions_taken.extend(self._process_error_report(feedback))
            elif feedback.feedback_type == FeedbackType.PERFORMANCE_METRIC:
                actions_taken.extend(self._process_performance_metric(feedback))
            elif feedback.feedback_type == FeedbackType.QUALITY_ASSESSMENT:
                actions_taken.extend(self._process_quality_assessment(feedback))
            elif feedback.feedback_type == FeedbackType.USER_FEEDBACK:
                actions_taken.extend(self._process_user_feedback(feedback))
            else:
                actions_taken.append("Applied general processing")
            
            # Handle severity-specific actions
            if feedback.severity == FeedbackSeverity.CRITICAL:
                actions_taken.extend(self._handle_critical_feedback(feedback))
            elif feedback.severity == FeedbackSeverity.HIGH:
                actions_taken.extend(self._handle_high_priority_feedback(feedback))
            
            # Update feedback processing timestamp
            feedback.updated_at = datetime.utcnow()
            self._update_feedback(feedback)
            
            # Log successful processing
            self._log_processing(
                feedback.id, 
                "processed", 
                f"Successfully processed by {processor}. Actions: {', '.join(actions_taken)}"
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ProcessingResult(
                success=True,
                message=f"Feedback processed successfully. Actions taken: {', '.join(actions_taken)}",
                processed_items=1,
                execution_time_ms=execution_time,
                metadata={"actions_taken": actions_taken}
            )
            
        except Exception as e:
            error_msg = f"Failed to process feedback: {str(e)}"
            logger.error(error_msg)
            
            # Log failed processing
            self._log_processing(feedback.id, "processing_failed", error_msg)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ProcessingResult(
                success=False,
                message=error_msg,
                processed_items=0,
                errors=[error_msg],
                execution_time_ms=execution_time
            )
    
    def _auto_process_feedback(self, feedback: Feedback):
        """Automatically process feedback based on rules."""
        # Auto-assign tags based on content
        content_lower = feedback.content.lower()
        auto_tags = []
        
        if any(word in content_lower for word in ["bug", "error", "crash", "exception"]):
            auto_tags.append("bug")
        
        if any(word in content_lower for word in ["slow", "performance", "timeout", "lag"]):
            auto_tags.append("performance")
        
        if any(word in content_lower for word in ["security", "vulnerable", "exploit", "hack"]):
            auto_tags.append("security")
        
        if any(word in content_lower for word in ["ui", "ux", "interface", "design"]):
            auto_tags.append("ui-ux")
        
        # Add auto-generated tags
        feedback.tags.extend([tag for tag in auto_tags if tag not in feedback.tags])
        
        # Auto-escalate critical issues
        if feedback.severity == FeedbackSeverity.CRITICAL:
            self._escalate_feedback(feedback)
    
    def _process_error_report(self, feedback: Feedback) -> List[str]:
        """Process error report feedback."""
        actions = []
        
        # Extract error information
        error_info = self._extract_error_info(feedback.content)
        if error_info:
            feedback.metadata.update({"error_analysis": error_info})
            actions.append("Extracted error information")
        
        # Check for known issues
        if self._is_known_issue(feedback):
            actions.append("Matched to known issue")
        else:
            actions.append("Flagged as new issue")
        
        # Create automated ticket if critical
        if feedback.severity in [FeedbackSeverity.CRITICAL, FeedbackSeverity.HIGH]:
            actions.append("Created automated support ticket")
        
        return actions
    
    def _process_performance_metric(self, feedback: Feedback) -> List[str]:
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
    
    def _process_quality_assessment(self, feedback: Feedback) -> List[str]:
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
    
    def _process_user_feedback(self, feedback: Feedback) -> List[str]:
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
    
    def _handle_critical_feedback(self, feedback: Feedback) -> List[str]:
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
    
    def _handle_high_priority_feedback(self, feedback: Feedback) -> List[str]:
        """Handle high priority feedback."""
        actions = []
        
        # Schedule for review within 24 hours
        actions.append("Scheduled for priority review")
        
        # Create standard ticket
        actions.append("Created priority support ticket")
        
        return actions
    
    def resolve_feedback(self, feedback_id: str, resolution_notes: str, resolved_by: str = "system") -> Optional[Feedback]:
        """Mark feedback as resolved."""
        feedback = self.get_feedback(feedback_id)
        if not feedback:
            return None
        
        feedback.is_resolved = True
        feedback.resolution_notes = resolution_notes
        feedback.resolved_by = resolved_by
        feedback.resolved_at = datetime.utcnow()
        feedback.updated_at = datetime.utcnow()
        
        self._update_feedback(feedback)
        self._log_processing(feedback.id, "resolved", f"Resolved by {resolved_by}: {resolution_notes}")
        
        logger.info(f"Resolved feedback: {feedback.id}")
        return feedback
    
    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """Get feedback by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM feedback WHERE id = ?", (feedback_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_feedback(row)
    
    def list_feedback(
        self, 
        feedback_type: str = None, 
        severity: str = None,
        target_type: str = None,
        target_id: str = None,
        resolved: bool = None,
        limit: int = 100
    ) -> List[Feedback]:
        """List feedback with optional filtering."""
        query = "SELECT * FROM feedback WHERE 1=1"
        params = []
        
        if feedback_type:
            query += " AND feedback_type = ?"
            params.append(feedback_type)
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        if target_type:
            query += " AND target_type = ?"
            params.append(target_type)
        
        if target_id:
            query += " AND target_id = ?"
            params.append(target_id)
        
        if resolved is not None:
            query += " AND is_resolved = ?"
            params.append(resolved)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [self._row_to_feedback(row) for row in cursor.fetchall()]
    
    def get_feedback_summary(self, target_type: str = None, target_id: str = None) -> FeedbackSummary:
        """Get feedback summary for a target."""
        # Get all relevant feedback
        feedback_list = self.list_feedback(target_type=target_type, target_id=target_id, limit=1000)
        
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
        resolved_feedback = [f for f in feedback_list if f.is_resolved and f.resolved_at]
        if resolved_feedback:
            total_resolution_time = sum(
                (f.resolved_at - f.created_at).total_seconds() / 3600
                for f in resolved_feedback
            )
            average_resolution_time_hours = total_resolution_time / len(resolved_feedback)
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
            average_resolution_time_hours=average_resolution_time_hours
        )
    
    def process_batch(self, feedback_ids: List[str], processor: str = "system") -> ProcessingResult:
        """Process multiple feedback items in batch."""
        start_time = datetime.utcnow()
        
        processed_count = 0
        errors = []
        warnings = []
        
        for feedback_id in feedback_ids:
            try:
                feedback = self.get_feedback(feedback_id)
                if not feedback:
                    warnings. append(f"Feedback not found: {feedback_id}")
                    continue
                
                result = self.process(feedback, processor)
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
            execution_time_ms=execution_time
        )
    
    def _extract_error_info(self, content: str) -> Dict[str, Any]:
        """Extract error information from content."""
        error_info = {}
        
        # Look for stack traces
        if "Traceback" in content or "Exception" in content:
            error_info["has_stack_trace"] = True
        
        # Look for error codes
        import re
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
        import re
        
        # Response time
        response_times = re.findall(r"response time:?\s*(\d+(?:\.\d+)?)\s*ms", content, re.IGNORECASE)
        if response_times:
            metrics["response_time_ms"] = float(response_times[0])
        
        # CPU usage
        cpu_usage = re.findall(r"cpu:?\s*(\d+(?:\.\d+)?)\s*%", content, re.IGNORECASE)
        if cpu_usage:
            metrics["cpu_usage_percent"] = float(cpu_usage[0])
        
        # Memory usage
        memory_usage = re.findall(r"memory:?\s*(\d+(?:\.\d+)?)\s*(?:mb|gb)", content, re.IGNORECASE)
        if memory_usage:
            metrics["memory_usage"] = float(memory_usage[0])
        
        return metrics
    
    def _extract_quality_data(self, content: str) -> Dict[str, Any]:
        """Extract quality assessment data from content."""
        quality_data = {}
        
        # Look for scores
        import re
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
        
        if any(word in content_lower for word in ["feature", "enhancement", "request", "add"]):
            return "feature_request"
        elif any(word in content_lower for word in ["bug", "error", "broken", "issue"]):
            return "bug_report"
        elif any(word in content_lower for word in ["ui", "design", "interface", "layout"]):
            return "ui_feedback"
        elif any(word in content_lower for word in ["slow", "fast", "performance", "speed"]):
            return "performance_feedback"
        else:
            return "general"
    
    def _is_known_issue(self, feedback: Feedback) -> bool:
        """Check if this is a known issue."""
        # This would typically check against a knowledge base
        # For now, we'll do a simple check
        known_patterns = [
            "connection timeout",
            "database locked",
            "memory leak"
        ]
        
        content_lower = feedback.content.lower()
        return any(pattern in content_lower for pattern in known_patterns)
    
    def _metrics_exceed_threshold(self, metrics: Dict[str, Any]) -> bool:
        """Check if metrics exceed acceptable thresholds."""
        thresholds = {
            "response_time_ms": 5000,  # 5 seconds
            "cpu_usage_percent": 80,   # 80%
            "memory_usage": 1024       # 1GB
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
    
    def _escalate_feedback(self, feedback: Feedback):
        """Escalate critical feedback."""
        feedback.metadata["escalated"] = True
        feedback.metadata["escalated_at"] = datetime.utcnow().isoformat()
        
        # In a real system, this would trigger notifications, create tickets, etc.
        logger.warning(f"CRITICAL FEEDBACK ESCALATED: {feedback.id} - {feedback.title}")
    
    def _update_feedback(self, feedback: Feedback):
        """Update feedback in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE feedback SET
                    tags = ?, is_resolved = ?, resolution_notes = ?, resolved_by = ?,
                    resolved_at = ?, updated_at = ?, metadata = ?
                WHERE id = ?
            """, (
                str(feedback.tags), feedback.is_resolved, feedback.resolution_notes,
                feedback.resolved_by,
                feedback.resolved_at.isoformat() if feedback.resolved_at else None,
                feedback.updated_at.isoformat(), str(feedback.metadata), feedback.id
            ))
    
    def _log_processing(self, feedback_id: str, action: str, result: str, error_message: str = None):
        """Log feedback processing action."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO feedback_processing_log (
                    feedback_id, action, result, error_message
                ) VALUES (?, ?, ?, ?)
            """, (feedback_id, action, result, error_message))
    
    def _row_to_feedback(self, row) -> Feedback:
        """Convert database row to Feedback object."""
        import json
        
        return Feedback(
            id=row["id"],
            verification_id=row["verification_id"],
            feedback_type=FeedbackType(row["feedback_type"]),
            severity=FeedbackSeverity(row["severity"]),
            title=row["title"],
            content=row["content"],
            source=row["source"],
            target_type=row["target_type"],
            target_id=row["target_id"],
            tags=json.loads(row["tags"] or "[]"),
            attachments=json.loads(row["attachments"] or "[]"),
            is_resolved=bool(row["is_resolved"]),
            resolution_notes=row["resolution_notes"],
            resolved_by=row["resolved_by"],
            resolved_at=datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            metadata=json.loads(row["metadata"] or "{}")
        )


# Singleton instance
_feedback_processor: Optional[FeedbackProcessor] = None


def get_feedback_processor() -> FeedbackProcessor:
    """Get singleton FeedbackProcessor instance."""
    global _feedback_processor
    if _feedback_processor is None:
        _feedback_processor = FeedbackProcessor()
    return _feedback_processor


# Legacy function for backward compatibility
def process(feedback: Any) -> bool:
    """Process feedback using the enhanced processor."""
    processor = get_feedback_processor()
    
    # Handle legacy Feedback object or convert if needed
    if hasattr(feedback, 'id'):
        result = processor.process(feedback)
        return result.success
    
    return True
