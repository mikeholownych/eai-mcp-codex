"""
Logging filters for structured logging in MCP services.
Provides various filters for log enrichment, sanitization, and correlation.
"""

import os
import logging
import uuid
import json
import time
import psutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from threading import local

from .tracing import get_current_span
from .logging_config import LogSanitizer

logger = logging.getLogger(__name__)


class TraceCorrelationFilter(logging.Filter):
    """Filter to add tracing correlation information to log records."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self._local = local()
    
    def filter(self, record):
        """Add trace correlation information to log record."""
        try:
            current_span = get_current_span()
            if current_span:
                span_context = current_span.get_span_context()
                record.trace_id = f"{span_context.trace_id:032x}"
                record.span_id = f"{span_context.span_id:016x}"
                record.trace_flags = span_context.trace_flags
            else:
                # Generate a correlation ID if no trace is available
                if not hasattr(self._local, 'correlation_id'):
                    self._local.correlation_id = str(uuid.uuid4())
                record.correlation_id = self._local.correlation_id
        except Exception:
            # Tracing might not be initialized
            if not hasattr(self._local, 'correlation_id'):
                self._local.correlation_id = str(uuid.uuid4())
            record.correlation_id = self._local.correlation_id
        
        return True


class ServiceMetadataFilter(logging.Filter):
    """Filter to add service metadata to log records."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.service_name = os.getenv('SERVICE_NAME', 'unknown-service')
        self.service_version = os.getenv('SERVICE_VERSION', '1.0.0')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.instance_id = os.getenv('HOSTNAME', 'unknown')
    
    def filter(self, record):
        """Add service metadata to log record."""
        record.service_name = self.service_name
        record.service_version = self.service_version
        record.environment = self.environment
        record.instance_id = self.instance_id
        record.timestamp = datetime.utcnow().isoformat() + 'Z'
        
        return True


class SensitiveDataFilter(logging.Filter):
    """Filter to sanitize sensitive information from log records."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.sanitizer = LogSanitizer()
    
    def filter(self, record):
        """Sanitize sensitive information in log record."""
        # Sanitize message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self.sanitizer.sanitize(record.msg)
        
        # Sanitize args if they exist
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = self.sanitizer.sanitize_dict(record.args)
            elif isinstance(record.args, (list, tuple)):
                sanitized_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        sanitized_args.append(self.sanitizer.sanitize(arg))
                    elif isinstance(arg, dict):
                        sanitized_args.append(self.sanitizer.sanitize_dict(arg))
                    else:
                        sanitized_args.append(arg)
                record.args = tuple(sanitized_args) if isinstance(record.args, tuple) else sanitized_args
        
        return True


class RequestContextFilter(logging.Filter):
    """Filter to add request context information to log records."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self._local = local()
    
    def filter(self, record):
        """Add request context to log record."""
        # Add request ID if not already present
        if not hasattr(record, 'request_id'):
            if hasattr(self._local, 'request_id'):
                record.request_id = self._local.request_id
            else:
                record.request_id = str(uuid.uuid4())
        
        # Add user context if available (with privacy considerations)
        if hasattr(self._local, 'user_id'):
            record.user_id = self._local.user_id
        
        # Add session context if available
        if hasattr(self._local, 'session_id'):
            record.session_id = self._local.session_id
        
        # Add operation context if available
        if hasattr(self._local, 'operation'):
            record.operation = self._local.operation
        
        # Add business process context if available
        if hasattr(self._local, 'business_process'):
            record.business_process = self._local.business_process
        
        # Add workflow context if available
        if hasattr(self._local, 'workflow_id'):
            record.workflow_id = self._local.workflow_id
        
        return True
    
    def set_request_context(self, request_id: str = None, user_id: str = None, 
                           session_id: str = None, operation: str = None,
                           business_process: str = None, workflow_id: str = None):
        """Set request context for the current thread."""
        if request_id:
            self._local.request_id = request_id
        if user_id:
            self._local.user_id = user_id
        if session_id:
            self._local.session_id = session_id
        if operation:
            self._local.operation = operation
        if business_process:
            self._local.business_process = business_process
        if workflow_id:
            self._local.workflow_id = workflow_id
    
    def clear_request_context(self):
        """Clear request context for the current thread."""
        if hasattr(self._local, 'request_id'):
            delattr(self._local, 'request_id')
        if hasattr(self._local, 'user_id'):
            delattr(self._local, 'user_id')
        if hasattr(self._local, 'session_id'):
            delattr(self._local, 'session_id')
        if hasattr(self._local, 'operation'):
            delattr(self._local, 'operation')
        if hasattr(self._local, 'business_process'):
            delattr(self._local, 'business_process')
        if hasattr(self._local, 'workflow_id'):
            delattr(self._local, 'workflow_id')


