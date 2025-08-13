"""
Structured logging configuration for MCP services.
Provides centralized logging setup with correlation to tracing and comprehensive formatting.
"""

import os
import sys
import json
import logging
import logging.config
from typing import Dict, Any
from datetime import datetime
import uuid
import re
from contextlib import contextmanager
import yaml

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

try:
    import loguru
    LOGURU_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False

from .tracing import get_current_span
from .trace_propagation import TracePropagationUtils

logger = logging.getLogger(__name__)


class LogSanitizer:
    """Sanitizes sensitive information from log messages."""
    
    def __init__(self):
        self.sanitization_patterns = [
            # API keys and tokens
            (r'api[_-]?key[\'"]?\s*[:=]\s*[\'"]([^\'"]+)[\'"]', 'api_key=***'),
            (r'authorization[\'"]?\s*[:=]\s*[\'"]([^\'"]+)[\'"]', 'authorization=***'),
            (r'bearer[\'"]?\s*([^\s\'"]+)', 'bearer=***'),
            (r'token[\'"]?\s*[:=]\s*[\'"]([^\'"]+)[\'"]', 'token=***'),
            
            # Passwords
            (r'password[\'"]?\s*[:=]\s*[\'"]([^\'"]+)[\'"]', 'password=***'),
            (r'passwd[\'"]?\s*[:=]\s*[\'"]([^\'"]+)[\'"]', 'passwd=***'),
            
            # Secrets
            (r'secret[\'"]?\s*[:=]\s*[\'"]([^\'"]+)[\'"]', 'secret=***'),
            (r'private[_-]?key[\'"]?\s*[:=]\s*[\'"]([^\'"]+)[\'"]', 'private_key=***'),
            
            # Personal information
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email@***'),
            (r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b', 'SSN=***'),
            (r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', 'credit_card=***'),
            
            # Database connection strings
            (r'postgresql://([^:]+):([^@]+)@', 'postgresql://user:***@'),
            (r'mysql://([^:]+):([^@]+)@', 'mysql://user:***@'),
            (r'mongodb://([^:]+):([^@]+)@', 'mongodb://user:***@'),
        ]
    
    def sanitize(self, message: str) -> str:
        """Sanitize a log message by removing sensitive information."""
        if not message:
            return message
            
        sanitized = message
        for pattern, replacement in self.sanitization_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive values in a dictionary."""
        if not isinstance(data, dict):
            return data
            
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self.sanitize(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [self.sanitize_dict(item) if isinstance(item, dict) 
                                 else self.sanitize(item) if isinstance(item, str) 
                                 else item for item in value]
            else:
                sanitized[key] = value
        
        return sanitized


class LogFormatter:
    """Formats log messages with structured data and tracing correlation."""
    
    def __init__(self, sanitizer: LogSanitizer):
        self.sanitizer = sanitizer
        self.propagation_utils = TracePropagationUtils()
    
    def add_service_info(self, logger, method_name, event_dict):
        """Add service information to log records."""
        event_dict['service'] = {
            'name': os.getenv('SERVICE_NAME', 'unknown-service'),
            'version': os.getenv('SERVICE_VERSION', '1.0.0'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'instance_id': os.getenv('HOSTNAME', 'unknown'),
        }
        return event_dict
    
    def add_tracing_info(self, logger, method_name, event_dict):
        """Add tracing correlation information to log records."""
        try:
            current_span = get_current_span()
            if current_span:
                span_context = current_span.get_span_context()
                event_dict['trace'] = {
                    'trace_id': f"{span_context.trace_id:032x}",
                    'span_id': f"{span_context.span_id:016x}",
                    'trace_flags': span_context.trace_flags,
                }
        except Exception:
            # Tracing might not be initialized
            pass
        
        return event_dict
    
    def add_request_info(self, logger, method_name, event_dict):
        """Add request correlation information to log records."""
        if 'request_id' not in event_dict:
            event_dict['request_id'] = str(uuid.uuid4())
        
        event_dict['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        return event_dict
    
    def sanitize_event_dict(self, logger, method_name, event_dict):
        """Sanitize sensitive information in log records."""
        return self.sanitizer.sanitize_dict(event_dict)
    
    def format_json(self, logger, method_name, event_dict):
        """Format log record as JSON."""
        return json.dumps(event_dict, default=str)


class StructuredLogger:
    """Centralized structured logging configuration."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config/logging.yml"
        self.config = self._load_config()
        self.sanitizer = LogSanitizer()
        self.formatter = LogFormatter(self.sanitizer)
        self._configured = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Load logging configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config.get('logging', {})
        except Exception as e:
            logger.warning(f"Failed to load logging config from {self.config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default logging configuration."""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json': {
                    '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                    'fmt': '%(asctime)s %(name)s %(levelname)s %(message)s'
                },
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'json',
                    'filename': 'logs/app.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5
                }
            },
            'loggers': {
                '': {
                    'level': 'INFO',
                    'handlers': ['console', 'file'],
                    'propagate': False
                }
            }
        }
    
    def configure_structlog(self):
        """Configure structlog for structured logging."""
        if not STRUCTLOG_AVAILABLE:
            logger.warning("structlog not available, using standard logging")
            return
        
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                self.formatter.add_service_info,
                self.formatter.add_tracing_info,
                self.formatter.add_request_info,
                self.formatter.sanitize_event_dict,
                self.formatter.format_json
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    def configure_loguru(self):
        """Configure loguru for structured logging."""
        if not LOGURU_AVAILABLE:
            logger.warning("loguru not available, using standard logging")
            return
        
        # Remove default handler
        loguru.logger.remove()
        
        # Add structured JSON handler
        loguru.logger.add(
            "logs/app.log",
            rotation="10 MB",
            retention="5 days",
            compression="zip",
            format=self._loguru_format,
            level="INFO",
            serialize=True
        )
        
        # Add console handler for development
        if os.getenv('ENVIRONMENT', 'development') == 'development':
            loguru.logger.add(
                sys.stderr,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                level="DEBUG"
            )
    
    def _loguru_format(self, record):
        """Format loguru records with structured data."""
        record['service'] = {
            'name': os.getenv('SERVICE_NAME', 'unknown-service'),
            'version': os.getenv('SERVICE_VERSION', '1.0.0'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'instance_id': os.getenv('HOSTNAME', 'unknown'),
        }
        
        # Add tracing information
        try:
            current_span = get_current_span()
            if current_span:
                span_context = current_span.get_span_context()
                record['trace'] = {
                    'trace_id': f"{span_context.trace_id:032x}",
                    'span_id': f"{span_context.span_id:016x}",
                    'trace_flags': span_context.trace_flags,
                }
        except Exception:
            pass
        
        # Add request ID
        if 'request_id' not in record:
            record['request_id'] = str(uuid.uuid4())
        
        return record
    
    def configure_standard_logging(self):
        """Configure standard Python logging."""
        logging.config.dictConfig(self.config)
    
    def initialize(self):
        """Initialize the logging system."""
        if self._configured:
            return
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure based on available libraries
        if STRUCTLOG_AVAILABLE:
            self.configure_structlog()
        elif LOGURU_AVAILABLE:
            self.configure_loguru()
        else:
            self.configure_standard_logging()
        
        self._configured = True
        logger.info("Logging system initialized")
    
    def get_logger(self, name: str = None):
        """Get a logger instance."""
        if not self._configured:
            self.initialize()
        
        if STRUCTLOG_AVAILABLE:
            return structlog.get_logger(name)
        elif LOGURU_AVAILABLE:
            return loguru.logger.bind(name=name)
        else:
            return logging.getLogger(name)
    
    @contextmanager
    def log_context(self, **context):
        """Context manager for adding temporary logging context."""
        if STRUCTLOG_AVAILABLE:
            logger = structlog.get_logger()
            with logger.bound(**context):
                yield
        elif LOGURU_AVAILABLE:
            with loguru.logger.contextualize(**context):
                yield
        else:
            # For standard logging, we can't easily add context
            yield


class LoggingManager:
    """Manages logging configuration and provides utility functions."""
    
    def __init__(self):
        self.structured_logger = StructuredLogger()
        self._initialized = False
    
    def initialize(self, config_path: str = None):
        """Initialize the logging system."""
        if self._initialized:
            return
        
        if config_path:
            self.structured_logger = StructuredLogger(config_path)
        
        self.structured_logger.initialize()
        self._initialized = True
    
    def get_logger(self, name: str = None):
        """Get a logger instance."""
        if not self._initialized:
            self.initialize()
        return self.structured_logger.get_logger(name)
    
    @contextmanager
    def log_operation(self, operation_name: str, **context):
        """Context manager for logging operations with timing."""
        logger = self.get_logger()
        start_time = datetime.utcnow()
        
        logger.info(f"Starting operation: {operation_name}", **context)
        
        try:
            with self.structured_logger.log_context(operation=operation_name, **context):
                yield
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Operation failed: {operation_name}", 
                       operation=operation_name, 
                       duration_seconds=duration,
                       error=str(e),
                       **context)
            raise
        else:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Operation completed: {operation_name}", 
                      operation=operation_name,
                      duration_seconds=duration,
                      **context)


