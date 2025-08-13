"""
Structured log validation utilities for the MCP logging framework.

Provides required-field checks, type/format validation, message quality
checks, and lightweight business rules. Designed to be fast and side-effect
free so it can run inline in hot paths.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class SeverityLevel:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    severity: str
    code: str
    message: str
    field_path: Optional[str] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LogValidator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.required_fields = self.config["required_fields"]
        self.field_rules = self.config["field_validation"]
        self.message_rules = self.config["message_validation"]
        self.business_rules = self.config["business_validation"]

    def _default_config(self) -> Dict[str, Any]:
        return {
            "required_fields": ["timestamp", "level", "message"],
            "field_validation": {
                "timestamp": {"type": "datetime", "format": "iso8601", "max_age_seconds": 300},
                "level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                },
            },
            "message_validation": {
                "max_length": 10000,
                "min_length": 1,
                "allowed_characters": r"[\x20-\x7E\r\n\t]",
            },
            "business_validation": {
                "max_field_count": 100,
                "max_nested_depth": 10,
                "check_sensitive_data": True,
            },
        }

    def validate_log_record(self, record: Dict[str, Any]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        issues += self._validate_required_fields(record)
        issues += self._validate_field_types(record)
        issues += self._validate_message(record)
        issues += self._validate_business_rules(record)
        if self.business_rules.get("check_sensitive_data", True):
            issues += self._validate_sensitive_data(record)
        return issues

    def _validate_required_fields(self, record: Dict[str, Any]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for field in self.required_fields:
            if self._get_nested(record, field) is None:
                issues.append(
                    ValidationIssue(
                        severity=SeverityLevel.ERROR,
                        code="MISSING_REQUIRED_FIELD",
                        message=f"Required field '{field}' is missing",
                        field_path=field,
                    )
                )
        return issues

    def _validate_field_types(self, record: Dict[str, Any]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for path, rules in self.field_rules.items():
            value = self._get_nested(record, path)
            if value is None:
                continue
            expected = rules.get("type")
            if expected and not self._is_type(value, expected):
                issues.append(
                    ValidationIssue(
                        severity=SeverityLevel.ERROR,
                        code="INVALID_FIELD_TYPE",
                        message=f"Field '{path}' has invalid type",
                        field_path=path,
                    )
                )
            if expected == "datetime" and rules.get("format") == "iso8601":
                if not self._is_iso8601(value):
                    issues.append(
                        ValidationIssue(
                            severity=SeverityLevel.ERROR,
                            code="INVALID_TIMESTAMP_FORMAT",
                            message=f"Field '{path}' not ISO8601",
                            field_path=path,
                        )
                    )
                else:
                    max_age = rules.get("max_age_seconds", 300)
                    if not self._is_fresh(value, max_age):
                        issues.append(
                            ValidationIssue(
                                severity=SeverityLevel.WARNING,
                                code="STALE_TIMESTAMP",
                                message=f"Field '{path}' timestamp is too old",
                                field_path=path,
                            )
                        )
            enum_vals = rules.get("enum")
            if enum_vals and isinstance(value, str) and value not in enum_vals:
                issues.append(
                    ValidationIssue(
                        severity=SeverityLevel.ERROR,
                        code="INVALID_ENUM_VALUE",
                        message=f"Field '{path}' has invalid value",
                        field_path=path,
                    )
                )
        return issues

    def _validate_message(self, record: Dict[str, Any]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        msg = record.get("message", "")
        if not isinstance(msg, str):
            return [
                ValidationIssue(
                    severity=SeverityLevel.ERROR,
                    code="INVALID_MESSAGE_TYPE",
                    message="Message must be a string",
                    field_path="message",
                )
            ]
        max_len = self.message_rules.get("max_length", 10000)
        min_len = self.message_rules.get("min_length", 1)
        if len(msg) > max_len:
            issues.append(
                ValidationIssue(
                    severity=SeverityLevel.WARNING,
                    code="MESSAGE_TOO_LONG",
                    message=f"Message length {len(msg)} > {max_len}",
                    field_path="message",
                )
            )
        if len(msg) < min_len:
            issues.append(
                ValidationIssue(
                    severity=SeverityLevel.WARNING,
                    code="MESSAGE_TOO_SHORT",
                    message=f"Message length {len(msg)} < {min_len}",
                    field_path="message",
                )
            )
        allow = self.message_rules.get("allowed_characters")
        if allow:
            invalid = re.findall(f"[^{allow}]", msg)
            if invalid:
                issues.append(
                    ValidationIssue(
                        severity=SeverityLevel.WARNING,
                        code="INVALID_CHARACTERS",
                        message="Message contains invalid characters",
                        field_path="message",
                    )
                )
        return issues

    def _validate_business_rules(self, record: Dict[str, Any]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        # Field count
        max_fields = self.business_rules.get("max_field_count", 100)
        count = self._count_fields(record)
        if count > max_fields:
            issues.append(
                ValidationIssue(
                    severity=SeverityLevel.WARNING,
                    code="TOO_MANY_FIELDS",
                    message=f"Log record has too many fields: {count}",
                )
            )
        # Nested depth
        max_depth = self.business_rules.get("max_nested_depth", 10)
        depth = self._nested_depth(record)
        if depth > max_depth:
            issues.append(
                ValidationIssue(
                    severity=SeverityLevel.WARNING,
                    code="TOO_DEEPLY_NESTED",
                    message=f"Nested depth {depth} exceeds {max_depth}",
                )
            )
        return issues

    def _validate_sensitive_data(self, record: Dict[str, Any]) -> List[ValidationIssue]:
        patterns = [
            re.compile(r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b"),  # SSN
            re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),  # CC
            re.compile(r"api_?key|password|secret", re.IGNORECASE),
        ]
        blob = json.dumps(record, default=str)
        for pat in patterns:
            if pat.search(blob):
                return [
                    ValidationIssue(
                        severity=SeverityLevel.ERROR,
                        code="SENSITIVE_DATA",
                        message="Sensitive data detected in log record",
                    )
                ]
        return []

    # ---- helpers ----
    def _get_nested(self, data: Dict[str, Any], path: str) -> Any:
        cur: Any = data
        for key in path.split("."):
            if not isinstance(cur, dict) or key not in cur:
                return None
            cur = cur[key]
        return cur

    def _is_type(self, value: Any, expected: str) -> bool:
        return (
            (expected == "string" and isinstance(value, str))
            or (expected == "number" and isinstance(value, (int, float)))
            or (expected == "datetime" and isinstance(value, str))
        )

    def _is_iso8601(self, value: str) -> bool:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except Exception:
            return False

    def _is_fresh(self, value: str, max_age_seconds: int) -> bool:
        try:
            ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return datetime.utcnow() - ts <= timedelta(seconds=max_age_seconds)
        except Exception:
            return False

    def _count_fields(self, data: Any) -> int:
        if isinstance(data, dict):
            return sum(self._count_fields(v) for v in data.values()) + len(data)
        if isinstance(data, list):
            return sum(self._count_fields(v) for v in data)
        return 1

    def _nested_depth(self, data: Any) -> int:
        if isinstance(data, dict):
            return 1 + (max([self._nested_depth(v) for v in data.values()] or [0]))
        if isinstance(data, list):
            return 1 + (max([self._nested_depth(v) for v in data] or [0]))
        return 0

