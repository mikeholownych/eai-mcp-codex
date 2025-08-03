"""
Log Shipping Module for MCP Services
Provides centralized log shipping configuration and utilities for all MCP services.
"""

import os
import sys
import logging
import logging.config
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
import json
import uuid

try:
    import fluent.handler
    FLUENT_AVAILABLE = True
except ImportError:
    FLUENT_AVAILABLE = False

try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False

from .logging_config import LogSanitizer, LogFormatter, StructuredLogger
from .tracing import get_current_span

logger = logging.getLogger(__name__)


class LogShippingConfig:
    """Configuration for log shipping."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config/log-shipping.yml"
        self.config = self._load_config()
        self.fluentd_host = os.getenv('FLUENTD_HOST', 'localhost')
        self.fluentd_port = int(os.getenv('FLUENTD_PORT', '24224'))
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.service_name = os.getenv('SERVICE_NAME', 'unknown-service')
        self.service_version = os.getenv('SERVICE_VERSION', '1.0.0')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load log shipping configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load log shipping config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default log shipping configuration."""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json': {
                    'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                    'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
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
                'fluentd': {
                    'class': 'fluent.handler.FluentHandler',
                    'level': 'INFO',
                    'formatter': 'json',
                    'tag': 'mcp',
                    'host': 'localhost',
                    'port': 24224
                }
            },
            'loggers': {
                '': {
                    'level': 'INFO',
                    'handlers': ['console', 'fluentd'],
                    'propagate': False
                }
            }
        }


