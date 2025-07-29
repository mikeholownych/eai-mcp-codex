"""
Security Metrics and Monitoring Dashboard

Provides comprehensive security monitoring and metrics collection:
- Real-time security metrics dashboard
- Security KPI tracking and alerting
- Threat intelligence visualization
- Security event correlation and analysis
- Performance monitoring for security components
- Integration with external monitoring systems (Prometheus, Grafana)
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import numpy as np
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import plotly.graph_objs as go
import plotly.utils

from ..common.redis_client import RedisClient
from .threat_detection import ThreatDetectionEngine, ThreatEvent, ThreatType, ThreatLevel
from .incident_response import IncidentResponseEngine, IncidentEvent, IncidentStatus, IncidentSeverity
from .session_management import SessionManager
from .audit_logging import AuditLogger

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of security metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class SecurityMetric:
    """Represents a security metric"""
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
            "description": self.description
        }


@dataclass
class SecurityAlert:
    """Represents a security alert"""
    alert_id: str
    title: str
    description: str
    level: AlertLevel
    metric_name: str
    threshold_value: float
    current_value: float
    timestamp: datetime
    is_active: bool = True
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "description": self.description,
            "level": self.level.value,
            "metric_name": self.metric_name,
            "threshold_value": self.threshold_value,
            "current_value": self.current_value,
            "timestamp": self.timestamp.isoformat(),
            "is_active": self.is_active,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class SecurityMetricsCollector:
    """Collects and aggregates security metrics"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.metric_definitions: Dict[str, Dict[str, Any]] = {}
        
        # Collection intervals
        self.collection_interval = 60  # seconds
        self.retention_hours = 24
        
        # Background task
        self._collection_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize metrics collector"""
        # Define standard security metrics
        self._define_standard_metrics()
        
        # Start collection task
        self._collection_task = asyncio.create_task(self._collect_metrics_loop())
        
        logger.info("Security metrics collector initialized")
    
    def _define_standard_metrics(self):
        """Define standard security metrics"""
        self.metric_definitions.update({
            "threats_detected_total": {
                "type": MetricType.COUNTER,
                "description": "Total number of threats detected",
                "labels": ["threat_type", "threat_level"]
            },
            "incidents_created_total": {
                "type": MetricType.COUNTER,
                "description": "Total number of incidents created",
                "labels": ["severity", "status"]
            },
            "active_sessions": {
                "type": MetricType.GAUGE,
                "description": "Number of active user sessions",
                "labels": ["session_type", "security_level"]
            },
            "failed_logins_total": {
                "type": MetricType.COUNTER,
                "description": "Total number of failed login attempts",
                "labels": ["source_ip", "user_id"]
            },
            "rate_limit_violations_total": {
                "type": MetricType.COUNTER,
                "description": "Total number of rate limit violations",
                "labels": ["endpoint", "source_ip"]
            },
            "security_response_time": {
                "type": MetricType.HISTOGRAM,
                "description": "Time taken to respond to security events",
                "labels": ["event_type", "response_type"]
            },
            "vulnerability_scan_results": {
                "type": MetricType.GAUGE,
                "description": "Number of vulnerabilities found",
                "labels": ["severity", "service"]
            },
            "encryption_operations_total": {
                "type": MetricType.COUNTER,
                "description": "Total number of encryption/decryption operations",
                "labels": ["operation", "algorithm"]
            },
            "audit_events_total": {
                "type": MetricType.COUNTER,
                "description": "Total number of audit events",
                "labels": ["event_type", "severity"]
            },
            "threat_intelligence_hits": {
                "type": MetricType.COUNTER,
                "description": "Number of threat intelligence matches",
                "labels": ["feed_source", "indicator_type"]
            }
        })
    
    async def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a metric value"""
        metric = SecurityMetric(
            name=name,
            metric_type=self.metric_definitions.get(name, {}).get("type", MetricType.GAUGE),
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels or {},
            description=self.metric_definitions.get(name, {}).get("description")
        )
        
        # Store in memory
        self.metrics[name].append(metric)
        
        # Store in Redis for persistence
        await self._store_metric_in_redis(metric)
    
    async def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None, value: float = 1.0):
        """Increment a counter metric"""
        await self.record_metric(name, value, labels)
    
    async def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric value"""
        await self.record_metric(name, value, labels)
    
    async def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value for histogram metric"""
        await self.record_metric(name, value, labels)
    
    async def get_metric_history(self, name: str, hours: int = 1) -> List[SecurityMetric]:
        """Get metric history for specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get from memory first
        history = [m for m in self.metrics[name] if m.timestamp >= cutoff_time]
        
        # If not enough data in memory, load from Redis
        if len(history) < 10:
            redis_history = await self._load_metric_from_redis(name, hours)
            history.extend(redis_history)
            
            # Sort by timestamp
            history.sort(key=lambda x: x.timestamp)
        
        return history
    
    async def get_current_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current value of a metric"""
        metric_history = self.metrics.get(name, deque())
        
        if not metric_history:
            return None
        
        # Filter by labels if provided
        if labels:
            for metric in reversed(metric_history):
                if all(metric.labels.get(k) == v for k, v in labels.items()):
                    return metric.value
            return None
        
        # Return most recent value
        return metric_history[-1].value
    
    async def calculate_rate(self, name: str, minutes: int = 5) -> float:
        """Calculate rate of change for a counter metric"""
        history = await self.get_metric_history(name, hours=1)
        
        if len(history) < 2:
            return 0.0
        
        # Filter to specified time window
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent_history = [m for m in history if m.timestamp >= cutoff_time]
        
        if len(recent_history) < 2:
            return 0.0
        
        # Calculate rate as difference over time
        latest = recent_history[-1]
        earliest = recent_history[0]
        
        time_diff = (latest.timestamp - earliest.timestamp).total_seconds()
        value_diff = latest.value - earliest.value
        
        return value_diff / (time_diff / 60) if time_diff > 0 else 0.0  # per minute
    
    async def _collect_metrics_loop(self):
        """Background loop to collect metrics"""
        while True:
            try:
                await asyncio.sleep(self.collection_interval)
                
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Clean up old metrics
                await self._cleanup_old_metrics()
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
    
    async def _collect_system_metrics(self):
        """Collect system-level security metrics"""
        try:
            # Memory usage for metrics storage
            memory_usage = sum(len(deque_obj) for deque_obj in self.metrics.values())
            await self.set_gauge("metrics_memory_usage", memory_usage)
            
            # Redis connection status
            try:
                await self.redis_client.client.ping()
                await self.set_gauge("redis_connection_status", 1.0)
            except:
                await self.set_gauge("redis_connection_status", 0.0)
            
        except Exception as e:
            logger.error(f"System metrics collection error: {e}")
    
    async def _store_metric_in_redis(self, metric: SecurityMetric):
        """Store metric in Redis for persistence"""
        try:
            key = f"metric:{metric.name}:{int(metric.timestamp.timestamp())}"
            await self.redis_client.client.set(
                key,
                json.dumps(metric.to_dict()),
                ex=self.retention_hours * 3600
            )
        except Exception as e:
            logger.error(f"Error storing metric in Redis: {e}")
    
    async def _load_metric_from_redis(self, name: str, hours: int) -> List[SecurityMetric]:
        """Load metric history from Redis"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            cutoff_timestamp = int(cutoff_time.timestamp())
            
            pattern = f"metric:{name}:*"
            keys = await self.redis_client.client.keys(pattern)
            
            metrics = []
            for key in keys:
                # Extract timestamp from key
                timestamp_str = key.decode().split(':')[-1]
                if int(timestamp_str) >= cutoff_timestamp:
                    data = await self.redis_client.client.get(key)
                    if data:
                        metric_dict = json.loads(data)
                        metric = SecurityMetric(
                            name=metric_dict["name"],
                            metric_type=MetricType(metric_dict["type"]),
                            value=metric_dict["value"],
                            timestamp=datetime.fromisoformat(metric_dict["timestamp"]),
                            labels=metric_dict.get("labels", {}),
                            description=metric_dict.get("description")
                        )
                        metrics.append(metric)
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error loading metrics from Redis: {e}")
            return []
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics from memory"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        for name, metric_history in self.metrics.items():
            # Remove old metrics
            while metric_history and metric_history[0].timestamp < cutoff_time:
                metric_history.popleft()


class SecurityAlerting:
    """Handles security alerting based on metrics"""
    
    def __init__(self, metrics_collector: SecurityMetricsCollector, redis_client: RedisClient):
        self.metrics_collector = metrics_collector
        self.redis_client = redis_client
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.active_alerts: Dict[str, SecurityAlert] = {}
        self.alert_callbacks: List[Callable] = []
        
        # Background task
        self._alerting_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize alerting system"""
        # Define default alert rules
        self._define_default_alert_rules()
        
        # Load existing alerts
        await self._load_active_alerts()
        
        # Start alerting task
        self._alerting_task = asyncio.create_task(self._alerting_loop())
        
        logger.info("Security alerting system initialized")
    
    def _define_default_alert_rules(self):
        """Define default alerting rules"""
        self.alert_rules.update({
            "high_threat_rate": {
                "metric": "threats_detected_total",
                "condition": "rate > 10",  # More than 10 threats per minute
                "level": AlertLevel.CRITICAL,
                "title": "High Threat Detection Rate",
                "description": "Threat detection rate is unusually high"
            },
            "failed_login_spike": {
                "metric": "failed_logins_total",
                "condition": "rate > 50",  # More than 50 failed logins per minute
                "level": AlertLevel.WARNING,
                "title": "Failed Login Spike",
                "description": "High number of failed login attempts detected"
            },
            "incident_backlog": {
                "metric": "incidents_created_total",
                "condition": "value > 100",  # More than 100 open incidents
                "level": AlertLevel.WARNING,
                "title": "Incident Backlog",
                "description": "High number of unresolved incidents"
            },
            "session_anomalies": {
                "metric": "active_sessions",
                "condition": "value > 10000",  # More than 10k active sessions
                "level": AlertLevel.INFO,
                "title": "High Session Count",
                "description": "Unusually high number of active sessions"
            },
            "redis_connection_down": {
                "metric": "redis_connection_status",
                "condition": "value < 1",
                "level": AlertLevel.CRITICAL,
                "title": "Redis Connection Down",
                "description": "Redis connection is not available"
            }
        })
    
    def add_alert_rule(self, rule_id: str, rule_config: Dict[str, Any]):
        """Add custom alert rule"""
        self.alert_rules[rule_id] = rule_config
    
    def add_alert_callback(self, callback: Callable):
        """Add callback function for alert notifications"""
        self.alert_callbacks.append(callback)
    
    async def check_alerts(self):
        """Check all alert rules against current metrics"""
        for rule_id, rule in self.alert_rules.items():
            try:
                await self._evaluate_alert_rule(rule_id, rule)
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule_id}: {e}")
    
    async def _evaluate_alert_rule(self, rule_id: str, rule: Dict[str, Any]):
        """Evaluate a single alert rule"""
        metric_name = rule["metric"]
        condition = rule["condition"]
        
        # Get current metric value or rate
        if "rate >" in condition:
            threshold = float(condition.split(">")[1].strip())
            current_value = await self.metrics_collector.calculate_rate(metric_name)
        elif "value >" in condition:
            threshold = float(condition.split(">")[1].strip())
            current_value = await self.metrics_collector.get_current_value(metric_name) or 0
        elif "value <" in condition:
            threshold = float(condition.split("<")[1].strip())
            current_value = await self.metrics_collector.get_current_value(metric_name) or 0
        else:
            logger.warning(f"Unsupported condition format: {condition}")
            return
        
        # Check if alert should be triggered
        alert_triggered = False
        if ">" in condition:
            alert_triggered = current_value > threshold
        elif "<" in condition:
            alert_triggered = current_value < threshold
        
        alert_id = f"{rule_id}_{metric_name}"
        
        if alert_triggered and alert_id not in self.active_alerts:
            # Create new alert
            alert = SecurityAlert(
                alert_id=alert_id,
                title=rule["title"],
                description=rule["description"],
                level=AlertLevel(rule["level"]),
                metric_name=metric_name,
                threshold_value=threshold,
                current_value=current_value,
                timestamp=datetime.utcnow()
            )
            
            self.active_alerts[alert_id] = alert
            await self._store_alert(alert)
            await self._trigger_alert_callbacks(alert)
            
            logger.warning(f"Alert triggered: {alert.title} (value: {current_value}, threshold: {threshold})")
        
        elif not alert_triggered and alert_id in self.active_alerts:
            # Resolve existing alert
            alert = self.active_alerts[alert_id]
            alert.is_active = False
            alert.resolved_at = datetime.utcnow()
            
            await self._store_alert(alert)
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert resolved: {alert.title}")
    
    async def get_active_alerts(self) -> List[SecurityAlert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    async def _alerting_loop(self):
        """Background loop for alert checking"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.check_alerts()
            except Exception as e:
                logger.error(f"Alerting loop error: {e}")
    
    async def _store_alert(self, alert: SecurityAlert):
        """Store alert in Redis"""
        try:
            await self.redis_client.client.set(
                f"alert:{alert.alert_id}",
                json.dumps(alert.to_dict()),
                ex=86400 * 7  # Keep for 7 days
            )
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    async def _load_active_alerts(self):
        """Load active alerts from Redis"""
        try:
            pattern = "alert:*"
            keys = await self.redis_client.client.keys(pattern)
            
            for key in keys:
                data = await self.redis_client.client.get(key)
                if data:
                    alert_dict = json.loads(data)
                    if alert_dict["is_active"]:
                        alert = SecurityAlert(
                            alert_id=alert_dict["alert_id"],
                            title=alert_dict["title"],
                            description=alert_dict["description"],
                            level=AlertLevel(alert_dict["level"]),
                            metric_name=alert_dict["metric_name"],
                            threshold_value=alert_dict["threshold_value"],
                            current_value=alert_dict["current_value"],
                            timestamp=datetime.fromisoformat(alert_dict["timestamp"]),
                            is_active=alert_dict["is_active"],
                            resolved_at=datetime.fromisoformat(alert_dict["resolved_at"]) if alert_dict.get("resolved_at") else None
                        )
                        self.active_alerts[alert.alert_id] = alert
            
            logger.info(f"Loaded {len(self.active_alerts)} active alerts")
        
        except Exception as e:
            logger.error(f"Error loading active alerts: {e}")
    
    async def _trigger_alert_callbacks(self, alert: SecurityAlert):
        """Trigger alert notification callbacks"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")


