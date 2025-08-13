#!/usr/bin/env python3
"""
Telemetry Client for AI Agent Collaboration Platform
Production-ready implementation with TTF metrics tracking
"""

import json
import time
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import requests
import yaml
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TelemetryEvent:
    """Telemetry event data structure"""
    event_name: str
    event_type: str
    timestamp: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    pii_flags: Optional[Dict[str, bool]] = None

@dataclass
class TTFMetrics:
    """Time-to-First-Value metrics"""
    user_id: str
    signup_timestamp: str
    ttf_project: Optional[float] = None
    ttf_agent: Optional[float] = None
    ttf_workflow: Optional[float] = None
    ttf_success: Optional[float] = None
    ttf_complete: Optional[float] = None
    ttf_efficiency_score: Optional[float] = None
    completed_stages: List[str] = None
    last_updated: str = None

class TelemetryClient:
    """Production telemetry client with TTF tracking"""
    
    def __init__(self, config_path: str = "launch/telemetry/config.yaml"):
        """Initialize telemetry client"""
        self.config = self._load_config(config_path)
        self.schema = self._load_schema()
        self.session_id = str(uuid.uuid4())
        self.event_buffer = []
        self.ttf_cache = {}
        self.base_url = os.getenv("TELEMETRY_API_URL", "https://telemetry.company.com")
        self.api_key = os.getenv("TELEMETRY_API_KEY")
        
        # Initialize TTF tracking
        self.ttf_targets = self.config.get("ttf_metrics", {}).get("targets", {})
        self.ttf_alerting = self.config.get("ttf_metrics", {}).get("alerting", {})
        
        logger.info(f"Telemetry client initialized with session {self.session_id}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load telemetry configuration"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info("Telemetry configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Failed to load telemetry config: {e}")
            return {}
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load telemetry event schema"""
        try:
            with open("launch/telemetry/events.schema.json", 'r') as f:
                schema = json.load(f)
            logger.info("Telemetry schema loaded successfully")
            return schema
        except Exception as e:
            logger.error(f"Failed to load telemetry schema: {e}")
            return {}
    
    def _validate_event(self, event: TelemetryEvent) -> bool:
        """Validate event against schema"""
        try:
            # Find event definition in schema
            event_def = None
            for evt in self.schema.get("events", []):
                if evt["event_name"] == event.event_name:
                    event_def = evt
                    break
            
            if not event_def:
                logger.error(f"Event {event.event_name} not found in schema")
                return False
            
            # Validate required properties
            required_props = event_def.get("required_properties", [])
            event_props = event.properties or {}
            
            for prop in required_props:
                if prop not in event_props:
                    logger.error(f"Required property {prop} missing from event {event.event_name}")
                    return False
            
            # Validate PII flags
            if event.pii_flags:
                schema_pii = event_def.get("pii_flags", {})
                for prop, is_pii in event.pii_flags.items():
                    if prop in schema_pii and schema_pii[prop] != is_pii:
                        logger.warning(f"PII flag mismatch for property {prop} in event {event.event_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Event validation failed: {e}")
            return False
    
    def _enrich_event(self, event: TelemetryEvent) -> TelemetryEvent:
        """Enrich event with additional context"""
        enrichment_config = self.config.get("processing", {}).get("enrichment", {})
        
        if enrichment_config.get("add_timestamp", True):
            event.timestamp = datetime.now(timezone.utc).isoformat()
        
        if enrichment_config.get("add_session_id", True):
            event.session_id = self.session_id
        
        if enrichment_config.get("add_correlation_id", True):
            event.correlation_id = str(uuid.uuid4())
        
        return event
    
    def _mask_pii(self, event: TelemetryEvent) -> TelemetryEvent:
        """Mask PII data based on flags"""
        if not event.pii_flags or not event.properties:
            return event
        
        masked_properties = event.properties.copy()
        
        for prop, is_pii in event.pii_flags.items():
            if is_pii and prop in masked_properties:
                value = masked_properties[prop]
                if isinstance(value, str):
                    # Hash PII values
                    masked_properties[prop] = hashlib.sha256(value.encode()).hexdigest()[:8]
                elif isinstance(value, (int, float)):
                    # Round numerical PII
                    masked_properties[prop] = round(value, -1)
        
        event.properties = masked_properties
        return event
    
    def track_event(self, event_name: str, event_type: str, properties: Dict[str, Any] = None, 
                   user_id: str = None, pii_flags: Dict[str, bool] = None) -> bool:
        """Track a telemetry event"""
        try:
            # Create event
            event = TelemetryEvent(
                event_name=event_name,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_id=user_id,
                properties=properties or {},
                pii_flags=pii_flags or {}
            )
            
            # Enrich and validate event
            event = self._enrich_event(event)
            event = self._mask_pii(event)
            
            if not self._validate_event(event):
                return False
            
            # Add to buffer
            self.event_buffer.append(asdict(event))
            
            # Process TTF metrics if applicable
            if user_id and event_name in ["first_project_created", "first_agent_created", 
                                        "first_workflow_executed", "first_success_event"]:
                self._update_ttf_metrics(user_id, event_name, event.timestamp)
            
            # Flush buffer if full
            if len(self.event_buffer) >= self.config.get("collection", {}).get("batch", {}).get("max_events", 100):
                self.flush_events()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to track event {event_name}: {e}")
            return False
    
    def _update_ttf_metrics(self, user_id: str, event_name: str, timestamp: str):
        """Update TTF metrics for a user"""
        try:
            if user_id not in self.ttf_cache:
                # Initialize TTF tracking for new user
                self.ttf_cache[user_id] = TTFMetrics(
                    user_id=user_id,
                    signup_timestamp=timestamp,
                    completed_stages=[]
                )
            
            ttf_metrics = self.ttf_cache[user_id]
            current_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            signup_time = datetime.fromisoformat(ttf_metrics.signup_timestamp.replace('Z', '+00:00'))
            
            # Calculate time differences in minutes
            time_diff = (current_time - signup_time).total_seconds() / 60
            
            if event_name == "first_project_created" and "project" not in ttf_metrics.completed_stages:
                ttf_metrics.ttf_project = time_diff
                ttf_metrics.completed_stages.append("project")
                logger.info(f"User {user_id} completed project stage in {time_diff:.2f} minutes")
            
            elif event_name == "first_agent_created" and "agent" not in ttf_metrics.completed_stages:
                ttf_metrics.ttf_agent = time_diff
                ttf_metrics.completed_stages.append("agent")
                logger.info(f"User {user_id} completed agent stage in {time_diff:.2f} minutes")
            
            elif event_name == "first_workflow_executed" and "workflow" not in ttf_metrics.completed_stages:
                ttf_metrics.ttf_workflow = time_diff
                ttf_metrics.completed_stages.append("workflow")
                logger.info(f"User {user_id} completed workflow stage in {time_diff:.2f} minutes")
            
            elif event_name == "first_success_event" and "success" not in ttf_metrics.completed_stages:
                ttf_metrics.ttf_success = time_diff
                ttf_metrics.completed_stages.append("success")
                logger.info(f"User {user_id} completed success stage in {time_diff:.2f} minutes")
                
                # Calculate complete TTF
                if all([ttf_metrics.ttf_project, ttf_metrics.ttf_agent, 
                       ttf_metrics.ttf_workflow, ttf_metrics.ttf_success]):
                    ttf_metrics.ttf_complete = (ttf_metrics.ttf_project + ttf_metrics.ttf_agent + 
                                              ttf_metrics.ttf_workflow + ttf_metrics.ttf_success)
                    
                    # Calculate efficiency score
                    target_ttf = self.ttf_targets.get("ttf_complete", 60)
                    if ttf_metrics.ttf_complete <= target_ttf:
                        ttf_metrics.ttf_efficiency_score = 100.0
                    else:
                        ttf_metrics.ttf_efficiency_score = max(0, (target_ttf / ttf_metrics.ttf_complete) * 100)
                    
                    logger.info(f"User {user_id} achieved TTF-Complete: {ttf_metrics.ttf_complete:.2f} minutes "
                              f"(Efficiency: {ttf_metrics.ttf_efficiency_score:.1f}%)")
                    
                    # Check alerting thresholds
                    self._check_ttf_alerts(user_id, ttf_metrics.ttf_complete)
            
            ttf_metrics.last_updated = timestamp
            
        except Exception as e:
            logger.error(f"Failed to update TTF metrics for user {user_id}: {e}")
    
    def _check_ttf_alerts(self, user_id: str, ttf_complete: float):
        """Check TTF against alerting thresholds"""
        try:
            if ttf_complete > self.ttf_alerting.get("escalation_threshold", 180):
                logger.critical(f"TTF ESCALATION: User {user_id} took {ttf_complete:.2f} minutes")
                self._send_alert("escalation", user_id, ttf_complete)
            elif ttf_complete > self.ttf_alerting.get("critical_threshold", 120):
                logger.error(f"TTF CRITICAL: User {user_id} took {ttf_complete:.2f} minutes")
                self._send_alert("critical", user_id, ttf_complete)
            elif ttf_complete > self.ttf_alerting.get("warning_threshold", 75):
                logger.warning(f"TTF WARNING: User {user_id} took {ttf_complete:.2f} minutes")
                self._send_alert("warning", user_id, ttf_complete)
                
        except Exception as e:
            logger.error(f"Failed to check TTF alerts: {e}")
    
    def _send_alert(self, level: str, user_id: str, ttf_value: float):
        """Send TTF alert to configured channels"""
        try:
            alert_data = {
                "level": level,
                "user_id": user_id,
                "ttf_value": ttf_value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "threshold": self.ttf_alerting.get(f"{level}_threshold", 0)
            }
            
            # Send to configured alerting platforms
            alerting_config = self.config.get("integrations", {}).get("alerting", [])
            
            for platform in alerting_config:
                if platform.get("enabled", False):
                    self._send_platform_alert(platform, alert_data)
                    
        except Exception as e:
            logger.error(f"Failed to send TTF alert: {e}")
    
    def _send_platform_alert(self, platform: Dict[str, Any], alert_data: Dict[str, Any]):
        """Send alert to specific platform"""
        try:
            platform_name = platform.get("name", "")
            
            if platform_name == "slack" and platform.get("webhook_url"):
                self._send_slack_alert(platform["webhook_url"], alert_data)
            elif platform_name == "pagerduty" and platform.get("service_key"):
                self._send_pagerduty_alert(platform["service_key"], alert_data)
            elif platform_name == "email":
                self._send_email_alert(platform, alert_data)
                
        except Exception as e:
            logger.error(f"Failed to send alert to {platform.get('name', 'unknown')}: {e}")
    
    def _send_slack_alert(self, webhook_url: str, alert_data: Dict[str, Any]):
        """Send alert to Slack"""
        try:
            color_map = {"warning": "#ffa500", "critical": "#ff0000", "escalation": "#8b0000"}
            color = color_map.get(alert_data["level"], "#000000")
            
            message = {
                "attachments": [{
                    "color": color,
                    "title": f"TTF {alert_data['level'].upper()} Alert",
                    "text": f"User {alert_data['user_id']} took {alert_data['ttf_value']:.2f} minutes to achieve first value",
                    "fields": [
                        {"title": "TTF Value", "value": f"{alert_data['ttf_value']:.2f} minutes", "short": True},
                        {"title": "Threshold", "value": f"{alert_data['threshold']} minutes", "short": True},
                        {"title": "User ID", "value": alert_data["user_id"], "short": True}
                    ],
                    "footer": "AI Agent Collaboration Platform Telemetry",
                    "ts": int(time.time())
                }]
            }
            
            response = requests.post(webhook_url, json=message, timeout=10)
            response.raise_for_status()
            logger.info("Slack alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def _send_pagerduty_alert(self, service_key: str, alert_data: Dict[str, Any]):
        """Send alert to PagerDuty"""
        try:
            severity_map = {"warning": "warning", "critical": "critical", "escalation": "critical"}
            severity = severity_map.get(alert_data["level"], "info")
            
            message = {
                "routing_key": service_key,
                "event_action": "trigger",
                "payload": {
                    "summary": f"TTF {alert_data['level'].upper()}: User took {alert_data['ttf_value']:.2f} minutes",
                    "severity": severity,
                    "source": "telemetry-client",
                    "custom_details": alert_data
                }
            }
            
            response = requests.post("https://events.pagerduty.com/v2/enqueue", 
                                  json=message, timeout=10)
            response.raise_for_status()
            logger.info("PagerDuty alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send PagerDuty alert: {e}")
    
    def _send_email_alert(self, platform_config: Dict[str, Any], alert_data: Dict[str, Any]):
        """Send alert via email"""
        # Implementation would depend on SMTP configuration
        logger.info(f"Email alert would be sent for TTF {alert_data['level']}")
    
    def get_ttf_metrics(self, user_id: str) -> Optional[TTFMetrics]:
        """Get TTF metrics for a user"""
        return self.ttf_cache.get(user_id)
    
    def get_ttf_summary(self) -> Dict[str, Any]:
        """Get summary of all TTF metrics"""
        try:
            total_users = len(self.ttf_cache)
            completed_users = sum(1 for metrics in self.ttf_cache.values() 
                               if metrics.ttf_complete is not None)
            
            if completed_users == 0:
                return {"total_users": total_users, "completed_users": 0}
            
            ttf_values = [metrics.ttf_complete for metrics in self.ttf_cache.values() 
                         if metrics.ttf_complete is not None]
            
            summary = {
                "total_users": total_users,
                "completed_users": completed_users,
                "completion_rate": (completed_users / total_users) * 100,
                "avg_ttf": sum(ttf_values) / len(ttf_values),
                "median_ttf": sorted(ttf_values)[len(ttf_values) // 2],
                "min_ttf": min(ttf_values),
                "max_ttf": max(ttf_values),
                "ttf_distribution": {
                    "under_30": sum(1 for ttf in ttf_values if ttf < 30),
                    "under_60": sum(1 for ttf in ttf_values if ttf < 60),
                    "under_90": sum(1 for ttf in ttf_values if ttf < 90),
                    "over_90": sum(1 for ttf in ttf_values if ttf >= 90)
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate TTF summary: {e}")
            return {}
    
    def flush_events(self) -> bool:
        """Flush buffered events to telemetry API"""
        if not self.event_buffer:
            return True
        
        try:
            events = self.event_buffer.copy()
            self.event_buffer.clear()
            
            # Send events to telemetry API
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"events": events, "batch_id": str(uuid.uuid4())}
            
            response = requests.post(f"{self.base_url}/api/v1/events/batch", 
                                  json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Successfully flushed {len(events)} events to telemetry API")
            return True
            
        except Exception as e:
            logger.error(f"Failed to flush events: {e}")
            # Re-add events to buffer for retry
            self.event_buffer.extend(events)
            return False
    
    def close(self):
        """Close telemetry client and flush remaining events"""
        try:
            self.flush_events()
            logger.info("Telemetry client closed successfully")
        except Exception as e:
            logger.error(f"Error closing telemetry client: {e}")

# Convenience functions for common events
def track_user_signup(client: TelemetryClient, user_id: str, signup_method: str, 
                     plan_tier: str = "free") -> bool:
    """Track user signup event"""
    return client.track_event(
        event_name="user_signed_up",
        event_type="user_action",
        properties={
            "signup_method": signup_method,
            "plan_tier": plan_tier
        },
        user_id=user_id,
        pii_flags={"user_id": False}
    )

def track_user_signin(client: TelemetryClient, user_id: str, signin_method: str) -> bool:
    """Track user signin event"""
    return client.track_event(
        event_name="user_signed_in",
        event_type="user_action",
        properties={"signin_method": signin_method},
        user_id=user_id,
        pii_flags={"user_id": False}
    )

def track_project_creation(client: TelemetryClient, user_id: str, project_id: str, 
                          project_name: str, project_type: str) -> bool:
    """Track project creation event"""
    return client.track_event(
        event_name="first_project_created",
        event_type="user_action",
        properties={
            "project_id": project_id,
            "project_name": project_name,
            "project_type": project_type
        },
        user_id=user_id,
        pii_flags={"user_id": False, "project_name": True}
    )

def track_agent_creation(client: TelemetryClient, user_id: str, project_id: str, 
                        agent_id: str, agent_type: str, agent_model: str) -> bool:
    """Track agent creation event"""
    return client.track_event(
        event_name="first_agent_created",
        event_type="user_action",
        properties={
            "project_id": project_id,
            "agent_id": agent_id,
            "agent_type": agent_type,
            "agent_model": agent_model
        },
        user_id=user_id,
        pii_flags={"user_id": False}
    )

def track_workflow_execution(client: TelemetryClient, user_id: str, project_id: str, 
                           workflow_id: str, workflow_type: str, agents_involved: int) -> bool:
    """Track workflow execution event"""
    return client.track_event(
        event_name="first_workflow_executed",
        event_type="user_action",
        properties={
            "project_id": project_id,
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "agents_involved": agents_involved
        },
        user_id=user_id,
        pii_flags={"user_id": False}
    )

def track_success_event(client: TelemetryClient, user_id: str, project_id: str, 
                       success_type: str, feature_used: str) -> bool:
    """Track success event"""
    return client.track_event(
        event_name="first_success_event",
        event_type="user_action",
        properties={
            "project_id": project_id,
            "success_type": success_type,
            "feature_used": feature_used
        },
        user_id=user_id,
        pii_flags={"user_id": False}
    )

# Example usage
if __name__ == "__main__":
    # Initialize telemetry client
    client = TelemetryClient()
    
    try:
        # Example user journey tracking
        user_id = "user_123"
        
        # Track signup
        track_user_signup(client, user_id, "email", "free")
        
        # Simulate project creation after 3 minutes
        time.sleep(3)
        track_project_creation(client, user_id, "proj_456", "My First Project", "development")
        
        # Simulate agent creation after 2 more minutes
        time.sleep(2)
        track_agent_creation(client, user_id, "proj_456", "agent_789", "planner", "claude-3-sonnet")
        
        # Simulate workflow execution after 1 more minute
        time.sleep(1)
        track_workflow_execution(client, user_id, "proj_456", "workflow_101", "code_review", 2)
        
        # Simulate success after 2 more minutes
        time.sleep(2)
        track_success_event(client, user_id, "proj_456", "code_review_complete", "automated_review")
        
        # Get TTF summary
        summary = client.get_ttf_summary()
        print(f"TTF Summary: {json.dumps(summary, indent=2)}")
        
        # Get user-specific TTF metrics
        user_metrics = client.get_ttf_metrics(user_id)
        if user_metrics:
            print(f"User {user_id} TTF Metrics:")
            print(f"  Project: {user_metrics.ttf_project:.2f} minutes")
            print(f"  Agent: {user_metrics.ttf_agent:.2f} minutes")
            print(f"  Workflow: {user_metrics.ttf_workflow:.2f} minutes")
            print(f"  Success: {user_metrics.ttf_success:.2f} minutes")
            print(f"  Complete: {user_metrics.ttf_complete:.2f} minutes")
            print(f"  Efficiency: {user_metrics.ttf_efficiency_score:.1f}%")
        
    finally:
        client.close()