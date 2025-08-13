"""
Health Check Monitoring and Alerting Integration.
Provides comprehensive monitoring, alerting, and dashboard integration for health checks.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from .health_aggregator import SystemHealthReport, ServiceHealthSummary, AggregationStatus, get_health_aggregator
from .logging import get_logger
from .tracing import get_tracer
from .metrics import get_metrics_collector

logger = get_logger("health_monitoring")
tracer = get_tracer()
metrics = get_metrics_collector("health_monitoring")


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of health alerts."""
    SERVICE_DOWN = "service_down"
    SERVICE_DEGRADED = "service_degraded"
    SERVICE_UNHEALTHY = "service_unhealthy"
    SYSTEM_DEGRADED = "system_degraded"
    SYSTEM_UNHEALTHY = "system_unhealthy"
    HIGH_ERROR_RATE = "high_error_rate"
    SLOW_RESPONSE = "slow_response"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CONNECTIVITY_ISSUE = "connectivity_issue"


@dataclass
class HealthAlert:
    """Health alert data structure."""
    id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    service_name: Optional[str]
    timestamp: str
    resolved: bool = False
    resolved_at: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    enabled: bool
    condition: str
    severity: AlertSeverity
    alert_type: AlertType
    threshold: float
    duration: int  # seconds
    services: List[str]  # empty list means all services
    notification_channels: List[str]