# Global logging manager instance
_logging_manager = None


def get_logging_manager() -> LoggingManager:
    """Get the global logging manager instance."""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager


def initialize_logging(config_path: str = None):
    """Initialize the global logging system."""
    manager = get_logging_manager()
    manager.initialize(config_path)


def get_logger(name: str = None):
    """Get a logger instance."""
    manager = get_logging_manager()
    return manager.get_logger(name)


def log_operation(operation_name: str, **context):
    """Context manager for logging operations with timing."""
    manager = get_logging_manager()
    return manager.log_operation(operation_name, **context)


# Convenience functions for different log types
def log_info(message: str, **kwargs):
    """Log an info message."""
    logger = get_logger()
    logger.info(message, **kwargs)


def log_error(message: str, **kwargs):
    """Log an error message."""
    logger = get_logger()
    logger.error(message, **kwargs)


def log_warning(message: str, **kwargs):
    """Log a warning message."""
    logger = get_logger()
    logger.warning(message, **kwargs)


def log_debug(message: str, **kwargs):
    """Log a debug message."""
    logger = get_logger()
    logger.debug(message, **kwargs)


def log_critical(message: str, **kwargs):
    """Log a critical message."""
    logger = get_logger()
    logger.critical(message, **kwargs)


def log_exception(message: str, **kwargs):
    """Log an exception with traceback."""
    logger = get_logger()
    logger.exception(message, **kwargs)