class PerformanceMetricsFilter(logging.Filter):
    """Filter to add performance metrics to log records."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self._start_times = {}
        self._local = local()
    
    def filter(self, record):
        """Add performance metrics to log record."""
        # Add timing information if available
        if hasattr(self._local, 'operation_start_time'):
            duration = time.time() - self._local.operation_start_time
            record.duration_seconds = duration
            record.duration_ms = duration * 1000
        
        # Add memory usage information
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            record.memory_rss_mb = memory_info.rss / 1024 / 1024
            record.memory_vms_mb = memory_info.vms / 1024 / 1024
            record.memory_percent = process.memory_percent()
        except Exception:
            # If resource stats unavailable, set safe defaults
            record.memory_rss_mb = None
            record.memory_vms_mb = None
            record.memory_percent = None
        
        # Add CPU usage information
        try:
            record.cpu_percent = psutil.cpu_percent(interval=None)
        except Exception:
            record.cpu_percent = None
        
        # Add thread count
        try:
            record.thread_count = process.num_threads()
        except Exception:
            record.thread_count = None
        
        return True
    
    def start_operation_timing(self):
        """Start timing an operation."""
        self._local.operation_start_time = time.time()
    
    def end_operation_timing(self):
        """End timing an operation."""
        if hasattr(self._local, 'operation_start_time'):
            delattr(self._local, 'operation_start_time')


class LogLevelFilter(logging.Filter):
    """Filter to route logs based on log level."""
    
    def __init__(self, name: str = "", min_level: int = logging.DEBUG, 
                 max_level: int = logging.CRITICAL):
        super().__init__(name)
        self.min_level = min_level
        self.max_level = max_level
    
    def filter(self, record):
        """Filter logs based on level."""
        return self.min_level <= record.levelno <= self.max_level


class ServiceFilter(logging.Filter):
    """Filter to route logs based on service name."""
    
    def __init__(self, name: str = "", services: List[str] = None):
        super().__init__(name)
        self.services = services or []
    
    def filter(self, record):
        """Filter logs based on service name."""
        service_name = getattr(record, 'service_name', 'unknown-service')
        return service_name in self.services


class OperationTypeFilter(logging.Filter):
    """Filter to route logs based on operation type."""
    
    def __init__(self, name: str = "", operation_types: List[str] = None):
        super().__init__(name)
        self.operation_types = operation_types or []
    
    def filter(self, record):
        """Filter logs based on operation type."""
        operation = getattr(record, 'operation', None)
        return operation in self.operation_types


class SecurityEventFilter(logging.Filter):
    """Filter to identify and route security events."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.security_keywords = [
            'authentication', 'authorization', 'login', 'logout', 'access',
            'permission', 'security', 'violation', 'breach', 'attack',
            'malicious', 'suspicious', 'unauthorized', 'forbidden'
        ]
    
    def filter(self, record):
        """Identify security events in log records."""
        message = getattr(record, 'msg', '').lower()
        
        # Check if message contains security keywords
        is_security_event = any(keyword in message for keyword in self.security_keywords)
        
        # Check if level indicates security concern
        is_security_level = record.levelno in [logging.WARNING, logging.ERROR, logging.CRITICAL]
        
        # Mark as security event
        record.is_security_event = is_security_event or is_security_level
        
        return True


class PerformanceEventFilter(logging.Filter):
    """Filter to identify and route performance events."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.performance_keywords = [
            'performance', 'slow', 'timeout', 'latency', 'duration',
            'response_time', 'throughput', 'bottleneck', 'optimization'
        ]
    
    def filter(self, record):
        """Identify performance events in log records."""
        message = getattr(record, 'msg', '').lower()
        
        # Check if message contains performance keywords
        is_performance_event = any(keyword in message for keyword in self.performance_keywords)
        
        # Check if record has duration information
        has_duration = hasattr(record, 'duration_seconds') or hasattr(record, 'duration_ms')
        
        # Mark as performance event
        record.is_performance_event = is_performance_event or has_duration
        
        return True


class BusinessEventFilter(logging.Filter):
    """Filter to identify and route business events."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.business_keywords = [
            'workflow', 'process', 'transaction', 'business', 'operation',
            'task', 'job', 'pipeline', 'collaboration', 'consensus'
        ]
    
    def filter(self, record):
        """Identify business events in log records."""
        message = getattr(record, 'msg', '').lower()
        
        # Check if message contains business keywords
        is_business_event = any(keyword in message for keyword in self.business_keywords)
        
        # Check if record has business context
        has_business_context = (
            hasattr(record, 'business_process') or
            hasattr(record, 'workflow_id') or
            hasattr(record, 'operation')
        )
        
        # Mark as business event
        record.is_business_event = is_business_event or has_business_context
        
        return True