class SecurityDashboard:
    """Security monitoring dashboard"""
    
    def __init__(self, 
                 metrics_collector: SecurityMetricsCollector,
                 alerting: SecurityAlerting,
                 threat_detection: Optional[ThreatDetectionEngine] = None,
                 incident_response: Optional[IncidentResponseEngine] = None,
                 session_manager: Optional[SessionManager] = None):
        self.metrics_collector = metrics_collector
        self.alerting = alerting
        self.threat_detection = threat_detection
        self.incident_response = incident_response
        self.session_manager = session_manager
        
        # Dashboard data cache
        self.dashboard_data_cache: Dict[str, Any] = {}
        self.cache_ttl = 30  # seconds
        self.last_cache_update = 0
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        current_time = time.time()
        
        # Return cached data if still valid
        if current_time - self.last_cache_update < self.cache_ttl:
            return self.dashboard_data_cache
        
        # Collect fresh dashboard data
        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "overview": await self._get_overview_metrics(),
            "threats": await self._get_threat_metrics(),
            "incidents": await self._get_incident_metrics(),
            "sessions": await self._get_session_metrics(),
            "alerts": await self._get_alert_data(),
            "charts": await self._generate_chart_data()
        }
        
        # Update cache
        self.dashboard_data_cache = dashboard_data
        self.last_cache_update = current_time
        
        return dashboard_data
    
    async def _get_overview_metrics(self) -> Dict[str, Any]:
        """Get high-level overview metrics"""
        return {
            "threats_last_hour": await self.metrics_collector.calculate_rate("threats_detected_total", 60),
            "incidents_open": len([i for i in (await self.incident_response.get_incidents() if self.incident_response else [])
                                 if i.status not in [IncidentStatus.CLOSED, IncidentStatus.RESOLVED]]),
            "active_sessions": await self.metrics_collector.get_current_value("active_sessions") or 0,
            "failed_logins_last_hour": await self.metrics_collector.calculate_rate("failed_logins_total", 60),
            "active_alerts": len(await self.alerting.get_active_alerts()),
            "system_status": "healthy"  # Would be calculated based on various health metrics
        }
    
    async def _get_threat_metrics(self) -> Dict[str, Any]:
        """Get threat-related metrics"""
        if not self.threat_detection:
            return {}
        
        stats = await self.threat_detection.get_threat_statistics()
        
        return {
            "total_threats": stats.get("threats_detected", 0),
            "active_threats": stats.get("active_threats", 0),
            "threats_by_type": stats.get("active_threats_by_type", {}),
            "threats_by_level": stats.get("active_threats_by_level", {}),
            "detection_rate": await self.metrics_collector.calculate_rate("threats_detected_total", 60)
        }
    
    async def _get_incident_metrics(self) -> Dict[str, Any]:
        """Get incident-related metrics"""
        if not self.incident_response:
            return {}
        
        stats = await self.incident_response.get_incident_statistics()
        
        return {
            "total_incidents": stats.get("incidents_created", 0),
            "active_incidents": stats.get("active_incidents", 0),
            "incidents_by_status": stats.get("incidents_by_status", {}),
            "incidents_by_severity": stats.get("incidents_by_severity", {}),
            "resolution_rate": stats.get("incidents_resolved", 0) / max(stats.get("incidents_created", 1), 1)
        }
    
    async def _get_session_metrics(self) -> Dict[str, Any]:
        """Get session-related metrics"""
        if not self.session_manager:
            return {}
        
        stats = await self.session_manager.get_session_statistics()
        
        return {
            "total_sessions": stats.get("total_sessions", 0),
            "active_sessions": stats.get("active_sessions", 0),
            "anomalous_sessions": stats.get("anomalous_sessions", 0),
            "sessions_by_type": stats.get("sessions_by_type", {}),
            "sessions_by_security_level": stats.get("sessions_by_security_level", {}),
            "concurrent_users": stats.get("concurrent_users", 0)
        }
    
    async def _get_alert_data(self) -> Dict[str, Any]:
        """Get alert data"""
        active_alerts = await self.alerting.get_active_alerts()
        
        return {
            "active_count": len(active_alerts),
            "alerts_by_level": {
                level.value: len([a for a in active_alerts if a.level == level])
                for level in AlertLevel
            },
            "recent_alerts": [alert.to_dict() for alert in sorted(active_alerts, key=lambda x: x.timestamp, reverse=True)[:10]]
        }
    
    async def _generate_chart_data(self) -> Dict[str, Any]:
        """Generate data for dashboard charts"""
        charts = {}
        
        # Threat detection timeline
        threat_history = await self.metrics_collector.get_metric_history("threats_detected_total", hours=24)
        if threat_history:
            charts["threat_timeline"] = {
                "timestamps": [m.timestamp.isoformat() for m in threat_history],
                "values": [m.value for m in threat_history],
                "type": "line"
            }
        
        # Failed login attempts
        login_history = await self.metrics_collector.get_metric_history("failed_logins_total", hours=24)
        if login_history:
            charts["failed_logins"] = {
                "timestamps": [m.timestamp.isoformat() for m in login_history],
                "values": [m.value for m in login_history],
                "type": "bar"
            }
        
        # Active sessions over time
        session_history = await self.metrics_collector.get_metric_history("active_sessions", hours=24)
        if session_history:
            charts["session_count"] = {
                "timestamps": [m.timestamp.isoformat() for m in session_history],
                "values": [m.value for m in session_history],
                "type": "area"
            }
        
        return charts
    
    def generate_html_dashboard(self) -> str:
        """Generate HTML dashboard"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Monitoring Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .metric-card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metric-value { font-size: 2em; font-weight: bold; color: #3498db; }
                .metric-label { color: #7f8c8d; margin-top: 5px; }
                .chart-container { background: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .alert { padding: 10px; margin: 5px 0; border-radius: 3px; }
                .alert-critical { background-color: #e74c3c; color: white; }
                .alert-warning { background-color: #f39c12; color: white; }
                .alert-info { background-color: #3498db; color: white; }
                .status-healthy { color: #27ae60; font-weight: bold; }
                .status-warning { color: #f39c12; font-weight: bold; }
                .status-critical { color: #e74c3c; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Security Monitoring Dashboard</h1>
                <p>Real-time security metrics and threat intelligence</p>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value" id="threats-rate">--</div>
                    <div class="metric-label">Threats/Hour</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="active-incidents">--</div>
                    <div class="metric-label">Active Incidents</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="active-sessions">--</div>
                    <div class="metric-label">Active Sessions</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="failed-logins">--</div>
                    <div class="metric-label">Failed Logins/Hour</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="active-alerts">--</div>
                    <div class="metric-label">Active Alerts</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="system-status">--</div>
                    <div class="metric-label">System Status</div>
                </div>
            </div>
            
            <div class="chart-container">
                <h3>Threat Detection Timeline (24h)</h3>
                <div id="threat-chart"></div>
            </div>
            
            <div class="chart-container">
                <h3>Active Sessions Over Time</h3>
                <div id="session-chart"></div>
            </div>
            
            <div class="chart-container">
                <h3>Recent Security Alerts</h3>
                <div id="alerts-container"></div>
            </div>
            
            <script>
                async function updateDashboard() {
                    try {
                        const response = await fetch('/security/dashboard/data');
                        const data = await response.json();
                        
                        // Update metric cards
                        document.getElementById('threats-rate').textContent = Math.round(data.overview.threats_last_hour || 0);
                        document.getElementById('active-incidents').textContent = data.overview.incidents_open || 0;
                        document.getElementById('active-sessions').textContent = data.overview.active_sessions || 0;
                        document.getElementById('failed-logins').textContent = Math.round(data.overview.failed_logins_last_hour || 0);
                        document.getElementById('active-alerts').textContent = data.overview.active_alerts || 0;
                        
                        const statusElement = document.getElementById('system-status');
                        statusElement.textContent = data.overview.system_status || 'Unknown';
                        statusElement.className = 'status-' + (data.overview.system_status || 'warning');
                        
                        // Update charts
                        if (data.charts.threat_timeline) {
                            const threatTrace = {
                                x: data.charts.threat_timeline.timestamps,
                                y: data.charts.threat_timeline.values,
                                type: 'scatter',
                                mode: 'lines+markers',
                                name: 'Threats Detected'
                            };
                            Plotly.newPlot('threat-chart', [threatTrace], {height: 300});
                        }
                        
                        if (data.charts.session_count) {
                            const sessionTrace = {
                                x: data.charts.session_count.timestamps,
                                y: data.charts.session_count.values,
                                type: 'scatter',
                                fill: 'tonexty',
                                name: 'Active Sessions'
                            };
                            Plotly.newPlot('session-chart', [sessionTrace], {height: 300});
                        }
                        
                        // Update alerts
                        const alertsContainer = document.getElementById('alerts-container');
                        alertsContainer.innerHTML = '';
                        
                        if (data.alerts.recent_alerts) {
                            data.alerts.recent_alerts.forEach(alert => {
                                const alertDiv = document.createElement('div');
                                alertDiv.className = 'alert alert-' + alert.level;
                                alertDiv.innerHTML = `
                                    <strong>${alert.title}</strong><br>
                                    ${alert.description}<br>
                                    <small>Current: ${alert.current_value}, Threshold: ${alert.threshold_value}</small>
                                `;
                                alertsContainer.appendChild(alertDiv);
                            });
                        }
                        
                    } catch (error) {
                        console.error('Failed to update dashboard:', error);
                    }
                }
                
                // Update dashboard every 30 seconds
                updateDashboard();
                setInterval(updateDashboard, 30000);
            </script>
        </body>
        </html>
        """
        return html_template