class HealthMonitor:
    """Monitors health checks and generates alerts."""
    
    def __init__(self):
        self.aggregator = get_health_aggregator()
        self.alert_rules = self._load_default_alert_rules()
        self.active_alerts: List[HealthAlert] = []
        self.alert_history: List[HealthAlert] = []
        self.max_alert_history = 1000
        self.notification_handlers = {}
        self.monitoring_interval = 30  # seconds
        
        # Initialize metrics
        self._initialize_metrics()
        
        # Setup notification handlers
        self._setup_notification_handlers()
    
    def _initialize_metrics(self):
        """Initialize health monitoring metrics."""
        metrics.register_gauge(
            "active_alerts_count",
            "Number of active health alerts",
            labels=["severity", "alert_type"]
        )
        
        metrics.register_counter(
            "alerts_generated_total",
            "Total number of alerts generated",
            labels=["severity", "alert_type"]
        )
        
        metrics.register_counter(
            "alerts_resolved_total",
            "Total number of alerts resolved",
            labels=["severity", "alert_type"]
        )
        
        metrics.register_histogram(
            "alert_processing_duration_seconds",
            "Time taken to process alerts",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        metrics.register_gauge(
            "health_monitoring_uptime_seconds",
            "Health monitoring service uptime"
        )
    
    def _load_default_alert_rules(self) -> List[AlertRule]:
        """Load default alert rules."""
        return [
            AlertRule(
                name="service_down",
                enabled=True,
                condition="service_status == 'error'",
                severity=AlertSeverity.CRITICAL,
                alert_type=AlertType.SERVICE_DOWN,
                threshold=1.0,
                duration=60,
                services=[],
                notification_channels=["email", "slack"]
            ),
            AlertRule(
                name="service_unhealthy",
                enabled=True,
                condition="service_status == 'unhealthy'",
                severity=AlertSeverity.ERROR,
                alert_type=AlertType.SERVICE_UNHEALTHY,
                threshold=1.0,
                duration=120,
                services=[],
                notification_channels=["email", "slack"]
            ),
            AlertRule(
                name="service_degraded",
                enabled=True,
                condition="service_status == 'degraded'",
                severity=AlertSeverity.WARNING,
                alert_type=AlertType.SERVICE_DEGRADED,
                threshold=1.0,
                duration=300,
                services=[],
                notification_channels=["email"]
            ),
            AlertRule(
                name="system_degraded",
                enabled=True,
                condition="system_status == 'degraded'",
                severity=AlertSeverity.WARNING,
                alert_type=AlertType.SYSTEM_DEGRADED,
                threshold=1.0,
                duration=60,
                services=[],
                notification_channels=["email", "slack", "pagerduty"]
            ),
            AlertRule(
                name="system_unhealthy",
                enabled=True,
                condition="system_status == 'unhealthy'",
                severity=AlertSeverity.ERROR,
                alert_type=AlertType.SYSTEM_UNHEALTHY,
                threshold=1.0,
                duration=30,
                services=[],
                notification_channels=["email", "slack", "pagerduty"]
            ),
            AlertRule(
                name="high_error_rate",
                enabled=True,
                condition="error_rate > 0.1",
                severity=AlertSeverity.ERROR,
                alert_type=AlertType.HIGH_ERROR_RATE,
                threshold=0.1,
                duration=300,
                services=[],
                notification_channels=["email", "slack"]
            ),
            AlertRule(
                name="slow_response",
                enabled=True,
                condition="response_time > 5000",
                severity=AlertSeverity.WARNING,
                alert_type=AlertType.SLOW_RESPONSE,
                threshold=5000.0,
                duration=600,
                services=[],
                notification_channels=["email"]
            ),
            AlertRule(
                name="resource_exhaustion",
                enabled=True,
                condition="resource_usage > 0.9",
                severity=AlertSeverity.ERROR,
                alert_type=AlertType.RESOURCE_EXHAUSTION,
                threshold=0.9,
                duration=120,
                services=[],
                notification_channels=["email", "slack", "pagerduty"]
            )
        ]
    
    def _setup_notification_handlers(self):
        """Setup notification handlers."""
        self.notification_handlers = {
            "email": self._send_email_notification,
            "slack": self._send_slack_notification,
            "pagerduty": self._send_pagerduty_notification,
            "webhook": self._send_webhook_notification
        }
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        logger.info("Starting health monitoring")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
        # Start metrics collection
        asyncio.create_task(self._metrics_collection_loop())
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                # Get current health report
                health_report = await self.aggregator.aggregate_all_health_checks()
                
                # Process alert rules
                await self._process_alert_rules(health_report)
                
                # Update active alerts
                self._update_active_alerts(health_report)
                
                # Wait for next iteration
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _metrics_collection_loop(self):
        """Collect and update monitoring metrics."""
        start_time = datetime.utcnow()
        
        while True:
            try:
                # Update uptime metric
                uptime = (datetime.utcnow() - start_time).total_seconds()
                metrics.gauge("health_monitoring_uptime_seconds").set(uptime)
                
                # Update active alerts metrics
                for severity in AlertSeverity:
                    for alert_type in AlertType:
                        count = sum(1 for alert in self.active_alerts
                                  if alert.severity == severity and alert.alert_type == alert_type)
                        metrics.gauge("active_alerts_count").labels(
                            severity=severity.value,
                            alert_type=alert_type.value
                        ).set(count)
                
                # Wait for next iteration
                await asyncio.sleep(60)  # Update metrics every minute
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {str(e)}")
                await asyncio.sleep(60)
    
    async def _process_alert_rules(self, health_report: SystemHealthReport):
        """Process alert rules against health report."""
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            try:
                await self._evaluate_alert_rule(rule, health_report)
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule.name}: {str(e)}")
    
    async def _evaluate_alert_rule(self, rule: AlertRule, health_report: SystemHealthReport):
        """Evaluate a single alert rule."""
        # Check if rule applies to specific services or all services
        target_services = rule.services if rule.services else [s.service_name for s in health_report.service_summaries]
        
        for service_name in target_services:
            # Find service summary
            service_summary = next(
                (s for s in health_report.service_summaries if s.service_name == service_name),
                None
            )
            
            if not service_summary:
                continue
            
            # Evaluate condition
            condition_met = await self._evaluate_condition(rule.condition, service_summary, health_report)
            
            if condition_met:
                # Check if alert already exists and is active
                existing_alert = next(
                    (a for a in self.active_alerts
                     if a.alert_type == rule.alert_type and a.service_name == service_name and not a.resolved),
                    None
                )
                
                if not existing_alert:
                    # Create new alert
                    alert = HealthAlert(
                        id=f"{rule.name}_{service_name}_{int(datetime.utcnow().timestamp())}",
                        alert_type=rule.alert_type,
                        severity=rule.severity,
                        title=self._generate_alert_title(rule, service_name),
                        message=self._generate_alert_message(rule, service_name, service_summary),
                        service_name=service_name,
                        timestamp=datetime.utcnow().isoformat(),
                        metadata={
                            "rule_name": rule.name,
                            "threshold": rule.threshold,
                            "current_value": self._get_current_value(rule.condition, service_summary),
                            "service_summary": asdict(service_summary)
                        }
                    )
                    
                    await self._trigger_alert(alert)
    
    async def _evaluate_condition(self, condition: str, service_summary: ServiceHealthSummary, 
                                 health_report: SystemHealthReport) -> bool:
        """Evaluate alert condition."""
        try:
            # Simple condition evaluation (in production, use a proper expression evaluator)
            if condition == "service_status == 'error'":
                return service_summary.overall_status == AggregationStatus.ERROR.value
            elif condition == "service_status == 'unhealthy'":
                return service_summary.overall_status == AggregationStatus.UNHEALTHY.value
            elif condition == "service_status == 'degraded'":
                return service_summary.overall_status == AggregationStatus.DEGRADED.value
            elif condition == "system_status == 'degraded'":
                return health_report.overall_status == AggregationStatus.DEGRADED.value
            elif condition == "system_status == 'unhealthy'":
                return health_report.overall_status == AggregationStatus.UNHEALTHY.value
            elif condition.startswith("error_rate >"):
                threshold = float(condition.split(">")[1].strip())
                error_rate = service_summary.error_checks / max(service_summary.total_checks, 1)
                return error_rate > threshold
            elif condition.startswith("response_time >"):
                threshold = float(condition.split(">")[1].strip())
                # This would need to be implemented with actual response time data
                return False  # Placeholder
            elif condition.startswith("resource_usage >"):
                threshold = float(condition.split(">")[1].strip())
                # This would need to be implemented with actual resource usage data
                return False  # Placeholder
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {str(e)}")
            return False
    
    def _get_current_value(self, condition: str, service_summary: ServiceHealthSummary) -> float:
        """Get current value for condition evaluation."""
        if condition.startswith("error_rate"):
            return service_summary.error_checks / max(service_summary.total_checks, 1)
        # Add more conditions as needed
        return 0.0
    
    def _generate_alert_title(self, rule: AlertRule, service_name: str) -> str:
        """Generate alert title."""
        if rule.alert_type == AlertType.SERVICE_DOWN:
            return f"Service Down: {service_name}"
        elif rule.alert_type == AlertType.SERVICE_UNHEALTHY:
            return f"Service Unhealthy: {service_name}"
        elif rule.alert_type == AlertType.SERVICE_DEGRADED:
            return f"Service Degraded: {service_name}"
        elif rule.alert_type == AlertType.SYSTEM_DEGRADED:
            return "System Degraded"
        elif rule.alert_type == AlertType.SYSTEM_UNHEALTHY:
            return "System Unhealthy"
        elif rule.alert_type == AlertType.HIGH_ERROR_RATE:
            return f"High Error Rate: {service_name}"
        elif rule.alert_type == AlertType.SLOW_RESPONSE:
            return f"Slow Response: {service_name}"
        elif rule.alert_type == AlertType.RESOURCE_EXHAUSTION:
            return f"Resource Exhaustion: {service_name}"
        else:
            return f"Health Alert: {service_name}"
    
    def _generate_alert_message(self, rule: AlertRule, service_name: str, 
                              service_summary: ServiceHealthSummary) -> str:
        """Generate alert message."""
        message = f"Alert triggered for service: {service_name}\n"
        message += f"Rule: {rule.name}\n"
        message += f"Severity: {rule.severity.value}\n"
        message += f"Service Status: {service_summary.overall_status}\n"
        message += f"Healthy Checks: {service_summary.healthy_checks}\n"
        message += f"Degraded Checks: {service_summary.degraded_checks}\n"
        message += f"Unhealthy Checks: {service_summary.unhealthy_checks}\n"
        message += f"Error Checks: {service_summary.error_checks}\n"
        message += f"Total Checks: {service_summary.total_checks}\n"
        message += f"Last Updated: {service_summary.last_updated}\n"
        
        if service_summary.critical_issues:
            message += "\nCritical Issues:\n"
            for issue in service_summary.critical_issues:
                message += f"- {issue}\n"
        
        if service_summary.warnings:
            message += "\nWarnings:\n"
            for warning in service_summary.warnings:
                message += f"- {warning}\n"
        
        return message
    
    async def _trigger_alert(self, alert: HealthAlert):
        """Trigger an alert."""
        logger.info(f"Triggering alert: {alert.title}")
        
        # Add to active alerts
        self.active_alerts.append(alert)
        
        # Add to alert history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_alert_history:
            self.alert_history = self.alert_history[-self.max_alert_history:]
        
        # Update metrics
        metrics.counter("alerts_generated_total").labels(
            severity=alert.severity.value,
            alert_type=alert.alert_type.value
        ).inc()
        
        # Send notifications
        await self._send_notifications(alert)
    
    async def _send_notifications(self, alert: HealthAlert):
        """Send alert notifications."""
        # Get notification channels from alert rule
        rule = next((r for r in self.alert_rules if r.alert_type == alert.alert_type), None)
        if not rule:
            return
        
        for channel in rule.notification_channels:
            try:
                handler = self.notification_handlers.get(channel)
                if handler:
                    await handler(alert)
            except Exception as e:
                logger.error(f"Error sending notification via {channel}: {str(e)}")
    
    async def _send_email_notification(self, alert: HealthAlert):
        """Send email notification."""
        try:
            # Basic implementation for health alerting
            # In production, configure SMTP settings and use proper email sending
            logger.info(f"Would send email notification for alert: {alert.title}")
            
            # Example email implementation (commented out for now):
            # msg = MIMEMultipart()
            # msg['From'] = "health-monitoring@example.com"
            # msg['To'] = "admin@example.com"
            # msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            # 
            # body = f"Alert Details:\n\n{alert.message}"
            # msg.attach(MIMEText(body, 'plain'))
            # 
            # with smtplib.SMTP('smtp.example.com', 587) as server:
            #     server.starttls()
            #     server.login('username', 'password')
            #     server.send_message(msg)
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
    
    async def _send_slack_notification(self, alert: HealthAlert):
        """Send Slack notification."""
        try:
            # Basic implementation for health alerting
            # In production, integrate with Slack API
            logger.info(f"Would send Slack notification for alert: {alert.title}")
            
            # Example Slack implementation (commented out for now):
            # import aiohttp
            # 
            # webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
            # 
            # payload = {
            #     "text": f"[{alert.severity.value.upper()}] {alert.title}",
            #     "attachments": [
            #         {
            #             "color": "danger" if alert.severity == AlertSeverity.CRITICAL else "warning",
            #             "text": alert.message
            #         }
            #     ]
            # }
            # 
            # async with aiohttp.ClientSession() as session:
            #     async with session.post(webhook_url, json=payload) as response:
            #         if response.status != 200:
            #             logger.error(f"Slack notification failed: {response.status}")
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
    
    async def _send_pagerduty_notification(self, alert: HealthAlert):
        """Send PagerDuty notification."""
        try:
            # Basic implementation for health alerting
            # In production, integrate with PagerDuty API
            logger.info(f"Would send PagerDuty notification for alert: {alert.title}")
            
        except Exception as e:
            logger.error(f"Error sending PagerDuty notification: {str(e)}")
    
    async def _send_webhook_notification(self, alert: HealthAlert):
        """Send webhook notification."""
        try:
            # Basic implementation for health alerting
            # In production, send to configured webhook URL
            logger.info(f"Would send webhook notification for alert: {alert.title}")
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")
    
    def _update_active_alerts(self, health_report: SystemHealthReport):
        """Update active alerts based on current health status."""
        alerts_to_resolve = []
        
        for alert in self.active_alerts:
            if alert.resolved:
                continue
            
            # Find service summary
            service_summary = next(
                (s for s in health_report.service_summaries if s.service_name == alert.service_name),
                None
            )
            
            if not service_summary:
                continue
            
            # Check if alert should be resolved
            should_resolve = False
            
            if alert.alert_type == AlertType.SERVICE_DOWN:
                should_resolve = service_summary.overall_status != AggregationStatus.ERROR.value
            elif alert.alert_type == AlertType.SERVICE_UNHEALTHY:
                should_resolve = service_summary.overall_status != AggregationStatus.UNHEALTHY.value
            elif alert.alert_type == AlertType.SERVICE_DEGRADED:
                should_resolve = service_summary.overall_status != AggregationStatus.DEGRADED.value
            elif alert.alert_type == AlertType.SYSTEM_DEGRADED:
                should_resolve = health_report.overall_status != AggregationStatus.DEGRADED.value
            elif alert.alert_type == AlertType.SYSTEM_UNHEALTHY:
                should_resolve = health_report.overall_status != AggregationStatus.UNHEALTHY.value
            
            if should_resolve:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow().isoformat()
                alerts_to_resolve.append(alert)
        
        # Update metrics for resolved alerts
        for alert in alerts_to_resolve:
            metrics.counter("alerts_resolved_total").labels(
                severity=alert.severity.value,
                alert_type=alert.alert_type.value
            ).inc()
            logger.info(f"Resolved alert: {alert.title}")
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None, 
                         alert_type: Optional[AlertType] = None) -> List[Dict[str, Any]]:
        """Get active alerts, optionally filtered by severity and type."""
        alerts = self.active_alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        
        return [asdict(alert) for alert in alerts if not alert.resolved]
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for the specified number of hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        history = [alert for alert in self.alert_history 
                  if datetime.fromisoformat(alert.timestamp) > cutoff_time]
        
        return [asdict(alert) for alert in history]
    
    def get_alert_rules(self) -> List[Dict[str, Any]]:
        """Get all alert rules."""
        return [asdict(rule) for rule in self.alert_rules]
    
    def update_alert_rule(self, rule_name: str, updates: Dict[str, Any]) -> bool:
        """Update an alert rule."""
        for rule in self.alert_rules:
            if rule.name == rule_name:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                logger.info(f"Updated alert rule: {rule_name}")
                return True
        
        logger.warning(f"Alert rule not found: {rule_name}")
        return False
    
    def add_alert_rule(self, rule: AlertRule) -> bool:
        """Add a new alert rule."""
        if any(r.name == rule.name for r in self.alert_rules):
            logger.warning(f"Alert rule already exists: {rule.name}")
            return False
        
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
        return True
    
    def remove_alert_rule(self, rule_name: str) -> bool:
        """Remove an alert rule."""
        for i, rule in enumerate(self.alert_rules):
            if rule.name == rule_name:
                del self.alert_rules[i]
                logger.info(f"Removed alert rule: {rule_name}")
                return True
        
        logger.warning(f"Alert rule not found: {rule_name}")
        return False
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring status information."""
        return {
            "monitoring_active": True,
            "monitoring_interval": self.monitoring_interval,
            "total_alert_rules": len(self.alert_rules),
            "enabled_alert_rules": sum(1 for r in self.alert_rules if r.enabled),
            "active_alerts": len([a for a in self.active_alerts if not a.resolved]),
            "alert_history_size": len(self.alert_history),
            "notification_channels": list(self.notification_handlers.keys())
        }


# Global instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


# Monitoring endpoints
async def get_active_alerts(severity: Optional[str] = None, alert_type: Optional[str] = None) -> Dict[str, Any]:
    """Get active alerts."""
    monitor = get_health_monitor()
    
    sev = AlertSeverity(severity) if severity else None
    at = AlertType(alert_type) if alert_type else None
    
    alerts = monitor.get_active_alerts(severity=sev, alert_type=at)
    
    return {
        "alerts": alerts,
        "total_count": len(alerts)
    }


async def get_alert_history(hours: int = 24) -> Dict[str, Any]:
    """Get alert history."""
    monitor = get_health_monitor()
    history = monitor.get_alert_history(hours)
    
    return {
        "hours": hours,
        "alerts": history,
        "total_count": len(history)
    }


async def get_alert_rules() -> Dict[str, Any]:
    """Get alert rules."""
    monitor = get_health_monitor()
    rules = monitor.get_alert_rules()
    
    return {
        "rules": rules,
        "total_count": len(rules)
    }


async def update_alert_rule(rule_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update an alert rule."""
    monitor = get_health_monitor()
    success = monitor.update_alert_rule(rule_name, updates)
    
    return {
        "success": success,
        "message": f"Alert rule {rule_name} {'updated' if success else 'not found'}"
    }


async def add_alert_rule(rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new alert rule."""
    monitor = get_health_monitor()
    
    try:
        rule = AlertRule(**rule_data)
        success = monitor.add_alert_rule(rule)
        
        return {
            "success": success,
            "message": f"Alert rule {rule.name} {'added' if success else 'already exists'}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error adding alert rule: {str(e)}"
        }


async def remove_alert_rule(rule_name: str) -> Dict[str, Any]:
    """Remove an alert rule."""
    monitor = get_health_monitor()
    success = monitor.remove_alert_rule(rule_name)
    
    return {
        "success": success,
        "message": f"Alert rule {rule_name} {'removed' if success else 'not found'}"
    }


async def get_monitoring_status() -> Dict[str, Any]:
    """Get monitoring status."""
    monitor = get_health_monitor()
    return monitor.get_monitoring_status()
