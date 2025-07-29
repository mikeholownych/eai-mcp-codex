"""
Security Automation and Incident Response System

Provides automated incident response capabilities including:
- Automated threat response workflows
- Incident classification and escalation
- Playbook-driven response automation
- Integration with external security tools
- Incident tracking and case management
- Post-incident analysis and reporting
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import secrets
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

import jinja2

from ..common.redis_client import RedisClient
from .threat_detection import ThreatEvent, ThreatType, ThreatLevel
from .audit_logging import AuditLogger, AuditEventType, AuditEventSeverity

logger = logging.getLogger(__name__)


class IncidentStatus(str, Enum):
    """Incident status values"""
    NEW = "new"
    INVESTIGATING = "investigating" 
    CONTAINING = "containing"
    ERADICATING = "eradicating"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(str, Enum):
    """Types of automated actions"""
    BLOCK_IP = "block_ip"
    SUSPEND_USER = "suspend_user"
    REVOKE_TOKENS = "revoke_tokens"
    QUARANTINE_FILE = "quarantine_file"
    ISOLATE_SYSTEM = "isolate_system"
    SEND_ALERT = "send_alert"
    CREATE_TICKET = "create_ticket"
    RUN_SCRIPT = "run_script"
    API_CALL = "api_call"
    NOTIFY_TEAM = "notify_team"


class ActionStatus(str, Enum):
    """Status of automated actions"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class IncidentEvent:
    """Represents a security incident"""
    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    threat_events: List[str] = field(default_factory=list)  # ThreatEvent IDs
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    playbook_used: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission"""
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "threat_events": self.threat_events,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": self.updated_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "tags": self.tags,
            "artifacts": self.artifacts,
            "timeline": self.timeline,
            "playbook_used": self.playbook_used
        }


@dataclass
class AutomatedAction:
    """Represents an automated response action"""
    action_id: str
    action_type: ActionType
    parameters: Dict[str, Any]
    status: ActionStatus = ActionStatus.PENDING
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "parameters": self.parameters,
            "status": self.status.value,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds
        }


@dataclass
class ResponsePlaybook:
    """Defines automated response workflow"""
    playbook_id: str
    name: str
    description: str
    trigger_conditions: Dict[str, Any]  # Conditions that trigger this playbook
    actions: List[Dict[str, Any]]  # List of actions to execute
    escalation_rules: List[Dict[str, Any]] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    
    def matches_threat(self, threat_event: ThreatEvent) -> bool:
        """Check if threat event matches playbook conditions"""
        conditions = self.trigger_conditions
        
        # Check threat type
        if "threat_types" in conditions:
            if threat_event.threat_type.value not in conditions["threat_types"]:
                return False
        
        # Check threat level
        if "min_threat_level" in conditions:
            threat_levels = ["low", "medium", "high", "critical"]
            min_level_idx = threat_levels.index(conditions["min_threat_level"])
            current_level_idx = threat_levels.index(threat_event.threat_level.value)
            if current_level_idx < min_level_idx:
                return False
        
        # Check risk score
        if "min_risk_score" in conditions:
            if threat_event.risk_score < conditions["min_risk_score"]:
                return False
        
        # Check confidence
        if "min_confidence" in conditions:
            if threat_event.confidence < conditions["min_confidence"]:
                return False
        
        # Check source IP patterns
        if "ip_patterns" in conditions and threat_event.source_ip:
            import re
            patterns = conditions["ip_patterns"]
            if not any(re.match(pattern, threat_event.source_ip) for pattern in patterns):
                return False
        
        return True


class ActionExecutor(Protocol):
    """Protocol for action executors"""
    async def execute(self, action: AutomatedAction) -> Dict[str, Any]:
        ...


class BlockIPExecutor:
    """Executor for blocking IP addresses"""
    
    def __init__(self, firewall_api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.firewall_api_url = firewall_api_url
        self.api_key = api_key
    
    async def execute(self, action: AutomatedAction) -> Dict[str, Any]:
        """Block IP address"""
        ip_address = action.parameters.get("ip_address")
        if not ip_address:
            raise ValueError("IP address not provided")
        
        duration = action.parameters.get("duration_minutes", 60)
        reason = action.parameters.get("reason", "Automated security response")
        
        if self.firewall_api_url and self.api_key:
            # Call external firewall API
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                payload = {
                    "ip_address": ip_address,
                    "action": "block",
                    "duration": duration,
                    "reason": reason
                }
                
                async with session.post(
                    f"{self.firewall_api_url}/block",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Successfully blocked IP {ip_address}")
                        return {
                            "success": True,
                            "ip_address": ip_address,
                            "duration": duration,
                            "firewall_response": result
                        }
                    else:
                        error_msg = f"Firewall API error: {response.status}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
        else:
            # Simulate blocking (log only)
            logger.warning(f"IP {ip_address} would be blocked for {duration} minutes (simulation)")
            return {
                "success": True,
                "ip_address": ip_address,
                "duration": duration,
                "simulated": True
            }


class SuspendUserExecutor:
    """Executor for suspending user accounts"""
    
    def __init__(self, user_management_api: Optional[str] = None):
        self.user_management_api = user_management_api
    
    async def execute(self, action: AutomatedAction) -> Dict[str, Any]:
        """Suspend user account"""
        user_id = action.parameters.get("user_id")
        if not user_id:
            raise ValueError("User ID not provided")
        
        duration = action.parameters.get("duration_minutes", 60)
        reason = action.parameters.get("reason", "Security incident response")
        
        # In a real implementation, this would call the user management system
        logger.warning(f"User {user_id} suspended for {duration} minutes: {reason}")
        
        return {
            "success": True,
            "user_id": user_id,
            "duration": duration,
            "reason": reason,
            "suspended_at": datetime.utcnow().isoformat()
        }


class SendAlertExecutor:
    """Executor for sending alerts"""
    
    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None, webhook_urls: Optional[List[str]] = None):
        self.smtp_config = smtp_config
        self.webhook_urls = webhook_urls or []
        self.email_template = jinja2.Template("""
