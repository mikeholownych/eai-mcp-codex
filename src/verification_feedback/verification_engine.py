"""Verification Engine business logic implementation."""

import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

from src.common.logging import get_logger
from src.common.database import (
    DatabaseManager,
    serialize_json_field,
    deserialize_json_field,
    serialize_datetime,
    deserialize_datetime,
)
from .models import (
    Verification,
    VerificationRule,
    VerificationResult,
    VerificationStatus,
    VerificationRequest,
    FeedbackSeverity,
    QualityMetrics,
)
from .config import settings

logger = get_logger("verification_engine")


class VerificationEngine:
    """Core business logic for verification processing."""

    def __init__(self, dsn: str = settings.database_url):
        self.db_manager = DatabaseManager(dsn)
        self.dsn = dsn
        self.rule_processors: Dict[str, Callable] = {
            "regex": self._process_regex_rule,
            "threshold": self._process_threshold_rule,
            "length": self._process_length_rule,
            "complexity": self._process_complexity_rule,
            "security": self._process_security_rule,
            "performance": self._process_performance_rule,
            "syntax": self._process_syntax_rule,
        }

    async def initialize_database(self):
        """Initialize database connection and create tables if they don't exist."""
        await self.db_manager.connect()
        await self._ensure_database()
        await self._load_default_rules()

    async def shutdown_database(self):
        """Shutdown database connection pool."""
        await self.db_manager.disconnect()

    async def _ensure_database(self):
        """Create database and tables if they don't exist."""
        script = """
                CREATE TABLE IF NOT EXISTS verification_rules (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    rule_type TEXT NOT NULL,
                    pattern TEXT,
                    threshold REAL,
                    parameters JSONB DEFAULT '{}',
                    is_active BOOLEAN DEFAULT TRUE,
                    severity TEXT DEFAULT 'medium',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS verifications (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    target_content TEXT,
                    status TEXT DEFAULT 'pending',
                    rules_applied JSONB DEFAULT '[]',
                    overall_score REAL,
                    passed_checks INTEGER DEFAULT 0,
                    failed_checks INTEGER DEFAULT 0,
                    total_checks INTEGER DEFAULT 0,
                    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    created_by TEXT DEFAULT 'system',
                    metadata JSONB DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS verification_results (
                    id TEXT PRIMARY KEY,
                    verification_id TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    passed BOOLEAN NOT NULL,
                    score REAL,
                    message TEXT DEFAULT '',
                    details JSONB DEFAULT '{}',
                    suggestions JSONB DEFAULT '[]',
                    evidence JSONB DEFAULT '[]',
                    execution_time_ms REAL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (verification_id) REFERENCES verifications (id) ON DELETE CASCADE,
                    FOREIGN KEY (rule_id) REFERENCES verification_rules (id) ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS idx_verifications_target ON verifications(target_type, target_id);
                CREATE INDEX IF NOT EXISTS idx_verifications_status ON verifications(status);
                CREATE INDEX IF NOT EXISTS idx_results_verification ON verification_results(verification_id);
                CREATE INDEX IF NOT EXISTS idx_rules_type ON verification_rules(rule_type);
            """
        logger.info(f"Attempting to create tables in {self.dsn}")
        await self.db_manager.execute_script(script)
        logger.info("Database tables ensured.")

    async def _load_default_rules(self):
        """Load default verification rules if none exist."""
        existing_rules = await self.get_rules()
        if existing_rules:
            return  # Rules already exist

        default_rules = [
            VerificationRule(
                id="code_length_check",
                name="Code Length Check",
                description="Ensure code blocks are not too long",
                rule_type="length",
                threshold=1000.0,
                severity=FeedbackSeverity.MEDIUM,
                parameters={"max_lines": 50},
            ),
            VerificationRule(
                id="sql_injection_check",
                name="SQL Injection Check",
                description="Detect potential SQL injection vulnerabilities",
                rule_type="security",
                pattern=r"(select|insert|update|delete|drop|create|alter)\s+.*\s*(where|from|into)",
                severity=FeedbackSeverity.HIGH,
            ),
            VerificationRule(
                id="complexity_check",
                name="Complexity Check",
                description="Check code complexity metrics",
                rule_type="complexity",
                threshold=10.0,
                severity=FeedbackSeverity.MEDIUM,
            ),
            VerificationRule(
                id="profanity_check",
                name="Profanity Check",
                description="Check for inappropriate language",
                rule_type="regex",
                pattern=r"\b(damn|hell|stupid)\b",
                severity=FeedbackSeverity.LOW,
            ),
            VerificationRule(
                id="password_in_code",
                name="Password in Code",
                description="Detect hardcoded passwords",
                rule_type="security",
                pattern=r"(password|pwd|pass)\s*=\s*['\"][^'\"]+['\"]",
                severity=FeedbackSeverity.CRITICAL,
            ),
        ]

        for rule in default_rules:
            await self.create_rule(rule)

    async def create_rule(self, rule: VerificationRule) -> VerificationRule:
        """Create a new verification rule."""
        query = """
            INSERT INTO verification_rules (
                id, name, description, rule_type, pattern, threshold, parameters,
                is_active, severity, created_at, updated_at, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """
        values = (
            rule.id,
            rule.name,
            rule.description,
            rule.rule_type,
            rule.pattern,
            rule.threshold,
            serialize_json_field(rule.parameters),
            rule.is_active,
            rule.severity.value,
            serialize_datetime(rule.created_at),
            serialize_datetime(rule.updated_at),
            serialize_json_field(rule.metadata),
        )
        await self.db_manager.execute_update(query, values)

        logger.info(f"Created verification rule: {rule.id}")
        return rule

    async def get_rules(
        self, rule_type: Optional[str] = None, active_only: bool = True
    ) -> List[VerificationRule]:
        """Get verification rules."""
        query = "SELECT * FROM verification_rules WHERE 1=1"
        params = []
        param_idx = 1

        if rule_type:
            query += f" AND rule_type = ${param_idx}"
            params.append(rule_type)
            param_idx += 1

        if active_only:
            query += f" AND is_active = ${param_idx}"
            params.append(active_only)
            param_idx += 1

        query += " ORDER BY name"

        rows = await self.db_manager.execute_query(query, tuple(params))
        return [self._row_to_rule(row) for row in rows]

    async def verify(
        self, request: VerificationRequest, created_by: str = "system"
    ) -> Verification:
        """Perform verification on the target."""
        verification_id = str(uuid.uuid4())
        now = datetime.utcnow()

        verification = Verification(
            id=verification_id,
            name=request.name,
            description=request.description,
            target_type=request.target_type,
            target_id=request.target_id,
            target_content=request.target_content,
            status=VerificationStatus.IN_PROGRESS,
            created_by=created_by,
            started_at=now,
            metadata=request.metadata,
        )

        # Get rules to apply
        rules_to_apply = []

        if request.rule_ids:
            # Use specific rules
            all_rules = await self.get_rules(active_only=True)
            rules_to_apply = [rule for rule in all_rules if rule.id in request.rule_ids]
        elif request.rule_categories:
            # Use rules from categories
            for category in request.rule_categories:
                rules_to_apply.extend(
                    await self.get_rules(rule_type=category, active_only=True)
                )
        else:
            # Use all active rules
            rules_to_apply = await self.get_rules(active_only=True)

        verification.rules_applied = [rule.id for rule in rules_to_apply]
        verification.total_checks = len(rules_to_apply)

        # Save initial verification record
        await self._save_verification(verification)

        try:
            # Apply each rule
            results = []
            for rule in rules_to_apply:
                result = self._apply_rule(rule, verification, request.parameters)
                results.append(result)

                if result.passed:
                    verification.passed_checks += 1
                else:
                    verification.failed_checks += 1

            verification.results = results

            # Calculate overall score
            if results:
                valid_scores = [r.score for r in results if r.score is not None]
                if valid_scores:
                    verification.overall_score = sum(valid_scores) / len(valid_scores)
                else:
                    verification.overall_score = 0.0

            # Determine final status
            if verification.failed_checks == 0:
                verification.status = VerificationStatus.PASSED
            elif verification.failed_checks > verification.passed_checks:
                verification.status = VerificationStatus.FAILED
            else:
                verification.status = VerificationStatus.REQUIRES_MANUAL_REVIEW

            verification.completed_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            verification.status = VerificationStatus.FAILED
            verification.completed_at = datetime.utcnow()

        finally:
            # Update verification record
            await self._save_verification(verification)

            # Save individual results
            for result in verification.results:
                await self._save_result(verification.id, result)

        logger.info(
            f"Verification completed: {verification.id} with status {verification.status}"
        )
        return verification

    def _apply_rule(
        self,
        rule: VerificationRule,
        verification: Verification,
        parameters: Dict[str, Any],
    ) -> VerificationResult:
        """Apply a single verification rule."""
        start_time = datetime.utcnow()

        result = VerificationResult(
            rule_id=rule.id,
            status=VerificationStatus.IN_PROGRESS,
            passed=False,
            message=f"Applying rule: {rule.name}",
        )

        try:
            # Get the appropriate processor
            processor = self.rule_processors.get(rule.rule_type)
            if not processor:
                raise ValueError(f"Unknown rule type: {rule.rule_type}")

            # Apply the rule
            processor(rule, verification, result, parameters)

            result.status = (
                VerificationStatus.PASSED
                if result.passed
                else VerificationStatus.FAILED
            )

        except Exception as e:
            logger.error(f"Rule {rule.id} failed: {e}")
            result.status = VerificationStatus.FAILED
            result.passed = False
            result.message = f"Rule execution failed: {str(e)}"

        # Calculate execution time
        end_time = datetime.utcnow()
        result.execution_time_ms = (end_time - start_time).total_seconds() * 1000
        result.timestamp = end_time

        return result

    def _process_regex_rule(
        self,
        rule: VerificationRule,
        verification: Verification,
        result: VerificationResult,
        params: Dict[str, Any],
    ):
        """Process regex-based rule."""
        if not rule.pattern or not verification.target_content:
            result.passed = True
            result.message = "No pattern or content to check"
            return

        try:
            matches = re.findall(
                rule.pattern, verification.target_content, re.IGNORECASE
            )

            if matches:
                result.passed = False
                result.message = f"Pattern matched {len(matches)} times"
                result.details = {"matches": matches[:10]}  # Limit to first 10 matches
                result.evidence = [f"Match: {match}" for match in matches[:5]]
                result.score = 0.0

                if rule.severity == FeedbackSeverity.CRITICAL:
                    result.suggestions.append(
                        "Immediately address this critical security issue"
                    )
                elif rule.severity == FeedbackSeverity.HIGH:
                    result.suggestions.append("Review and fix this high-priority issue")
                else:
                    result.suggestions.append("Consider addressing this issue")
            else:
                result.passed = True
                result.message = "Pattern not found"
                result.score = 1.0

        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

    def _process_threshold_rule(
        self,
        rule: VerificationRule,
        verification: Verification,
        result: VerificationResult,
        params: Dict[str, Any],
    ):
        """Process threshold-based rule."""
        if rule.threshold is None:
            result.passed = True
            result.message = "No threshold specified"
            return

        # Extract numeric value from content (this is a simplified example)
        content = verification.target_content or ""

        # For demonstration, we'll use content length
        value = len(content)

        if value > rule.threshold:
            result.passed = False
            result.message = f"Value {value} exceeds threshold {rule.threshold}"
            result.score = max(0.0, 1.0 - (value - rule.threshold) / rule.threshold)
            result.details = {"value": value, "threshold": rule.threshold}
            result.suggestions.append(f"Reduce value to below {rule.threshold}")
        else:
            result.passed = True
            result.message = f"Value {value} is within threshold {rule.threshold}"
            result.score = 1.0

    def _process_length_rule(
        self,
        rule: VerificationRule,
        verification: Verification,
        result: VerificationResult,
        params: Dict[str, Any],
    ):
        """Process length-based rule."""
        content = verification.target_content or ""

        max_lines = rule.parameters.get("max_lines", 100)
        line_count = len(content.split("\n"))

        if line_count > max_lines:
            result.passed = False
            result.message = (
                f"Content has {line_count} lines, exceeding limit of {max_lines}"
            )
            result.score = max(0.0, 1.0 - (line_count - max_lines) / max_lines)
            result.suggestions.append("Consider breaking this into smaller components")
        else:
            result.passed = True
            result.message = f"Content length ({line_count} lines) is acceptable"
            result.score = 1.0

    def _process_complexity_rule(
        self,
        rule: VerificationRule,
        verification: Verification,
        result: VerificationResult,
        params: Dict[str, Any],
    ):
        """Process complexity-based rule."""
        content = verification.target_content or ""

        # Simple complexity calculation (number of nested blocks)
        complexity = (
            content.count("{")
            + content.count("if")
            + content.count("for")
            + content.count("while")
        )
        threshold = rule.threshold or 10

        if complexity > threshold:
            result.passed = False
            result.message = (
                f"Complexity score {complexity} exceeds threshold {threshold}"
            )
            result.score = max(0.0, 1.0 - (complexity - threshold) / threshold)
            result.suggestions.append("Consider refactoring to reduce complexity")
        else:
            result.passed = True
            result.message = f"Complexity score {complexity} is acceptable"
            result.score = 1.0

    def _process_security_rule(
        self,
        rule: VerificationRule,
        verification: Verification,
        result: VerificationResult,
        params: Dict[str, Any],
    ):
        """Process security-based rule."""
        # This combines pattern matching with security-specific logic
        self._process_regex_rule(rule, verification, result, params)

        # Add security-specific suggestions
        if not result.passed:
            result.suggestions.extend(
                [
                    "Review for security vulnerabilities",
                    "Consider using parameterized queries",
                    "Validate and sanitize all inputs",
                ]
            )

    def _process_performance_rule(
        self,
        rule: VerificationRule,
        verification: Verification,
        result: VerificationResult,
        params: Dict[str, Any],
    ):
        """Process performance-based rule."""
        content = verification.target_content or ""

        # Look for performance anti-patterns
        performance_issues = []

        if "SELECT *" in content.upper():
            performance_issues.append("Avoid SELECT * queries")

        if content.count("for") > 3:  # Nested loops
            performance_issues.append("Multiple nested loops detected")

        if performance_issues:
            result.passed = False
            result.message = f"Found {len(performance_issues)} performance issues"
            result.score = max(0.0, 1.0 - len(performance_issues) * 0.2)
            result.suggestions.extend(performance_issues)
        else:
            result.passed = True
            result.message = "No obvious performance issues detected"
            result.score = 1.0

    def _process_syntax_rule(
        self,
        rule: VerificationRule,
        verification: Verification,
        result: VerificationResult,
        params: Dict[str, Any],
    ):
        """Process syntax-based rule."""
        content = verification.target_content or ""

        # Simple syntax checks (this would be more sophisticated in practice)
        syntax_errors = []

        # Check for unmatched brackets
        if content.count("{") != content.count("}"):
            syntax_errors.append("Unmatched curly braces")

        if content.count("(") != content.count(")"):
            syntax_errors.append("Unmatched parentheses")

        if content.count("[") != content.count("]"):
            syntax_errors.append("Unmatched square brackets")

        if syntax_errors:
            result.passed = False
            result.message = f"Found {len(syntax_errors)} syntax issues"
            result.score = 0.0
            result.suggestions.extend(syntax_errors)
        else:
            result.passed = True
            result.message = "No syntax errors detected"
            result.score = 1.0

    async def get_verification(self, verification_id: str) -> Optional[Verification]:
        """Get a verification by ID."""
        query = "SELECT * FROM verifications WHERE id = $1"
        row = await self.db_manager.execute_query(query, (verification_id,))

        if not row:
            return None

        return self._row_to_verification(row[0])

    async def list_verifications(
        self, target_type: Optional[str] = None, status: Optional[str] = None
    ) -> List[Verification]:
        """List verifications with optional filtering."""
        query = "SELECT * FROM verifications WHERE 1=1"
        params = []
        param_idx = 1

        if target_type:
            query += f" AND target_type = ${param_idx}"
            params.append(target_type)
            param_idx += 1

        if status:
            query += f" AND status = ${param_idx}"
            params.append(status)
            param_idx += 1

        query += " ORDER BY started_at DESC"

        rows = await self.db_manager.execute_query(query, tuple(params))
        return [self._row_to_verification(row) for row in rows]

    async def get_quality_metrics(
        self, target_type: str, target_id: str
    ) -> Optional[QualityMetrics]:
        """Get quality metrics for a target."""
        verifications = await self.list_verifications(target_type=target_type)
        target_verifications = [v for v in verifications if v.target_id == target_id]

        if not target_verifications:
            return None

        # Calculate metrics
        scores = [
            v.overall_score for v in target_verifications if v.overall_score is not None
        ]
        overall_score = sum(scores) / len(scores) if scores else 0.0

        # Get individual scores by rule type
        individual_scores = {}
        for verification in target_verifications:
            for result in verification.results:
                if result.score is not None:
                    rule = next(
                        (r for r in await self.get_rules() if r.id == result.rule_id),
                        None,
                    )
                    if rule:
                        rule_type = rule.rule_type
                        if rule_type not in individual_scores:
                            individual_scores[rule_type] = []
                        individual_scores[rule_type].append(result.score)

        # Average scores by rule type
        for rule_type in individual_scores:
            individual_scores[rule_type] = sum(individual_scores[rule_type]) / len(
                individual_scores[rule_type]
            )

        # Generate recommendations
        recommendations = []
        for rule_type, score in individual_scores.items():
            if score < 0.7:
                recommendations.append(
                    f"Improve {rule_type} quality (current score: {score:.2f})"
                )

        return QualityMetrics(
            target_type=target_type,
            target_id=target_id,
            overall_score=overall_score,
            individual_scores=individual_scores,
            recommendations=recommendations,
        )

    async def _save_verification(self, verification: Verification):
        """Save verification to database."""
        query = """
            INSERT INTO verifications (
                id, name, description, target_type, target_id, target_content, status,
                rules_applied, overall_score, passed_checks, failed_checks, total_checks,
                started_at, completed_at, created_by, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                target_type = EXCLUDED.target_type,
                target_id = EXCLUDED.target_id,
                target_content = EXCLUDED.target_content,
                status = EXCLUDED.status,
                rules_applied = EXCLUDED.rules_applied,
                overall_score = EXCLUDED.overall_score,
                passed_checks = EXCLUDED.passed_checks,
                failed_checks = EXCLUDED.failed_checks,
                total_checks = EXCLUDED.total_checks,
                started_at = EXCLUDED.started_at,
                completed_at = EXCLUDED.completed_at,
                created_by = EXCLUDED.created_by,
                metadata = EXCLUDED.metadata
        """
        values = (
            verification.id,
            verification.name,
            verification.description,
            verification.target_type,
            verification.target_id,
            verification.target_content,
            verification.status.value,
            serialize_json_field(verification.rules_applied),
            verification.overall_score,
            verification.passed_checks,
            verification.failed_checks,
            verification.total_checks,
            serialize_datetime(verification.started_at),
            serialize_datetime(verification.completed_at),
            verification.created_by,
            serialize_json_field(verification.metadata),
        )
        await self.db_manager.execute_update(query, values)

    async def _save_result(self, verification_id: str, result: VerificationResult):
        """Save verification result to database."""
        query = """
            INSERT INTO verification_results (
                id, verification_id, rule_id, status, passed, score, message,
                details, suggestions, evidence, execution_time_ms, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """
        values = (
            str(uuid.uuid4()),
            verification_id,
            result.rule_id,
            result.status.value,
            result.passed,
            result.score,
            result.message,
            serialize_json_field(result.details),
            serialize_json_field(result.suggestions),
            serialize_json_field(result.evidence),
            result.execution_time_ms,
            serialize_datetime(result.timestamp),
        )
        await self.db_manager.execute_update(query, values)

    def _row_to_rule(self, row) -> VerificationRule:
        """Convert database row to VerificationRule object."""
        return VerificationRule(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            rule_type=row["rule_type"],
            pattern=row["pattern"],
            threshold=row["threshold"],
            parameters=deserialize_json_field(row["parameters"]),
            is_active=bool(row["is_active"]),
            severity=FeedbackSeverity(row["severity"]),
            created_at=deserialize_datetime(row["created_at"]),
            updated_at=deserialize_datetime(row["updated_at"]),
            metadata=deserialize_json_field(row["metadata"]),
        )

    def _row_to_verification(self, row) -> Verification:
        """Convert database row to Verification object."""
        return Verification(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            target_type=row["target_type"],
            target_id=row["target_id"],
            target_content=row["target_content"],
            status=VerificationStatus(row["status"]),
            rules_applied=deserialize_json_field(row["rules_applied"]),
            overall_score=row["overall_score"],
            passed_checks=row["passed_checks"],
            failed_checks=row["failed_checks"],
            total_checks=row["total_checks"],
            started_at=deserialize_datetime(row["started_at"]),
            completed_at=deserialize_datetime(row["completed_at"]),
            created_by=row["created_by"],
            metadata=deserialize_json_field(row["metadata"]),
        )

    def _row_to_result(self, row) -> VerificationResult:
        """Convert database row to VerificationResult object."""
        return VerificationResult(
            rule_id=row["rule_id"],
            status=VerificationStatus(row["status"]),
            passed=bool(row["passed"]),
            score=row["score"],
            message=row["message"] or "",
            details=deserialize_json_field(row["details"]),
            suggestions=deserialize_json_field(row["suggestions"]),
            evidence=deserialize_json_field(row["evidence"]),
            execution_time_ms=row["execution_time_ms"],
            timestamp=deserialize_datetime(row["timestamp"]),
        )


# Singleton instance
_verification_engine: Optional[VerificationEngine] = None


async def get_verification_engine() -> VerificationEngine:
    """Get singleton VerificationEngine instance."""
    global _verification_engine
    if _verification_engine is None:
        _verification_engine = VerificationEngine()
        await _verification_engine.initialize_database()
    return _verification_engine


# Legacy function for backward compatibility
async def verify(feedback_id: int) -> Any:
    """Return verification results for the given feedback ID."""
    # This is a legacy function that would need to be adapted
    engine = await get_verification_engine()

    # Create a simple verification request
    request = VerificationRequest(
        name=f"Legacy Verification {feedback_id}",
        target_type="legacy",
        target_id=str(feedback_id),
        target_content="Sample content for legacy verification",
    )

    verification = await engine.verify(request)

    # Return a simplified result for backward compatibility
    from .models import Feedback

    return Feedback(
        id=str(feedback_id),
        feedback_type="system_feedback",
        title=f"Verification {verification.id}",
        content=f"Verification completed with status: {verification.status}",
    )