class SecurityMetricsMiddleware:
    """FastAPI middleware to collect security metrics"""
    
    def __init__(self, metrics_collector: SecurityMetricsCollector):
        self.metrics_collector = metrics_collector
    
    async def __call__(self, request: Request, call_next):
        """Collect metrics from HTTP requests"""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record request metrics
            await self.metrics_collector.increment_counter(
                "http_requests_total",
                labels={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status_code": str(response.status_code)
                }
            )
            
            # Record response time
            response_time = time.time() - start_time
            await self.metrics_collector.observe_histogram(
                "http_request_duration_seconds",
                response_time,
                labels={
                    "method": request.method,
                    "endpoint": request.url.path
                }
            )
            
            # Record failed login attempts
            if (request.url.path == "/auth/login" and 
                response.status_code in [401, 403]):
                await self.metrics_collector.increment_counter(
                    "failed_logins_total",
                    labels={
                        "source_ip": request.client.host if request.client else "unknown"
                    }
                )
            
            return response
            
        except Exception as e:
            # Record error metrics
            await self.metrics_collector.increment_counter(
                "http_errors_total",
                labels={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "error_type": type(e).__name__
                }
            )
            raise


# Factory functions
async def setup_security_monitoring(redis_client: RedisClient,
                                   threat_detection: Optional[ThreatDetectionEngine] = None,
                                   incident_response: Optional[IncidentResponseEngine] = None,
                                   session_manager: Optional[SessionManager] = None) -> Tuple[SecurityMetricsCollector, SecurityAlerting, SecurityDashboard]:
    """Setup complete security monitoring system"""
    
    # Initialize metrics collector
    metrics_collector = SecurityMetricsCollector(redis_client)
    await metrics_collector.initialize()
    
    # Initialize alerting
    alerting = SecurityAlerting(metrics_collector, redis_client)
    await alerting.initialize()
    
    # Initialize dashboard
    dashboard = SecurityDashboard(
        metrics_collector, 
        alerting, 
        threat_detection, 
        incident_response, 
        session_manager
    )
    
    logger.info("Security monitoring system initialized")
    return metrics_collector, alerting, dashboard


