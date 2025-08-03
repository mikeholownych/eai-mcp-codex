"""
Trace sampling and filtering utilities for MCP services.
Provides adaptive sampling, privacy-conscious filtering, and trace retention policies.
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Union
from contextlib import contextmanager, asynccontextmanager
import asyncio
import time
import re
import hashlib
import json
from dataclasses import dataclass
from enum import Enum

from opentelemetry import trace, context
from opentelemetry.trace import (
    Span, 
    SpanKind, 
    Status, 
    StatusCode,
    SamplingResult,
    Decision,
    TraceState
)
from opentelemetry.sdk.trace.sampling import Sampler, SamplingResult
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace.span import SpanContext

from .tracing import get_tracing_config

logger = logging.getLogger(__name__)


class SamplingDecision(Enum):
    """Sampling decision enumeration."""
    RECORD_AND_SAMPLE = "RECORD_AND_SAMPLE"
    RECORD_ONLY = "RECORD_ONLY"
    DROP = "DROP"


@dataclass
class SamplingContext:
    """Context for sampling decisions."""
    trace_id: int
    span_name: str
    span_kind: SpanKind
    attributes: Dict[str, Any]
    parent_context: Optional[SpanContext]
    links: List[Any]
    trace_state: Optional[TraceState]


class AdaptiveSampler(Sampler):
    """Adaptive sampler that adjusts sampling rate based on service load."""
    
    def __init__(self, base_sample_rate: float = 0.1, max_sample_rate: float = 1.0,
                 target_tps: int = 10, max_tps: int = 100,
                 window_size: int = 60):
        """
        Initialize adaptive sampler.
        
        Args:
            base_sample_rate: Base sampling rate (0.0 to 1.0)
            max_sample_rate: Maximum sampling rate (0.0 to 1.0)
            target_tps: Target traces per second
            max_tps: Maximum traces per second
            window_size: Window size in seconds for rate calculation
        """
        self.base_sample_rate = base_sample_rate
        self.max_sample_rate = max_sample_rate
        self.target_tps = target_tps
        self.max_tps = max_tps
        self.window_size = window_size
        
        # Rate tracking
        self.trace_counts = []
        self.current_tps = 0.0
        self.last_update = time.time()
        
        # Service-specific sampling rules
        self.service_rules = {
            "model-router": {"base_rate": 0.5, "max_rate": 1.0},
            "plan-management": {"base_rate": 0.3, "max_rate": 0.8},
            "git-worktree-manager": {"base_rate": 0.2, "max_rate": 0.6},
            "workflow-orchestrator": {"base_rate": 0.4, "max_rate": 0.9},
            "verification-feedback": {"base_rate": 0.3, "max_rate": 0.7},
        }
        
        # Operation-specific sampling rules
        self.operation_rules = {
            "llm.request": {"base_rate": 0.1, "max_rate": 0.5},
            "llm.response": {"base_rate": 0.1, "max_rate": 0.5},
            "database.query": {"base_rate": 0.05, "max_rate": 0.3},
            "http.request": {"base_rate": 0.1, "max_rate": 0.4},
            "message_queue.publish": {"base_rate": 0.05, "max_rate": 0.2},
            "message_queue.consume": {"base_rate": 0.05, "max_rate": 0.2},
        }
    
    def should_sample(self, parent_context: Optional[SpanContext], 
                     trace_id: int, name: str, kind: SpanKind = SpanKind.INTERNAL,
                     attributes: Dict[str, Any] = None, links: List[Any] = None,
                     trace_state: Optional[TraceState] = None) -> SamplingResult:
        """
        Determine if a span should be sampled.
        
        Args:
            parent_context: Parent span context
            trace_id: Trace ID
            name: Span name
            kind: Span kind
            attributes: Span attributes
            links: Span links
            trace_state: Trace state
            
        Returns:
            SamplingResult with decision and attributes
        """
        # Create sampling context
        sampling_context = SamplingContext(
            trace_id=trace_id,
            span_name=name,
            span_kind=kind,
            attributes=attributes or {},
            parent_context=parent_context,
            links=links or [],
            trace_state=trace_state
        )
        
        # Update current TPS
        self._update_tps()
        
        # Get sampling rate
        sample_rate = self._get_sample_rate(sampling_context)
        
        # Make sampling decision
        decision = self._make_sampling_decision(trace_id, sample_rate)
        
        # Add sampling attributes
        sampling_attributes = {
            "sampling.rate": sample_rate,
            "sampling.current_tps": self.current_tps,
            "sampling.target_tps": self.target_tps,
            "sampling.max_tps": self.max_tps,
            "sampling.decision": decision.value
        }
        
        return SamplingResult(
            decision=decision,
            attributes=sampling_attributes
        )
    
    def _update_tps(self):
        """Update current traces per second."""
        current_time = time.time()
        
        # Remove old trace counts
        self.trace_counts = [
            count for count in self.trace_counts
            if current_time - count <= self.window_size
        ]
        
        # Calculate current TPS
        self.current_tps = len(self.trace_counts) / self.window_size
        
        # Update last update time
        self.last_update = current_time
    
    def _get_sample_rate(self, context: SamplingContext) -> float:
        """Get sampling rate for the given context."""
        # Extract service name from attributes
        service_name = context.attributes.get("service.name", "unknown")
        
        # Extract operation type from span name
        operation_type = self._extract_operation_type(context.span_name)
        
        # Get base rates
        service_base_rate = self.service_rules.get(service_name, {}).get("base_rate", self.base_sample_rate)
        service_max_rate = self.service_rules.get(service_name, {}).get("max_rate", self.max_sample_rate)
        operation_base_rate = self.operation_rules.get(operation_type, {}).get("base_rate", self.base_sample_rate)
        operation_max_rate = self.operation_rules.get(operation_type, {}).get("max_rate", self.max_sample_rate)
        
        # Use the higher of service or operation base rate
        base_rate = max(service_base_rate, operation_base_rate)
        max_rate = min(service_max_rate, operation_max_rate)
        
        # Adjust based on current load
        if self.current_tps >= self.max_tps:
            # At maximum load, use minimum rate
            adjusted_rate = base_rate * 0.1
        elif self.current_tps >= self.target_tps:
            # Above target, reduce rate proportionally
            load_factor = (self.current_tps - self.target_tps) / (self.max_tps - self.target_tps)
            adjusted_rate = base_rate * (1.0 - load_factor * 0.9)
        else:
            # Below target, use full rate
            adjusted_rate = base_rate
        
        # Clamp to valid range
        adjusted_rate = max(0.0, min(adjusted_rate, max_rate))
        
        return adjusted_rate
    
    def _extract_operation_type(self, span_name: str) -> str:
        """Extract operation type from span name."""
        # Common patterns
        patterns = [
            r'llm\.(.+)',
            r'database\.(.+)',
            r'http\.(.+)',
            r'message_queue\.(.+)',
            r'service_communication\.(.+)',
            r'agent\.(.+)',
            r'workflow\.(.+)',
            r'verification\.(.+)',
            r'git\.(.+)',
            r'plan\.(.+)',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, span_name)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def _make_sampling_decision(self, trace_id: int, sample_rate: float) -> Decision:
        """Make sampling decision based on trace ID and sample rate."""
        # Record this trace
        self.trace_counts.append(time.time())
        
        # Use deterministic sampling based on trace ID
        if sample_rate >= 1.0:
            return Decision.RECORD_AND_SAMPLE
        elif sample_rate <= 0.0:
            return Decision.DROP
        else:
            # Use trace ID for deterministic sampling
            hash_value = int(hashlib.md5(str(trace_id).encode()).hexdigest(), 16)
            normalized_hash = hash_value / (2 ** 128)
            
            if normalized_hash < sample_rate:
                return Decision.RECORD_AND_SAMPLE
            else:
                return Decision.DROP
    
    def get_description(self) -> str:
        """Get sampler description."""
        return f"AdaptiveSampler(base_rate={self.base_sample_rate}, max_rate={self.max_sample_rate}, target_tps={self.target_tps})"


class PrivacyFilter:
    """Privacy-conscious filtering for sensitive data in traces."""
    
    def __init__(self):
        """Initialize privacy filter."""
        self.sensitive_patterns = [
            # Authentication and authorization
            (r'\bpassword\s*[:=]\s*[^\s]+', 'password=***'),
            (r'\btoken\s*[:=]\s*[^\s]+', 'token=***'),
            (r'\bapi[_-]?key\s*[:=]\s*[^\s]+', 'api_key=***'),
            (r'\bsecret\s*[:=]\s*[^\s]+', 'secret=***'),
            (r'\bauthorization\s*[:=]\s*[^\s]+', 'authorization=***'),
            (r'\bauth\s*[:=]\s*[^\s]+', 'auth=***'),
            (r'\bbearer\s+[^\s]+', 'bearer ***'),
            (r'\bbasic\s+[^\s]+', 'basic ***'),
            
            # Personal information
            (r'\bemail\s*[:=]\s*[^\s]+@[^\s]+', 'email=***'),
            (r'\bphone\s*[:=]\s*[^\s]+', 'phone=***'),
            (r'\bssn\s*[:=]\s*\d{3}[-]?\d{2}[-]?\d{4}', 'ssn=***'),
            (r'\bcredit[_-]?card\s*[:=]\s*\d+', 'credit_card=***'),
            (r'\bcard[_-]?number\s*[:=]\s*\d+', 'card_number=***'),
            (r'\bcvv\s*[:=]\s*\d{3,4}', 'cvv=***'),
            (r'\bexpiry\s*[:=]\s*\d{2}/\d{2,4}', 'expiry=***'),
            
            # Financial information
            (r'\bbank[_-]?account\s*[:=]\s*[^\s]+', 'bank_account=***'),
            (r'\baccount[_-]?number\s*[:=]\s*[^\s]+', 'account_number=***'),
            (r'\brouting[_-]?number\s*[:=]\s*[^\s]+', 'routing_number=***'),
            (r'\biban\s*[:=]\s*[^\s]+', 'iban=***'),
            (r'\bswift\s*[:=]\s*[^\s]+', 'swift=***'),
            
            # Health information
            (r'\bmedical[_-]?record\s*[:=]\s*[^\s]+', 'medical_record=***'),
            (r'\bpatient[_-]?id\s*[:=]\s*[^\s]+', 'patient_id=***'),
            (r'\bdiagnosis\s*[:=]\s*[^\s]+', 'diagnosis=***'),
            (r'\btreatment\s*[:=]\s*[^\s]+', 'treatment=***'),
            
            # Location information
            (r'\baddress\s*[:=]\s*[^\s]+', 'address=***'),
            (r'\blocation\s*[:=]\s*[^\s]+', 'location=***'),
            (r'\bgps\s*[:=]\s*[^\s]+', 'gps=***'),
            (r'\bcoordinates\s*[:=]\s*[^\s]+', 'coordinates=***'),
            
            # Database connection strings
            (r'\bpostgresql://[^\s]+', 'postgresql://***'),
            (r'\bmysql://[^\s]+', 'mysql://***'),
            (r'\bmongodb://[^\s]+', 'mongodb://***'),
            (r'\bredis://[^\s]+', 'redis://***'),
            
            # JWT tokens
            (r'\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b', 'jwt=***'),
        ]
        
        # Sensitive attribute names
        self.sensitive_attributes = {
            'password', 'token', 'api_key', 'secret', 'authorization', 'auth',
            'email', 'phone', 'ssn', 'credit_card', 'card_number', 'cvv', 'expiry',
            'bank_account', 'account_number', 'routing_number', 'iban', 'swift',
            'medical_record', 'patient_id', 'diagnosis', 'treatment',
            'address', 'location', 'gps', 'coordinates',
            'jwt', 'session_id', 'user_id', 'username'
        }
    
    def filter_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive data from span attributes."""
        filtered_attributes = {}
        
        for key, value in attributes.items():
            # Check if attribute name is sensitive
            if self._is_sensitive_attribute(key):
                filtered_attributes[key] = "***"
                continue
            
            # Filter string values
            if isinstance(value, str):
                filtered_value = self._filter_string(value)
                filtered_attributes[key] = filtered_value
            elif isinstance(value, dict):
                filtered_attributes[key] = self.filter_attributes(value)
            elif isinstance(value, list):
                filtered_attributes[key] = [
                    self._filter_string(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                filtered_attributes[key] = value
        
        return filtered_attributes
    
    def filter_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter sensitive data from span events."""
        filtered_events = []
        
        for event in events:
            filtered_event = {
                'name': event.get('name', ''),
                'timestamp': event.get('timestamp', 0),
                'attributes': self.filter_attributes(event.get('attributes', {}))
            }
            filtered_events.append(filtered_event)
        
        return filtered_events
    
    def _is_sensitive_attribute(self, key: str) -> bool:
        """Check if attribute name is sensitive."""
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in self.sensitive_attributes)
    
    def _filter_string(self, text: str) -> str:
        """Filter sensitive data from string."""
        filtered_text = text
        
        for pattern, replacement in self.sensitive_patterns:
            filtered_text = re.sub(pattern, replacement, filtered_text, flags=re.IGNORECASE)
        
        return filtered_text


class TraceRetentionPolicy:
    """Trace retention policy management."""
    
    def __init__(self):
        """Initialize trace retention policy."""
        # Default retention policies (in days)
        self.default_retention_days = 30
        self.service_retention_policies = {
            "model-router": 7,
            "plan-management": 30,
            "git-worktree-manager": 14,
            "workflow-orchestrator": 30,
            "verification-feedback": 30,
        }
        
        # Error retention policies (in days)
        self.error_retention_days = 90
        
        # High-value trace retention policies (in days)
        self.high_value_retention_days = 180
        
        # Trace classification rules
        self.high_value_patterns = [
            r'llm\.request.*duration_ms>5000',
            r'llm\.request.*error_type=.*',
            r'database\.query.*duration_ms>1000',
            r'http\.request.*status_code>=500',
            r'workflow\.execution.*status=error',
            r'verification\.feedback.*severity=critical',
        ]
    
    def get_retention_days(self, span_attributes: Dict[str, Any]) -> int:
        """
        Get retention days for a trace based on span attributes.
        
        Args:
            span_attributes: Span attributes
            
        Returns:
            Retention days
        """
        # Check for high-value traces
        if self._is_high_value_trace(span_attributes):
            return self.high_value_retention_days
        
        # Check for error traces
        if self._is_error_trace(span_attributes):
            return self.error_retention_days
        
        # Check service-specific retention
        service_name = span_attributes.get("service.name", "unknown")
        if service_name in self.service_retention_policies:
            return self.service_retention_policies[service_name]
        
        # Use default retention
        return self.default_retention_days
    
    def _is_high_value_trace(self, span_attributes: Dict[str, Any]) -> bool:
        """Check if trace is high-value based on attributes."""
        # Convert attributes to string for pattern matching
        attr_string = json.dumps(span_attributes, sort_keys=True)
        
        # Check against high-value patterns
        for pattern in self.high_value_patterns:
            if re.search(pattern, attr_string, re.IGNORECASE):
                return True
        
        # Check for specific high-value indicators
        high_value_indicators = [
            ("sampling.decision", "RECORD_AND_SAMPLE"),
            ("http.status_code", lambda x: int(x) >= 500),
            ("llm.tokens.total", lambda x: int(x) > 10000),
            ("db.duration_ms", lambda x: float(x) > 5000),
            ("error.type", lambda x: x is not None),
        ]
        
        for key, condition in high_value_indicators:
            if key in span_attributes:
                value = span_attributes[key]
                if callable(condition):
                    try:
                        if condition(value):
                            return True
                    except (ValueError, TypeError):
                        pass
                elif condition == value:
                    return True
        
        return False
    
    def _is_error_trace(self, span_attributes: Dict[str, Any]) -> bool:
        """Check if trace contains errors."""
        error_indicators = [
            "error.type",
            "error.message",
            "exception.type",
            "exception.message",
            "http.status_code",
            "db.error",
            "llm.error",
        ]
        
        for indicator in error_indicators:
            if indicator in span_attributes and span_attributes[indicator]:
                return True
        
        return False


class TraceSamplingManager:
    """Manager for trace sampling and filtering."""
    
    def __init__(self):
        """Initialize trace sampling manager."""
        self.adaptive_sampler = AdaptiveSampler()
        self.privacy_filter = PrivacyFilter()
        self.retention_policy = TraceRetentionPolicy()
    
    def configure_sampler(self, base_sample_rate: float = None, max_sample_rate: float = None,
                         target_tps: int = None, max_tps: int = None):
        """Configure adaptive sampler parameters."""
        if base_sample_rate is not None:
            self.adaptive_sampler.base_sample_rate = base_sample_rate
        if max_sample_rate is not None:
            self.adaptive_sampler.max_sample_rate = max_sample_rate
        if target_tps is not None:
            self.adaptive_sampler.target_tps = target_tps
        if max_tps is not None:
            self.adaptive_sampler.max_tps = max_tps
    
    def get_sampler(self) -> AdaptiveSampler:
        """Get the adaptive sampler."""
        return self.adaptive_sampler
    
    def get_privacy_filter(self) -> PrivacyFilter:
        """Get the privacy filter."""
        return self.privacy_filter
    
    def get_retention_policy(self) -> TraceRetentionPolicy:
        """Get the retention policy."""
        return self.retention_policy
    
    def filter_span_data(self, span_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter span data for privacy and retention."""
        # Filter attributes
        if 'attributes' in span_data:
            span_data['attributes'] = self.privacy_filter.filter_attributes(span_data['attributes'])
        
        # Filter events
        if 'events' in span_data:
            span_data['events'] = self.privacy_filter.filter_events(span_data['events'])
        
        # Add retention information
        if 'attributes' in span_data:
            retention_days = self.retention_policy.get_retention_days(span_data['attributes'])
            span_data['attributes']['retention_days'] = retention_days
        
        return span_data
    
    def get_sampling_stats(self) -> Dict[str, Any]:
        """Get sampling statistics."""
        return {
            "current_tps": self.adaptive_sampler.current_tps,
            "target_tps": self.adaptive_sampler.target_tps,
            "max_tps": self.adaptive_sampler.max_tps,
            "base_sample_rate": self.adaptive_sampler.base_sample_rate,
            "max_sample_rate": self.adaptive_sampler.max_sample_rate,
            "trace_count_window": len(self.adaptive_sampler.trace_counts),
            "window_size": self.adaptive_sampler.window_size,
        }


# Global instance
trace_sampling_manager = TraceSamplingManager()


def get_trace_sampling_manager() -> TraceSamplingManager:
    """Get the global trace sampling manager."""
    return trace_sampling_manager


def configure_trace_sampling(base_sample_rate: float = None, max_sample_rate: float = None,
                           target_tps: int = None, max_tps: int = None):
    """Configure trace sampling parameters."""
    trace_sampling_manager.configure_sampler(
        base_sample_rate, max_sample_rate, target_tps, max_tps
    )


def get_adaptive_sampler() -> AdaptiveSampler:
    """Get the adaptive sampler."""
    return trace_sampling_manager.get_sampler()


def get_privacy_filter() -> PrivacyFilter:
    """Get the privacy filter."""
    return trace_sampling_manager.get_privacy_filter()


def get_retention_policy() -> TraceRetentionPolicy:
    """Get the retention policy."""
    return trace_sampling_manager.get_retention_policy()


def filter_span_data(span_data: Dict[str, Any]) -> Dict[str, Any]:
    """Filter span data for privacy and retention."""
    return trace_sampling_manager.filter_span_data(span_data)


def get_sampling_stats() -> Dict[str, Any]:
    """Get sampling statistics."""
    return trace_sampling_manager.get_sampling_stats()