"""Validation utilities for common data types and patterns."""

import re
import uuid
from typing import Any, Dict, List, Union
from datetime import datetime
from pathlib import Path

from .exceptions import ValidationError


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that all required fields are present in data."""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            missing_fields.append(field)

    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            details={"missing_fields": missing_fields},
        )


def validate_string_length(
    value: str, field_name: str, min_length: int = None, max_length: int = None
) -> None:
    """Validate string length constraints."""
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field=field_name)

    if min_length is not None and len(value) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters long",
            field=field_name,
            details={"current_length": len(value), "min_length": min_length},
        )

    if max_length is not None and len(value) > max_length:
        raise ValidationError(
            f"{field_name} must be at most {max_length} characters long",
            field=field_name,
            details={"current_length": len(value), "max_length": max_length},
        )


def validate_email(email: str, field_name: str = "email") -> None:
    """Validate email address format."""
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValidationError(
            f"Invalid email format for {field_name}", field=field_name
        )


def validate_uuid(value: str, field_name: str = "uuid") -> None:
    """Validate UUID format."""
    try:
        uuid.UUID(value)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid UUID format for {field_name}", field=field_name)


def validate_url(url: str, field_name: str = "url") -> None:
    """Validate URL format."""
    url_pattern = r"^https?://(?:[-\w.])+(?:\.[a-zA-Z]{2,})+(?:/.*)?$"
    if not re.match(url_pattern, url):
        raise ValidationError(f"Invalid URL format for {field_name}", field=field_name)


def validate_path(
    path: str, field_name: str = "path", must_exist: bool = False
) -> None:
    """Validate file path format and optionally existence."""
    try:
        path_obj = Path(path)

        if must_exist and not path_obj.exists():
            raise ValidationError(
                f"Path does not exist: {path}", field=field_name, details={"path": path}
            )

        # Check for path traversal attempts
        if ".." in path or path.startswith("/"):
            if not path.startswith("/tmp/") and not path.startswith("/var/"):
                raise ValidationError(
                    f"Invalid path format for {field_name}",
                    field=field_name,
                    details={"reason": "potential_path_traversal"},
                )

    except (ValueError, OSError) as e:
        raise ValidationError(
            f"Invalid path format for {field_name}: {str(e)}", field=field_name
        )


def validate_json_structure(
    data: Dict[str, Any],
    required_keys: List[str] = None,
    allowed_keys: List[str] = None,
) -> None:
    """Validate JSON structure against schema requirements."""
    if required_keys:
        validate_required_fields(data, required_keys)

    if allowed_keys:
        invalid_keys = set(data.keys()) - set(allowed_keys)
        if invalid_keys:
            raise ValidationError(
                f"Invalid keys in data: {', '.join(invalid_keys)}",
                details={
                    "invalid_keys": list(invalid_keys),
                    "allowed_keys": allowed_keys,
                },
            )


def validate_choice(value: Any, choices: List[Any], field_name: str = "value") -> None:
    """Validate that value is one of the allowed choices."""
    if value not in choices:
        raise ValidationError(
            f"Invalid choice for {field_name}. Must be one of: {', '.join(map(str, choices))}",
            field=field_name,
            details={"value": value, "choices": choices},
        )


def validate_numeric_range(
    value: Union[int, float],
    field_name: str,
    min_value: Union[int, float] = None,
    max_value: Union[int, float] = None,
) -> None:
    """Validate numeric value is within specified range."""
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a number", field=field_name)

    if min_value is not None and value < min_value:
        raise ValidationError(
            f"{field_name} must be at least {min_value}",
            field=field_name,
            details={"value": value, "min_value": min_value},
        )

    if max_value is not None and value > max_value:
        raise ValidationError(
            f"{field_name} must be at most {max_value}",
            field=field_name,
            details={"value": value, "max_value": max_value},
        )


def validate_datetime_string(
    date_string: str, field_name: str = "datetime", format_string: str = None
) -> datetime:
    """Validate and parse datetime string."""
    try:
        if format_string:
            return datetime.strptime(date_string, format_string)
        else:
            # Try ISO format first
            try:
                return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            except ValueError:
                # Fallback to common formats
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%SZ",
                ]

                for fmt in formats:
                    try:
                        return datetime.strptime(date_string, fmt)
                    except ValueError:
                        continue

                raise ValueError("No matching datetime format found")

    except (ValueError, TypeError) as e:
        raise ValidationError(
            f"Invalid datetime format for {field_name}: {str(e)}",
            field=field_name,
            details={"value": date_string},
        )


def validate_list_items(
    items: List[Any],
    field_name: str,
    item_validator: callable = None,
    min_items: int = None,
    max_items: int = None,
) -> None:
    """Validate list and optionally each item in the list."""
    if not isinstance(items, list):
        raise ValidationError(f"{field_name} must be a list", field=field_name)

    if min_items is not None and len(items) < min_items:
        raise ValidationError(
            f"{field_name} must contain at least {min_items} items",
            field=field_name,
            details={"current_count": len(items), "min_items": min_items},
        )

    if max_items is not None and len(items) > max_items:
        raise ValidationError(
            f"{field_name} must contain at most {max_items} items",
            field=field_name,
            details={"current_count": len(items), "max_items": max_items},
        )

    if item_validator:
        for i, item in enumerate(items):
            try:
                item_validator(item)
            except ValidationError as e:
                raise ValidationError(
                    f"Invalid item at index {i} in {field_name}: {e.message}",
                    field=f"{field_name}[{i}]",
                    details={"index": i, "item": item, "original_error": e.message},
                )


def validate_password_strength(password: str, field_name: str = "password") -> None:
    """Validate password meets security requirements."""
    min_length = 8

    if len(password) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters long",
            field=field_name,
        )

    # Check for at least one uppercase letter
    if not re.search(r"[A-Z]", password):
        raise ValidationError(
            f"{field_name} must contain at least one uppercase letter", field=field_name
        )

    # Check for at least one lowercase letter
    if not re.search(r"[a-z]", password):
        raise ValidationError(
            f"{field_name} must contain at least one lowercase letter", field=field_name
        )

    # Check for at least one digit
    if not re.search(r"\d", password):
        raise ValidationError(
            f"{field_name} must contain at least one digit", field=field_name
        )

    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError(
            f"{field_name} must contain at least one special character",
            field=field_name,
        )


def validate_api_token(token: str, field_name: str = "token") -> None:
    """Validate API token format."""
    if not token:
        raise ValidationError(f"{field_name} cannot be empty", field=field_name)

    if len(token) < 32:
        raise ValidationError(
            f"{field_name} must be at least 32 characters long", field=field_name
        )

    # Check for valid characters (alphanumeric + some special chars)
    if not re.match(r"^[a-zA-Z0-9\-_\.]+$", token):
        raise ValidationError(
            f"{field_name} contains invalid characters", field=field_name
        )


class ValidationSchema:
    """Class-based validation schema for complex data validation."""

    def __init__(self):
        self.rules = {}

    def add_field(
        self,
        field_name: str,
        required: bool = False,
        validator: callable = None,
        **kwargs,
    ) -> "ValidationSchema":
        """Add a field validation rule."""
        self.rules[field_name] = {
            "required": required,
            "validator": validator,
            "kwargs": kwargs,
        }
        return self

    def validate(self, data: Dict[str, Any]) -> None:
        """Validate data against the schema."""
        # Check required fields
        required_fields = [
            field for field, rule in self.rules.items() if rule["required"]
        ]
        validate_required_fields(data, required_fields)

        # Validate each field
        for field_name, rule in self.rules.items():
            if field_name in data:
                value = data[field_name]
                validator = rule["validator"]

                if validator:
                    try:
                        validator(value, field_name, **rule["kwargs"])
                    except ValidationError:
                        raise
                    except Exception as e:
                        raise ValidationError(
                            f"Validation failed for {field_name}: {str(e)}",
                            field=field_name,
                        )


# Pre-defined validation schemas
def create_user_validation_schema() -> ValidationSchema:
    """Create validation schema for user data."""
    return (
        ValidationSchema()
        .add_field(
            "username",
            required=True,
            validator=validate_string_length,
            min_length=3,
            max_length=50,
        )
        .add_field("email", required=True, validator=validate_email)
        .add_field("password", required=True, validator=validate_password_strength)
    )


def create_task_validation_schema() -> ValidationSchema:
    """Create validation schema for task data."""
    return (
        ValidationSchema()
        .add_field(
            "title",
            required=True,
            validator=validate_string_length,
            min_length=1,
            max_length=200,
        )
        .add_field(
            "description",
            required=False,
            validator=validate_string_length,
            max_length=1000,
        )
        .add_field(
            "priority",
            required=False,
            validator=validate_choice,
            choices=["low", "medium", "high"],
        )
        .add_field("due_date", required=False, validator=validate_datetime_string)
    )