Security Alert: {{ alert_title }}

Incident ID: {{ incident_id }}
Severity: {{ severity }}
Time: {{ timestamp }}

Description:
{{ description }}

Threat Details:
- Type: {{ threat_type }}
- Source IP: {{ source_ip }}
- Risk Score: {{ risk_score }}

Actions Taken:
{{ actions_taken }}

Please review and take appropriate action if necessary.
""")
    
    async def execute(self, action: AutomatedAction) -> Dict[str, Any]:
        """Send alert via email and webhooks"""
        alert_data = action.parameters
        results = {}
        
        # Send email alerts
        if self.smtp_config and alert_data.get("email_recipients"):
            try:
                await self._send_email_alert(alert_data)
                results["email_sent"] = True
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
                results["email_error"] = str(e)
        
        # Send webhook alerts
        for webhook_url in self.webhook_urls:
            try:
                await self._send_webhook_alert(webhook_url, alert_data)
                results.setdefault("webhooks_sent", []).append(webhook_url)
            except Exception as e:
                logger.error(f"Failed to send webhook alert to {webhook_url}: {e}")
                results.setdefault("webhook_errors", {})[webhook_url] = str(e)
        
        return results
    
    async def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Send email alert"""
        if not self.smtp_config:
            return
        
        # Render email content
        email_content = self.email_template.render(**alert_data)
        
        msg = MIMEMultipart()
        msg['From'] = self.smtp_config['from_address']
        msg['To'] = ', '.join(alert_data['email_recipients'])
        msg['Subject'] = f"Security Alert: {alert_data.get('alert_title', 'Incident Detected')}"
        
        msg.attach(MIMEText(email_content, 'plain'))
        
        # Send email
        with smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port']) as server:
            if self.smtp_config.get('use_tls'):
                server.starttls()
            
            if self.smtp_config.get('username'):
                server.login(self.smtp_config['username'], self.smtp_config['password'])
            
            server.send_message(msg)
    
    async def _send_webhook_alert(self, webhook_url: str, alert_data: Dict[str, Any]):
        """Send webhook alert"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "alert_type": "security_incident",
                "timestamp": datetime.utcnow().isoformat(),
                "data": alert_data
            }
            
            async with session.post(webhook_url, json=payload) as response:
                if response.status not in [200, 201, 202]:
                    raise Exception(f"Webhook returned status {response.status}")


class APICallExecutor:
    """Executor for making API calls"""
    
    async def execute(self, action: AutomatedAction) -> Dict[str, Any]:
        """Make API call"""
        url = action.parameters.get("url")
        method = action.parameters.get("method", "POST").upper()
        headers = action.parameters.get("headers", {})
        payload = action.parameters.get("payload", {})
        
        if not url:
            raise ValueError("API URL not provided")
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=payload, headers=headers) as response:
                result = {
                    "status_code": response.status,
                    "success": 200 <= response.status < 300
                }
                
                try:
                    result["response"] = await response.json()
                except:
                    result["response"] = await response.text()
                
                return result


class IncidentResponseEngine:
    """Main incident response engine"""
    
    def __init__(self, redis_client: RedisClient, audit_logger: AuditLogger):
        self.redis_client = redis_client
        self.audit_logger = audit_logger
        
        # Storage
        self.incidents: Dict[str, IncidentEvent] = {}
        self.playbooks: Dict[str, ResponsePlaybook] = {}
        
        # Action executors
        self.executors: Dict[ActionType, ActionExecutor] = {}
        
        # Active automation
        self.auto_response_enabled = True
        self.pending_actions: Dict[str, AutomatedAction] = {}
        
        # Statistics
        self.stats = {
            "incidents_created": 0,
            "incidents_resolved": 0,
            "actions_executed": 0,
            "actions_failed": 0,
            "playbooks_triggered": 0
        }
    
    async def initialize(self):
        """Initialize the incident response engine"""
        # Register default executors
        self.executors[ActionType.BLOCK_IP] = BlockIPExecutor()
        self.executors[ActionType.SUSPEND_USER] = SuspendUserExecutor()
        self.executors[ActionType.SEND_ALERT] = SendAlertExecutor()
        self.executors[ActionType.API_CALL] = APICallExecutor()
        
        # Load existing data
        await self._load_incidents()
        await self._load_playbooks()
        
        # Start background tasks
        asyncio.create_task(self._process_pending_actions())
        
        logger.info("Incident response engine initialized")
    
    async def handle_threat_event(self, threat_event: ThreatEvent) -> Optional[IncidentEvent]:
        """Handle incoming threat event"""
        # Check if we should create an incident
        incident = await self._evaluate_incident_creation(threat_event)
        
        if incident:
            # Store incident
            self.incidents[incident.incident_id] = incident
            await self._store_incident(incident)
            
            # Find matching playbooks
            matching_playbooks = [
                playbook for playbook in self.playbooks.values()
                if playbook.is_active and playbook.matches_threat(threat_event)
            ]
            
            if matching_playbooks:
                # Use the first matching playbook (could be prioritized in future)
                playbook = matching_playbooks[0]
                await self._execute_playbook(incident, playbook, threat_event)
            
            # Update statistics
            self.stats["incidents_created"] += 1
            
            # Log incident creation
            self.audit_logger.log_event(
                AuditEventType.ADMIN_ACTION,
                f"Security incident created: {incident.incident_id}",
                severity=self._map_severity_to_audit(incident.severity),
                details=incident.to_dict()
            )
        
        return incident
    
    async def create_manual_incident(self, 
                                   title: str,
                                   description: str,
                                   severity: IncidentSeverity,
                                   created_by: str,
                                   threat_event_ids: Optional[List[str]] = None) -> IncidentEvent:
        """Create incident manually"""
        incident_id = f"inc_{int(time.time())}_{secrets.token_hex(4)}"
        
        incident = IncidentEvent(
            incident_id=incident_id,
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.NEW,
            threat_events=threat_event_ids or [],
            created_by=created_by
        )
        
        # Add to timeline
        incident.timeline.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "incident_created",
            "user": created_by,
            "details": {"method": "manual"}
        })
        
        # Store incident
        self.incidents[incident_id] = incident
        await self._store_incident(incident)
        
        self.stats["incidents_created"] += 1
        
        # Log creation
        self.audit_logger.log_event(
            AuditEventType.ADMIN_ACTION,
            f"Manual incident created: {incident_id}",
            user_id=created_by,
            details=incident.to_dict()
        )
        
        return incident
    
    async def update_incident_status(self, 
                                   incident_id: str,
                                   new_status: IncidentStatus,
                                   updated_by: str,
                                   notes: Optional[str] = None) -> bool:
        """Update incident status"""
        if incident_id not in self.incidents:
            return False
        
        incident = self.incidents[incident_id]
        old_status = incident.status
        
        incident.status = new_status
        incident.updated_at = datetime.utcnow()
        incident.updated_by = updated_by
        
        # Set resolution/closure timestamps
        if new_status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.utcnow()
            self.stats["incidents_resolved"] += 1
        elif new_status == IncidentStatus.CLOSED:
            incident.closed_at = datetime.utcnow()
        
        # Add to timeline
        timeline_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "status_changed",
            "user": updated_by,
            "details": {
                "old_status": old_status.value,
                "new_status": new_status.value,
                "notes": notes
            }
        }
        incident.timeline.append(timeline_entry)
        
        # Store updated incident
        await self._store_incident(incident)
        
        # Log status change
        self.audit_logger.log_event(
            AuditEventType.ADMIN_ACTION,
            f"Incident status changed: {incident_id} ({old_status.value} -> {new_status.value})",
            user_id=updated_by,
            details=timeline_entry
        )
        
        return True
    
    async def assign_incident(self, incident_id: str, assigned_to: str, assigned_by: str) -> bool:
        """Assign incident to user"""
        if incident_id not in self.incidents:
            return False
        
        incident = self.incidents[incident_id]
        old_assignee = incident.assigned_to
        
        incident.assigned_to = assigned_to
        incident.updated_at = datetime.utcnow()
        incident.updated_by = assigned_by
        
        # Add to timeline
        incident.timeline.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "incident_assigned",
            "user": assigned_by,
            "details": {
                "old_assignee": old_assignee,
                "new_assignee": assigned_to
            }
        })
        
        # Store updated incident
        await self._store_incident(incident)
        
        return True
    
    async def execute_manual_action(self, 
                                  incident_id: str,
                                  action_type: ActionType,
                                  parameters: Dict[str, Any],
                                  executed_by: str) -> AutomatedAction:
        """Execute manual action for an incident"""
        action_id = f"action_{int(time.time())}_{secrets.token_hex(4)}"
        
        action = AutomatedAction(
            action_id=action_id,
            action_type=action_type,
            parameters=parameters
        )
        
        # Execute action
        try:
            result = await self._execute_action(action)
            action.result = result
            action.status = ActionStatus.COMPLETED
            self.stats["actions_executed"] += 1
            
        except Exception as e:
            action.status = ActionStatus.FAILED
            action.error_message = str(e)
            self.stats["actions_failed"] += 1
            logger.error(f"Manual action failed: {e}")
        
        # Update incident timeline
        if incident_id in self.incidents:
            incident = self.incidents[incident_id]
            incident.timeline.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "manual_action_executed",
                "user": executed_by,
                "details": action.to_dict()
            })
            await self._store_incident(incident)
        
        # Log action
        self.audit_logger.log_event(
            AuditEventType.ADMIN_ACTION,
            f"Manual action executed: {action_type.value}",
            user_id=executed_by,
            details=action.to_dict()
        )
        
        return action
    
    async def create_playbook(self, playbook_data: Dict[str, Any], created_by: str) -> ResponsePlaybook:
        """Create new response playbook"""
        playbook_id = f"pb_{int(time.time())}_{secrets.token_hex(4)}"
        
        playbook = ResponsePlaybook(
            playbook_id=playbook_id,
            name=playbook_data["name"],
            description=playbook_data["description"],
            trigger_conditions=playbook_data["trigger_conditions"],
            actions=playbook_data["actions"],
            escalation_rules=playbook_data.get("escalation_rules", []),
            created_by=created_by
        )
        
        # Store playbook
        self.playbooks[playbook_id] = playbook
        await self._store_playbook(playbook)
        
        # Log creation
        self.audit_logger.log_event(
            AuditEventType.ADMIN_ACTION,
            f"Response playbook created: {playbook.name}",
            user_id=created_by,
            details={"playbook_id": playbook_id, "conditions": playbook.trigger_conditions}
        )
        
        return playbook
    
    async def get_incidents(self, 
                          status: Optional[IncidentStatus] = None,
                          severity: Optional[IncidentSeverity] = None,
                          assigned_to: Optional[str] = None,
                          limit: int = 100) -> List[IncidentEvent]:
        """Get incidents with optional filtering"""
        incidents = list(self.incidents.values())
        
        # Apply filters
        if status:
            incidents = [i for i in incidents if i.status == status]
        
        if severity:
            incidents = [i for i in incidents if i.severity == severity]
        
        if assigned_to:
            incidents = [i for i in incidents if i.assigned_to == assigned_to]
        
        # Sort by creation time (newest first)
        incidents.sort(key=lambda x: x.created_at, reverse=True)
        
        return incidents[:limit]
    
    async def get_incident_statistics(self) -> Dict[str, Any]:
        """Get incident response statistics"""
        stats = self.stats.copy()
        
        # Add current incident counts
        active_incidents = len([i for i in self.incidents.values() if i.status not in [IncidentStatus.CLOSED]])
        stats["active_incidents"] = active_incidents
        
        # Add status breakdown
        status_counts = {}
        for status in IncidentStatus:
            count = len([i for i in self.incidents.values() if i.status == status])
            status_counts[status.value] = count
        stats["incidents_by_status"] = status_counts
        
        # Add severity breakdown
        severity_counts = {}
        for severity in IncidentSeverity:
            count = len([i for i in self.incidents.values() if i.severity == severity])
            severity_counts[severity.value] = count
        stats["incidents_by_severity"] = severity_counts
        
        return stats
    
    async def _evaluate_incident_creation(self, threat_event: ThreatEvent) -> Optional[IncidentEvent]:
        """Evaluate if threat event should create an incident"""
        # Rules for incident creation
        create_incident = False
        
        # High/Critical threats always create incidents
        if threat_event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            create_incident = True
        
        # High risk score creates incident
        elif threat_event.risk_score >= 7:
            create_incident = True
        
        # Certain threat types always create incidents
        elif threat_event.threat_type in [
            ThreatType.BRUTE_FORCE,
            ThreatType.PRIVILEGE_ESCALATION,
            ThreatType.DATA_EXFILTRATION
        ]:
            create_incident = True
        
        if not create_incident:
            return None
        
        # Create incident
        incident_id = f"inc_{int(time.time())}_{secrets.token_hex(4)}"
        severity = self._map_threat_to_incident_severity(threat_event.threat_level)
        
        incident = IncidentEvent(
            incident_id=incident_id,
            title=f"{threat_event.threat_type.value.replace('_', ' ').title()} Detected",
            description=f"Automated incident created for {threat_event.threat_type.value} threat",
            severity=severity,
            status=IncidentStatus.NEW,
            threat_events=[threat_event.event_id],
            created_by="system"
        )
        
        # Add initial timeline entry
        incident.timeline.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "incident_created",
            "user": "system",
            "details": {
                "trigger_event": threat_event.event_id,
                "threat_type": threat_event.threat_type.value,
                "risk_score": threat_event.risk_score
            }
        })
        
        return incident
    
    async def _execute_playbook(self, incident: IncidentEvent, playbook: ResponsePlaybook, threat_event: ThreatEvent):
        """Execute response playbook"""
        incident.playbook_used = playbook.playbook_id
        self.stats["playbooks_triggered"] += 1
        
        # Add to timeline
        incident.timeline.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "playbook_executed",
            "user": "system",
            "details": {
                "playbook_id": playbook.playbook_id,
                "playbook_name": playbook.name
            }
        })
        
        # Execute actions
        for action_def in playbook.actions:
            action_id = f"action_{int(time.time())}_{secrets.token_hex(4)}"
            
            # Substitute variables in parameters
            parameters = self._substitute_variables(action_def["parameters"], threat_event, incident)
            
            action = AutomatedAction(
                action_id=action_id,
                action_type=ActionType(action_def["type"]),
                parameters=parameters,
                max_retries=action_def.get("max_retries", 3),
                timeout_seconds=action_def.get("timeout", 300)
            )
            
            # Queue action for execution
            self.pending_actions[action_id] = action
            
            # Add to incident timeline
            incident.timeline.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "action_queued",
                "user": "system",
                "details": action.to_dict()
            })
        
        # Update incident status
        incident.status = IncidentStatus.INVESTIGATING
        await self._store_incident(incident)
        
        # Log playbook execution
        self.audit_logger.log_event(
            AuditEventType.ADMIN_ACTION,
            f"Response playbook executed: {playbook.name}",
            details={
                "incident_id": incident.incident_id,
                "playbook_id": playbook.playbook_id,
                "actions_queued": len(playbook.actions)
            }
        )
    
    def _substitute_variables(self, parameters: Dict[str, Any], threat_event: ThreatEvent, incident: IncidentEvent) -> Dict[str, Any]:
        """Substitute variables in action parameters"""
        substituted = {}
        
        for key, value in parameters.items():
            if isinstance(value, str):
                # Replace placeholders
                substituted[key] = value.format(
                    threat_event_id=threat_event.event_id,
                    incident_id=incident.incident_id,
                    source_ip=threat_event.source_ip or "",
                    user_id=threat_event.user_id or "",
                    threat_type=threat_event.threat_type.value,
                    risk_score=threat_event.risk_score,
                    timestamp=datetime.utcnow().isoformat()
                )
            else:
                substituted[key] = value
        
        return substituted
    
    async def _process_pending_actions(self):
        """Background task to process pending actions"""
        while True:
            try:
                # Process pending actions
                completed_actions = []
                
                for action_id, action in self.pending_actions.items():
                    if action.status == ActionStatus.PENDING:
                        action.status = ActionStatus.RUNNING
                        asyncio.create_task(self._execute_action_async(action))
                    
                    elif action.status in [ActionStatus.COMPLETED, ActionStatus.FAILED, ActionStatus.SKIPPED]:
                        completed_actions.append(action_id)
                
                # Remove completed actions
                for action_id in completed_actions:
                    del self.pending_actions[action_id]
                
                await asyncio.sleep(5)  # Process every 5 seconds
                
            except Exception as e:
                logger.error(f"Error processing pending actions: {e}")
                await asyncio.sleep(10)
    
    async def _execute_action_async(self, action: AutomatedAction):
        """Execute action asynchronously"""
        try:
            result = await self._execute_action(action)
            action.result = result
            action.status = ActionStatus.COMPLETED
            action.completed_at = datetime.utcnow()
            self.stats["actions_executed"] += 1
            
        except Exception as e:
            action.status = ActionStatus.FAILED
            action.error_message = str(e)
            action.completed_at = datetime.utcnow()
            self.stats["actions_failed"] += 1
            
            logger.error(f"Action execution failed: {action.action_id} - {e}")
            
            # Retry if within retry limit
            if action.retry_count < action.max_retries:
                action.retry_count += 1
                action.status = ActionStatus.PENDING
                logger.info(f"Retrying action {action.action_id} (attempt {action.retry_count})")
    
    async def _execute_action(self, action: AutomatedAction) -> Dict[str, Any]:
        """Execute single action"""
        executor = self.executors.get(action.action_type)
        if not executor:
            raise ValueError(f"No executor found for action type: {action.action_type}")
        
        action.executed_at = datetime.utcnow()
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                executor.execute(action),
                timeout=action.timeout_seconds
            )
            return result
        
        except asyncio.TimeoutError:
            raise Exception(f"Action timed out after {action.timeout_seconds} seconds")
    
    def _map_threat_to_incident_severity(self, threat_level: ThreatLevel) -> IncidentSeverity:
        """Map threat level to incident severity"""
        mapping = {
            ThreatLevel.LOW: IncidentSeverity.LOW,
            ThreatLevel.MEDIUM: IncidentSeverity.MEDIUM,
            ThreatLevel.HIGH: IncidentSeverity.HIGH,
            ThreatLevel.CRITICAL: IncidentSeverity.CRITICAL
        }
        return mapping.get(threat_level, IncidentSeverity.MEDIUM)
    
    def _map_severity_to_audit(self, severity: IncidentSeverity) -> AuditEventSeverity:
        """Map incident severity to audit severity"""
        mapping = {
            IncidentSeverity.LOW: AuditEventSeverity.LOW,
            IncidentSeverity.MEDIUM: AuditEventSeverity.MEDIUM,
            IncidentSeverity.HIGH: AuditEventSeverity.HIGH,
            IncidentSeverity.CRITICAL: AuditEventSeverity.CRITICAL
        }
        return mapping.get(severity, AuditEventSeverity.MEDIUM)
    
    async def _store_incident(self, incident: IncidentEvent):
        """Store incident in Redis"""
        try:
            incident_data = json.dumps(incident.to_dict(), default=str)
            await self.redis_client.client.set(
                f"incident:{incident.incident_id}",
                incident_data,
                ex=86400 * 30  # Expire after 30 days
            )
        except Exception as e:
            logger.error(f"Failed to store incident: {e}")
    
    async def _store_playbook(self, playbook: ResponsePlaybook):
        """Store playbook in Redis"""
        try:
            playbook_data = json.dumps({
                "playbook_id": playbook.playbook_id,
                "name": playbook.name,
                "description": playbook.description,
                "trigger_conditions": playbook.trigger_conditions,
                "actions": playbook.actions,
                "escalation_rules": playbook.escalation_rules,
                "is_active": playbook.is_active,
                "created_at": playbook.created_at.isoformat(),
                "created_by": playbook.created_by
            }, default=str)
            
            await self.redis_client.client.set(
                f"playbook:{playbook.playbook_id}",
                playbook_data
            )
        except Exception as e:
            logger.error(f"Failed to store playbook: {e}")
    
    async def _load_incidents(self):
        """Load incidents from Redis"""
        try:
            pattern = "incident:*"
            keys = await self.redis_client.client.keys(pattern)
            
            for key in keys:
                incident_data = await self.redis_client.client.get(key)
                if incident_data:
                    data = json.loads(incident_data)
                    incident = IncidentEvent(
                        incident_id=data["incident_id"],
                        title=data["title"],
                        description=data["description"],
                        severity=IncidentSeverity(data["severity"]),
                        status=IncidentStatus(data["status"]),
                        threat_events=data.get("threat_events", []),
                        assigned_to=data.get("assigned_to"),
                        created_at=datetime.fromisoformat(data["created_at"]),
                        created_by=data["created_by"],
                        updated_at=datetime.fromisoformat(data["updated_at"]),
                        updated_by=data.get("updated_by"),
                        resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
                        closed_at=datetime.fromisoformat(data["closed_at"]) if data.get("closed_at") else None,
                        tags=data.get("tags", []),
                        artifacts=data.get("artifacts", {}),
                        timeline=data.get("timeline", []),
                        playbook_used=data.get("playbook_used")
                    )
                    self.incidents[incident.incident_id] = incident
            
            logger.info(f"Loaded {len(self.incidents)} incidents")
        
        except Exception as e:
            logger.error(f"Failed to load incidents: {e}")
    
    async def _load_playbooks(self):
        """Load playbooks from Redis"""
        try:
            pattern = "playbook:*"
            keys = await self.redis_client.client.keys(pattern)
            
            for key in keys:
                playbook_data = await self.redis_client.client.get(key)
                if playbook_data:
                    data = json.loads(playbook_data)
                    playbook = ResponsePlaybook(
                        playbook_id=data["playbook_id"],
                        name=data["name"],
                        description=data["description"],
                        trigger_conditions=data["trigger_conditions"],
                        actions=data["actions"],
                        escalation_rules=data.get("escalation_rules", []),
                        is_active=data.get("is_active", True),
                        created_at=datetime.fromisoformat(data["created_at"]),
                        created_by=data["created_by"]
                    )
                    self.playbooks[playbook.playbook_id] = playbook
            
            logger.info(f"Loaded {len(self.playbooks)} playbooks")
        
        except Exception as e:
            logger.error(f"Failed to load playbooks: {e}")


# Factory function
async def setup_incident_response(redis_client: RedisClient, audit_logger: AuditLogger) -> IncidentResponseEngine:
    """Setup incident response engine"""
    engine = IncidentResponseEngine(redis_client, audit_logger)
    await engine.initialize()
    
    logger.info("Incident response engine initialized")
    return engine


# Example playbook definitions
EXAMPLE_PLAYBOOKS = {
    "brute_force_response": {
        "name": "Brute Force Attack Response",
        "description": "Automated response to brute force attacks",
        "trigger_conditions": {
            "threat_types": ["brute_force"],
            "min_risk_score": 5
        },
        "actions": [
            {
                "type": "block_ip",
                "parameters": {
                    "ip_address": "{source_ip}",
                    "duration_minutes": 60,
                    "reason": "Brute force attack detected"
                }
            },
            {
                "type": "send_alert",
                "parameters": {
                    "alert_title": "Brute Force Attack Blocked",
                    "description": "IP {source_ip} has been blocked due to brute force attack",
                    "email_recipients": ["security@company.com"],
                    "severity": "high"
                }
            }
        ]
    },
    
    "suspicious_ip_response": {
        "name": "Suspicious IP Response",
        "description": "Response to suspicious IP addresses",
        "trigger_conditions": {
            "threat_types": ["suspicious_ip"],
            "min_threat_level": "medium"
        },
        "actions": [
            {
                "type": "block_ip",
                "parameters": {
                    "ip_address": "{source_ip}",
                    "duration_minutes": 120,
                    "reason": "Suspicious IP detected"
                }
            },
            {
                "type": "api_call",
                "parameters": {
                    "url": "https://threat-intel.company.com/report",
                    "method": "POST",
                    "payload": {
                        "ip": "{source_ip}",
                        "incident_id": "{incident_id}",
                        "timestamp": "{timestamp}"
                    }
                }
            }
        ]
    }
}