def create_dashboard_routes(app: FastAPI, dashboard: SecurityDashboard):
    """Add dashboard routes to FastAPI app"""
    
    @app.get("/security/dashboard", response_class=HTMLResponse)
    async def get_dashboard():
        """Get HTML dashboard"""
        return dashboard.generate_html_dashboard()
    
    @app.get("/security/dashboard/data")
    async def get_dashboard_data():
        """Get dashboard data as JSON"""
        return await dashboard.get_dashboard_data()
    
    @app.get("/security/metrics/{metric_name}")
    async def get_metric_data(metric_name: str, hours: int = 1):
        """Get specific metric data"""
        history = await dashboard.metrics_collector.get_metric_history(metric_name, hours)
        return {
            "metric_name": metric_name,
            "data_points": len(history),
            "history": [m.to_dict() for m in history]
        }
    
    @app.get("/security/alerts")
    async def get_alerts():
        """Get active alerts"""
        alerts = await dashboard.alerting.get_active_alerts()
        return {
            "active_alerts": len(alerts),
            "alerts": [alert.to_dict() for alert in alerts]
        }


# Example alert callback functions
async def email_alert_callback(alert: SecurityAlert):
    """Example email alert callback"""
    logger.critical(f"EMAIL ALERT: {alert.title} - {alert.description}")
    # In production, this would send an actual email


async def slack_alert_callback(alert: SecurityAlert):
    """Example Slack alert callback"""
    logger.critical(f"SLACK ALERT: {alert.title} - {alert.description}")
    # In production, this would send to Slack webhook


async def webhook_alert_callback(alert: SecurityAlert):
    """Example webhook alert callback"""
    logger.critical(f"WEBHOOK ALERT: {alert.title} - {alert.description}")
    # In production, this would call external webhook