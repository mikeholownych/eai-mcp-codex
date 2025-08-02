"""Logging configuration utilities with structured JSON support for Loki."""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging compatible with Loki."""
    
    def __init__(self, service_name: str = None):
        super().__init__()
        self.service_name = service_name or os.getenv("SERVICE_NAME", "unknown")
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "service_name": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class StandardFormatter(logging.Formatter):
    """Standard text formatter for development."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging(service_name: str = None, json_logs: bool = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        service_name: Name of the service for structured logging
        json_logs: Whether to use JSON formatting (defaults to LOG_FORMAT env var)
    """
    if json_logs is None:
        json_logs = os.getenv("LOG_FORMAT", "json").lower() == "json"
    
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)
    
    # Clear any existing handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter based on configuration
    if json_logs:
        formatter = JSONFormatter(service_name)
    else:
        formatter = StandardFormatter()
    
    handler.setFormatter(formatter)
    
    # Configure root logger
    root.setLevel(level)
    root.addHandler(handler)
    
    # Disable library loggers in production
    if json_logs:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str, extra_fields: Dict[str, Any] = None) -> logging.LoggerAdapter:
    """
    Return a configured logger instance with optional extra fields.
    
    Args:
        name: Logger name
        extra_fields: Additional fields to include in all log messages
    
    Returns:
        LoggerAdapter with extra fields
    """
    logger = logging.getLogger(name)
    if extra_fields:
        return logging.LoggerAdapter(logger, extra_fields)
    return logging.LoggerAdapter(logger, {})


def get_service_logger(service_name: str, request_id: str = None) -> logging.LoggerAdapter:
    """
    Get a logger configured for a specific service with request context.
    
    Args:
        service_name: Name of the service
        request_id: Optional request ID for tracing
    
    Returns:
        LoggerAdapter with service context
    """
    extra = {"service": service_name}
    if request_id:
        extra["request_id"] = request_id
    
    return get_logger(service_name, extra)


# Initialize logging on import
setup_logging()