class ErrorEventFilter(logging.Filter):
    """Filter to identify and route error events."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
    
    def filter(self, record):
        """Identify error events in log records."""
        # Mark as error event based on level
        record.is_error_event = record.levelno in [logging.ERROR, logging.CRITICAL]
        
        return True


class AuditEventFilter(logging.Filter):
    """Filter to identify and route audit events."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.audit_keywords = [
            'audit', 'compliance', 'regulation', 'policy', 'governance',
            'created', 'modified', 'deleted', 'accessed', 'approved',
            'rejected', 'reviewed', 'verified', 'validated'
        ]
    
    def filter(self, record):
        """Identify audit events in log records."""
        message = getattr(record, 'msg', '').lower()
        
        # Check if message contains audit keywords
        is_audit_event = any(keyword in message for keyword in self.audit_keywords)
        
        # Mark as audit event
        record.is_audit_event = is_audit_event
        
        return True


class LLMEventFilter(logging.Filter):
    """Filter to identify and route LLM events."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.llm_keywords = [
            'llm', 'model', 'prompt', 'completion', 'token', 'inference',
            'claude', 'gpt', 'ai', 'ml', 'machine_learning', 'generation'
        ]
    
    def filter(self, record):
        """Identify LLM events in log records."""
        message = getattr(record, 'msg', '').lower()
        
        # Check if message contains LLM keywords
        is_llm_event = any(keyword in message for keyword in self.llm_keywords)
        
        # Check if record has LLM context
        has_llm_context = (
            hasattr(record, 'model_name') or
            hasattr(record, 'prompt_tokens') or
            hasattr(record, 'completion_tokens') or
            hasattr(record, 'total_tokens')
        )
        
        # Mark as LLM event
        record.is_llm_event = is_llm_event or has_llm_context
        
        return True


class DatabaseEventFilter(logging.Filter):
    """Filter to identify and route database events."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.db_keywords = [
            'database', 'sql', 'query', 'transaction', 'connection',
            'postgresql', 'mysql', 'mongodb', 'redis', 'cache'
        ]
    
    def filter(self, record):
        """Identify database events in log records."""
        message = getattr(record, 'msg', '').lower()
        
        # Check if message contains database keywords
        is_db_event = any(keyword in message for keyword in self.db_keywords)
        
        # Check if record has database context
        has_db_context = (
            hasattr(record, 'db_operation') or
            hasattr(record, 'db_table') or
            hasattr(record, 'query_time') or
            hasattr(record, 'connection_id')
        )
        
        # Mark as database event
        record.is_database_event = is_db_event or has_db_context
        
        return True


# Global filter instances for easy access
_trace_filter = TraceCorrelationFilter()
_service_filter = ServiceMetadataFilter()
_sensitive_filter = SensitiveDataFilter()
_request_filter = RequestContextFilter()
_performance_filter = PerformanceMetricsFilter()


def get_trace_filter() -> TraceCorrelationFilter:
    """Get the global trace correlation filter."""
    return _trace_filter


def get_service_filter() -> ServiceMetadataFilter:
    """Get the global service metadata filter."""
    return _service_filter


def get_sensitive_filter() -> SensitiveDataFilter:
    """Get the global sensitive data filter."""
    return _sensitive_filter


def get_request_filter() -> RequestContextFilter:
    """Get the global request context filter."""
    return _request_filter


def get_performance_filter() -> PerformanceMetricsFilter:
    """Get the global performance metrics filter."""
    return _performance_filter


def set_request_context(request_id: str = None, user_id: str = None, 
                       session_id: str = None, operation: str = None,
                       business_process: str = None, workflow_id: str = None):
    """Set request context for the current thread."""
    _request_filter.set_request_context(
        request_id=request_id,
        user_id=user_id,
        session_id=session_id,
        operation=operation,
        business_process=business_process,
        workflow_id=workflow_id
    )


def clear_request_context():
    """Clear request context for the current thread."""
    _request_filter.clear_request_context()


def start_operation_timing():
    """Start timing an operation."""
    _performance_filter.start_operation_timing()


def end_operation_timing():
    """End timing an operation."""
    _performance_filter.end_operation_timing()