class LogShippingManager:
    """Manages log shipping for MCP services."""
    
    def __init__(self, config: LogShippingConfig = None):
        self.config = config or LogShippingConfig()
        self.sanitizer = LogSanitizer()
        self.formatter = LogFormatter(self.sanitizer)
        self._configured = False
        self._structured_logger = StructuredLogger()
    
    def configure_fluentd_handler(self) -> Optional[logging.Handler]:
        """Configure Fluentd handler for log shipping."""
        if not FLUENT_AVAILABLE:
            logger.warning("Fluentd handler not available, skipping log shipping")
            return None
        
        try:
            # Create Fluentd handler
            fluentd_handler = fluent.handler.FluentHandler(
                tag=f"mcp.{self.config.service_name}",
                host=self.config.fluentd_host,
                port=self.config.fluentd_port,
                timeout=3.0,
                verbose=False,
                buffer_chunk_limit=1048576,  # 1MB
                buffer_queue_limit=100,
                buffer_overflow_action='block',
                buffer_retry_limit=3,
                buffer_retry_wait=1.0,
                msgpack_kwargs={'use_bin_type': True}
            )
            
            # Set formatter
            if JSON_LOGGER_AVAILABLE:
                formatter = jsonlogger.JsonFormatter(
                    '%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S.%fZ'
                )
                fluentd_handler.setFormatter(formatter)
            
            return fluentd_handler
            
        except Exception as e:
            logger.error(f"Failed to configure Fluentd handler: {e}")
            return None
    
    def configure_file_handler(self, log_type: str = 'app') -> Optional[logging.Handler]:
        """Configure file handler for local logging."""
        try:
            # Create logs directory if it doesn't exist
            logs_dir = Path('logs')
            logs_dir.mkdir(exist_ok=True)
            
            # Create file handler
            filename = f"logs/{log_type}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                filename=filename,
                maxBytes=10485760,  # 10MB
                backupCount=10,
                encoding='utf8'
            )
            
            # Set formatter
            if JSON_LOGGER_AVAILABLE:
                formatter = jsonlogger.JsonFormatter(
                    '%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S.%fZ'
                )
                file_handler.setFormatter(formatter)
            
            return file_handler
            
        except Exception as e:
            logger.error(f"Failed to configure file handler: {e}")
            return None
    
    def configure_console_handler(self) -> Optional[logging.Handler]:
        """Configure console handler for development."""
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # Set formatter
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            return console_handler
            
        except Exception as e:
            logger.error(f"Failed to configure console handler: {e}")
            return None
    
    def configure_logging(self) -> bool:
        """Configure logging for the service."""
        if self._configured:
            return True
        
        try:
            # Load configuration
            logging.config.dictConfig(self.config.config)
            
            # Create logs directory
            Path('logs').mkdir(exist_ok=True)
            
            self._configured = True
            logger.info("Log shipping configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure logging: {e}")
            return False
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get a logger instance."""
        if not self._configured:
            self.configure_logging()
        
        return logging.getLogger(name or self.config.service_name)
    
    @contextmanager
    def log_context(self, **context):
        """Context manager for adding temporary logging context."""
        logger = self.get_logger()
        
        # Add context to log records
        old_extra = getattr(logger, 'extra', {})
        new_extra = {**old_extra, **context}
        
        try:
            logger.extra = new_extra
            yield
        finally:
            logger.extra = old_extra
    
    def log_with_context(self, level: str, message: str, **context):
        """Log a message with additional context."""
        logger = self.get_logger()
        
        # Add standard context
        context.update({
            'service_name': self.config.service_name,
            'service_version': self.config.service_version,
            'environment': self.config.environment,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'request_id': str(uuid.uuid4())
        })
        
        # Add tracing context if available
        try:
            current_span = get_current_span()
            if current_span:
                span_context = current_span.get_span_context()
                context.update({
                    'trace_id': f"{span_context.trace_id:032x}",
                    'span_id': f"{span_context.span_id:016x}",
                    'trace_flags': span_context.trace_flags
                })
        except Exception:
            pass
        
        # Sanitize context
        sanitized_context = self.sanitizer.sanitize_dict(context)
        
        # Log the message
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(message, **sanitized_context)
    
    def ship_log(self, log_data: Dict[str, Any]) -> bool:
        """Ship a log record to Fluentd."""
        if not FLUENT_AVAILABLE:
            logger.warning("Fluentd not available, cannot ship log")
            return False
        
        try:
            # Add metadata
            log_data.update({
                'service_name': self.config.service_name,
                'service_version': self.config.service_version,
                'environment': self.config.environment,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
            
            # Sanitize log data
            sanitized_data = self.sanitizer.sanitize_dict(log_data)
            
            # Send to Fluentd
            fluentd_handler = self.configure_fluentd_handler()
            if fluentd_handler:
                fluentd_handler.emit(logging.LogRecord(
                    name=self.config.service_name,
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=json.dumps(sanitized_data),
                    args=(),
                    exc_info=None
                ))
                return True
            
        except Exception as e:
            logger.error(f"Failed to ship log: {e}")
            return False
        
        return False
    
    def batch_ship_logs(self, log_records: List[Dict[str, Any]]) -> bool:
        """Ship multiple log records in batch."""
        if not FLUENT_AVAILABLE:
            logger.warning("Fluentd not available, cannot ship logs")
            return False
        
        try:
            # Process each log record
            for log_data in log_records:
                self.ship_log(log_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to batch ship logs: {e}")
            return False
    
    def create_service_logger(self, service_name: str) -> logging.Logger:
        """Create a logger for a specific service."""
        logger_name = f"mcp.{service_name}"
        return self.get_logger(logger_name)
    
    def create_performance_logger(self) -> logging.Logger:
        """Create a logger for performance metrics."""
        return self.get_logger('performance')
    
    def create_security_logger(self) -> logging.Logger:
        """Create a logger for security events."""
        return self.get_logger('security')
    
    def create_audit_logger(self) -> logging.Logger:
        """Create a logger for audit events."""
        return self.get_logger('audit')
    
    def create_error_logger(self) -> logging.Logger:
        """Create a logger for error events."""
        return self.get_logger('errors')
    
    def log_performance_metric(self, metric_name: str, value: float, **context):
        """Log a performance metric."""
        performance_logger = self.create_performance_logger()
        
        context.update({
            'metric_name': metric_name,
            'metric_value': value,
            'metric_type': 'performance'
        })
        
        self.log_with_context('info', f"Performance metric: {metric_name} = {value}", **context)
    
    def log_security_event(self, event_type: str, severity: str, **context):
        """Log a security event."""
        security_logger = self.create_security_logger()
        
        context.update({
            'security_event_type': event_type,
            'security_severity': severity,
            'event_type': 'security'
        })
        
        level = 'warning' if severity.lower() in ['medium', 'high', 'critical'] else 'info'
        self.log_with_context(level, f"Security event: {event_type}", **context)
    
    def log_audit_event(self, action: str, resource: str, result: str, **context):
        """Log an audit event."""
        audit_logger = self.create_audit_logger()
        
        context.update({
            'audit_action': action,
            'audit_resource': resource,
            'audit_result': result,
            'event_type': 'audit'
        })
        
        self.log_with_context('info', f"Audit event: {action} on {resource} - {result}", **context)
    
    def log_error(self, error: Exception, **context):
        """Log an error with exception information."""
        error_logger = self.create_error_logger()
        
        context.update({
            'error_type': type(error).__name__,
            'error_message': str(error),
            'event_type': 'error'
        })
        
        self.log_with_context('error', f"Error occurred: {str(error)}", **context)
    
    def log_business_event(self, event_name: str, **context):
        """Log a business event."""
        business_logger = self.get_logger('business')
        
        context.update({
            'business_event': event_name,
            'event_type': 'business'
        })
        
        self.log_with_context('info', f"Business event: {event_name}", **context)
    
    def log_request(self, method: str, path: str, status_code: int, duration_ms: float, **context):
        """Log an HTTP request."""
        api_logger = self.get_logger('api')
        
        context.update({
            'request_method': method,
            'request_path': path,
            'response_status': status_code,
            'request_duration_ms': duration_ms,
            'event_type': 'request'
        })
        
        level = 'error' if status_code >= 500 else 'warning' if status_code >= 400 else 'info'
        self.log_with_context(level, f"HTTP {method} {path} - {status_code} ({duration_ms}ms)", **context)
    
    def log_database_operation(self, operation: str, table: str, duration_ms: float, **context):
        """Log a database operation."""
        db_logger = self.get_logger('database')
        
        context.update({
            'db_operation': operation,
            'db_table': table,
            'operation_duration_ms': duration_ms,
            'event_type': 'database'
        })
        
        self.log_with_context('info', f"Database {operation} on {table} ({duration_ms}ms)", **context)
    
    def log_message_queue_operation(self, operation: str, queue: str, message_count: int, **context):
        """Log a message queue operation."""
        mq_logger = self.get_logger('message_queue')
        
        context.update({
            'mq_operation': operation,
            'mq_queue': queue,
            'message_count': message_count,
            'event_type': 'message_queue'
        })
        
        self.log_with_context('info', f"Message queue {operation} on {queue} ({message_count} messages)", **context)
    
    def log_llm_operation(self, model: str, operation: str, tokens_used: int, duration_ms: float, **context):
        """Log an LLM operation."""
        llm_logger = self.get_logger('llm')
        
        context.update({
            'llm_model': model,
            'llm_operation': operation,
            'tokens_used': tokens_used,
            'operation_duration_ms': duration_ms,
            'event_type': 'llm'
        })
        
        self.log_with_context('info', f"LLM {operation} with {model} ({tokens_used} tokens, {duration_ms}ms)", **context)
    
    def log_collaboration_event(self, event_type: str, participants: List[str], **context):
        """Log a collaboration event."""
        collab_logger = self.get_logger('collaboration')
        
        context.update({
            'collaboration_event_type': event_type,
            'participants': participants,
            'event_type': 'collaboration'
        })
        
        self.log_with_context('info', f"Collaboration event: {event_type} with {len(participants)} participants", **context)
    
    def log_health_check(self, service: str, status: str, **context):
        """Log a health check event."""
        health_logger = self.get_logger('health')
        
        context.update({
            'health_check_service': service,
            'health_check_status': status,
            'event_type': 'health_check'
        })
        
        level = 'error' if status != 'healthy' else 'info'
        self.log_with_context(level, f"Health check for {service}: {status}", **context)


# Global log shipping manager instance
_log_shipping_manager = None


def get_log_shipping_manager() -> LogShippingManager:
    """Get the global log shipping manager instance."""
    global _log_shipping_manager
    if _log_shipping_manager is None:
        _log_shipping_manager = LogShippingManager()
    return _log_shipping_manager


def configure_log_shipping(config_path: str = None) -> bool:
    """Configure log shipping for the application."""
    manager = get_log_shipping_manager()
    return manager.configure_logging()


def get_service_logger(service_name: str) -> logging.Logger:
    """Get a logger for a specific service."""
    manager = get_log_shipping_manager()
    return manager.create_service_logger(service_name)


def ship_log(log_data: Dict[str, Any]) -> bool:
    """Ship a log record to Fluentd."""
    manager = get_log_shipping_manager()
    return manager.ship_log(log_data)


def batch_ship_logs(log_records: List[Dict[str, Any]]) -> bool:
    """Ship multiple log records in batch."""
    manager = get_log_shipping_manager()
    return manager.batch_ship_logs(log_records)


# Convenience functions for different log types
def log_performance_metric(metric_name: str, value: float, **context):
    """Log a performance metric."""
    manager = get_log_shipping_manager()
    manager.log_performance_metric(metric_name, value, **context)


def log_security_event(event_type: str, severity: str, **context):
    """Log a security event."""
    manager = get_log_shipping_manager()
    manager.log_security_event(event_type, severity, **context)


def log_audit_event(action: str, resource: str, result: str, **context):
    """Log an audit event."""
    manager = get_log_shipping_manager()
    manager.log_audit_event(action, resource, result, **context)


def log_error(error: Exception, **context):
    """Log an error with exception information."""
    manager = get_log_shipping_manager()
    manager.log_error(error, **context)


def log_business_event(event_name: str, **context):
    """Log a business event."""
    manager = get_log_shipping_manager()
    manager.log_business_event(event_name, **context)


def log_request(method: str, path: str, status_code: int, duration_ms: float, **context):
    """Log an HTTP request."""
    manager = get_log_shipping_manager()
    manager.log_request(method, path, status_code, duration_ms, **context)


def log_database_operation(operation: str, table: str, duration_ms: float, **context):
    """Log a database operation."""
    manager = get_log_shipping_manager()
    manager.log_database_operation(operation, table, duration_ms, **context)


def log_message_queue_operation(operation: str, queue: str, message_count: int, **context):
    """Log a message queue operation."""
    manager = get_log_shipping_manager()
    manager.log_message_queue_operation(operation, queue, message_count, **context)


def log_llm_operation(model: str, operation: str, tokens_used: int, duration_ms: float, **context):
    """Log an LLM operation."""
    manager = get_log_shipping_manager()
    manager.log_llm_operation(model, operation, tokens_used, duration_ms, **context)


def log_collaboration_event(event_type: str, participants: List[str], **context):
    """Log a collaboration event."""
    manager = get_log_shipping_manager()
    manager.log_collaboration_event(event_type, participants, **context)


def log_health_check(service: str, status: str, **context):
    """Log a health check event."""
    manager = get_log_shipping_manager()
    manager.log_health_check(service, status, **context)