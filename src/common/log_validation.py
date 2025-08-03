"""
Log validation utilities for the MCP structured logging framework.
Provides comprehensive validation for structured log records, health checking,
and quality scoring.
"""

import re
import json
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics
import psutil

from .logging_config import LogSanitizer
from .tracing import get_current_span

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue with severity and details."""
    severity: SeverityLevel
    code: str
    message: str
    field_path: Optional[str] = None
    suggestion: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation issue to dictionary for serialization."""
        result = asdict(self)
        result['severity'] = self.severity.value
        return result


class LogValidator:
    """Validates structured log records against defined schemas and rules."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize log validator with configuration."""
        self.config = config or self._get_default_config()
        self.sanitizer = LogSanitizer()
        self.validation_stats = defaultdict(int)
        
        # Initialize validation patterns
        self._init_validation_patterns()
        
        # Initialize required fields
        self.required_fields = self.config.get('required_fields', [
            'timestamp', 'level', 'message'
        ])
        
        # Initialize field validation rules
        self.field_validation_rules = self.config.get('field_validation', {})
        
        # Initialize message validation rules
        self.message_validation_rules = self.config.get('message_validation', {})
        
        # Initialize business validation rules
        self.business_validation_rules = self.config.get('business_validation', {})
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default validation configuration."""
        return {
            'required_fields': ['timestamp', 'level', 'message'],
            'field_validation': {
                'timestamp': {
                    'type': 'datetime',
                    'format': 'iso8601',
                    'max_age_seconds': 300  # 5 minutes
                },
                'level': {
                    'type': 'string',
                    'enum': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
                },
                'trace.trace_id': {
                    'type': 'string',
                    'pattern': '^[0-9a-f]{32}$'
                },
                'trace.span_id': {
                    'type': 'string',
                    'pattern': '^[0-9a-f]{16}$'
                }
            },
            'message_validation': {
                'max_length': 10000,
                'min_length': 1,
                'allowed_characters': r'[\x20-\x7E\r\n\t]'
            },
            'business_validation': {
                'max_field_count': 100,
                'max_nested_depth': 10,
                'check_sensitive_data': True,
                'check_performance_metrics': True
            }
        }
    
    def _init_validation_patterns(self):
        """Initialize validation patterns and regexes."""
        self.patterns = {
            'iso8601_timestamp': re.compile(
                r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$'
            ),
            'trace_id': re.compile(r'^[0-9a-f]{32}$'),
            'span_id': re.compile(r'^[0-9a-f]{16}$'),
            'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'credit_card': re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b')
        }
    
    def validate_log_record(self, log_record: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate a structured log record against all rules."""
        issues = []
        
        # Validate required fields
        issues.extend(self._validate_required_fields(log_record))
        
        # Validate field types and formats
        issues.extend(self._validate_field_types(log_record))
        
        # Validate quality rules
        issues.extend(self._validate_quality_rules(log_record))
        
        # Validate business rules
        issues.extend(self._validate_business_rules(log_record))
        
        # Check for sensitive data exposure
        issues.extend(self._validate_sensitive_data(log_record))
        
        # Update validation statistics
        self._update_validation_stats(issues)
        
        return issues
    
    def _validate_required_fields(self, log_record: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate that all required fields are present."""
        issues = []
        
        for field in self.required_fields:
            if not self._get_nested_value(log_record, field):
                issues.append(ValidationIssue(
                    severity=SeverityLevel.ERROR,
                    code="MISSING_REQUIRED_FIELD",
                    message=f"Required field '{field}' is missing",
                    field_path=field,
                    suggestion="Add the required field to the log record"
                ))
        
        return issues
    
    def _validate_field_types(self, log_record: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate field types and formats."""
        issues = []
        
        for field_path, rules in self.field_validation_rules.items():
            field_value = self._get_nested_value(log_record, field_path)
            
            if field_value is None:
                continue
            
            # Validate type
            expected_type = rules.get('type')
            if expected_type and not self._validate_type(field_value, expected_type):
                issues.append(ValidationIssue(
                    severity=SeverityLevel.ERROR,
                    code="INVALID_FIELD_TYPE",
                    message=f"Field '{field_path}' has invalid type. Expected {expected_type}",
                    field_path=field_path,
                    suggestion=f"Convert field value to {expected_type} type"
                ))
            
            # Validate format
            if expected_type == 'datetime' and rules.get('format') == 'iso8601':
                if not self._validate_iso8601_timestamp(field_value):
                    issues.append(ValidationIssue(
                        severity=SeverityLevel.ERROR,
                        code="INVALID_TIMESTAMP_FORMAT",
                        message=f"Field '{field_path}' has invalid ISO8601 timestamp format",
                        field_path=field_path,
                        suggestion="Use ISO8601 format: YYYY-MM-DDTHH:MM:SS.sssZ"
                    ))
                
                # Check timestamp freshness
                max_age = rules.get('max_age_seconds', 300)
                if not self._validate_timestamp_freshness(field_value, max_age):
                    issues.append(ValidationIssue(
                        severity=SeverityLevel.WARNING,
                        code="STALE_TIMESTAMP",
                        message=f"Field '{field_path}' timestamp is too old",
                        field_path=field_path,
                        suggestion="Ensure logs are generated in near real-time"
                    ))
            
            # Validate pattern
            pattern = rules.get('pattern')
            if pattern and isinstance(field_value, str):
                if not re.match(pattern, field_value):
                    issues.append(ValidationIssue(
                        severity=SeverityLevel.ERROR,
                        code="INVALID_FIELD_PATTERN",
                        message=f"Field '{field_path}' does not match required pattern",
                        field_path=field_path,
                        suggestion=f"Ensure field value matches pattern: {pattern}"
                    ))
            
            # Validate enum values
            enum_values = rules.get('enum')
            if enum_values and isinstance(field_value, str):
                if field_value not in enum_values:
                    issues.append(ValidationIssue(
                        severity=SeverityLevel.ERROR,
                        code="INVALID_ENUM_VALUE",
                        message=f"Field '{field_path}' has invalid enum value",
                        field_path=field_path,
                        suggestion=f"Use one of: {', '.join(enum_values)}"
                    ))
        
        return issues
    
    def _validate_quality_rules(self, log_record: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate quality rules for log records."""
        issues = []
        
        # Validate message
        message = log_record.get('message', '')
        if message:
            # Check message length
            max_length = self.message_validation_rules.get('max_length', 10000)
            min_length = self.message_validation_rules.get('min_length', 1)
            
            if len(message) > max_length:
                issues.append(ValidationIssue(
                    severity=SeverityLevel.WARNING,
                    code="MESSAGE_TOO_LONG",
                    message=f"Message is too long ({len(message)} > {max_length} characters)",
                    field_path='message',
                    suggestion="Truncate or summarize long messages"
                ))
            
            if len(message) < min_length:
                issues.append(ValidationIssue(
                    severity=SeverityLevel.WARNING,
                    code="MESSAGE_TOO_SHORT",
                    message=f"Message is too short ({len(message)} < {min_length} characters)",
                    field_path='message',
                    suggestion="Provide more descriptive log messages"
                ))
            
            # Check allowed characters
            allowed_pattern = self.message_validation_rules.get('allowed_characters')
            if allowed_pattern:
                invalid_chars = re.findall(f'[^{allowed_pattern}]', message)
                if invalid_chars:
                    issues.append(ValidationIssue(
                        severity=SeverityLevel.WARNING,
                        code="INVALID_CHARACTERS",
                        message=f"Message contains invalid characters: {set(invalid_chars)}",
                        field_path='message',
                        suggestion="Remove or escape invalid characters"
                    ))
        
        # Validate field count
        max_field_count = self.business_validation_rules.get('max_field_count', 100)
        field_count = self._count_fields(log_record)
        if field_count > max_field_count:
            issues.append(ValidationIssue(
                severity=SeverityLevel.WARNING,
                code="TOO_MANY_FIELDS",
                message=f"Log record has too many fields ({field_count} > {max_field_count})",
                suggestion="Reduce the number of fields or use structured nesting"
            ))
        
        # Validate nested depth
        max_nested_depth = self.business_validation_rules.get('max_nested_depth', 10)
        nested_depth = self._calculate_nested_depth(log_record)
                            code="STALE_TIMESTAMP",
                            message=f"Log timestamp is {age:.0f} seconds old",
                            severity=ValidationSeverity.WARNING,
                            field_path="timestamp"
                        ))
                    elif age < 0:
                        issues.append(ValidationIssue(
                            code="FUTURE_TIMESTAMP",
                            message="Log timestamp is in the future",
                            severity=ValidationSeverity.ERROR,
                            field_path="timestamp"
                        ))
            except (ValueError, TypeError):
                # Already handled by field validation
                pass
        
        # Validate performance metrics
        if "duration_ms" in record:
            duration = record["duration_ms"]
            if isinstance(duration, (int, float)) and duration < 0:
                issues.append(ValidationIssue(
                    code="NEGATIVE_DURATION",
                    message="Duration cannot be negative",
                    severity=ValidationSeverity.ERROR,
                    field_path="duration_ms"
                ))
        
        # Validate memory usage
        if "memory_usage_mb" in record:
            memory = record["memory_usage_mb"]
            if isinstance(memory, (int, float)) and memory < 0:
                issues.append(ValidationIssue(
                    code="NEGATIVE_MEMORY",
                    message="Memory usage cannot be negative",
                    severity=ValidationSeverity.ERROR,
                    field_path="memory_usage_mb"
                ))
            elif isinstance(memory, (int, float)) and memory > 1024 * 1024:  # 1TB
                issues.append(ValidationIssue(
                    code="EXCESSIVE_MEMORY",
                    message="Memory usage seems unusually high",
                    severity=ValidationSeverity.WARNING,
                    field_path="memory_usage_mb"
                ))
        
        # Validate CPU usage
        if "cpu_usage_percent" in record:
            cpu = record["cpu_usage_percent"]
            if isinstance(cpu, (int, float)) and (cpu < 0 or cpu > 100):
                issues.append(ValidationIssue(
