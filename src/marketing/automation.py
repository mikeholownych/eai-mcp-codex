"""
Marketing automation system for managing leads, campaigns, and automated workflows.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from uuid import uuid4
import json

from ..common.redis_client import RedisClient
from ..common.database import DatabaseManager

logger = logging.getLogger(__name__)


class LeadStatus(str, Enum):
    """Lead status values"""
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    DEMO_SCHEDULED = "demo_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATING = "negotiating"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class TriggerEvent(str, Enum):
    """Marketing automation trigger events"""
    LEAD_CREATED = "lead_created"
    LEAD_QUALIFIED = "lead_qualified"
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    WEBSITE_VISIT = "website_visit"
    DEMO_SCHEDULED = "demo_scheduled"
    TRIAL_STARTED = "trial_started"
    CONVERSION = "conversion"
    CUSTOM = "custom"


class CampaignType(str, Enum):
    """Campaign types"""
    LEAD_GENERATION = "lead_generation"
    NURTURING = "nurturing"
    CONVERSION = "conversion"
    RETENTION = "retention"
    UPSELL = "upsell"
    RE_ENGAGEMENT = "re_engagement"


@dataclass
class Lead:
    """Lead information"""
    id: str = field(default_factory=lambda: str(uuid4()))
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    job_title: str = ""
    phone: str = ""
    website: str = ""
    industry: str = ""
    company_size: str = ""
    budget: str = ""
    lead_source: str = ""
    status: LeadStatus = LeadStatus.NEW
    score: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_contacted: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None


@dataclass
class LeadScore:
    """Lead scoring information"""
    lead_id: str
    score: int
    factors: Dict[str, int] = field(default_factory=dict)
    last_calculated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversionEvent:
    """Conversion event tracking"""
    id: str = field(default_factory=lambda: str(uuid4()))
    lead_id: str = ""
    event_type: str = ""
    event_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    value: Optional[float] = None


@dataclass
class EmailSequence:
    """Email sequence definition"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    emails: List[Dict[str, Any]] = field(default_factory=list)
    triggers: List[TriggerEvent] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AutomationRule:
    """Marketing automation rule"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    trigger_event: TriggerEvent = TriggerEvent.LEAD_CREATED
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    active: bool = True
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Campaign:
    """Marketing campaign"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    campaign_type: CampaignType = CampaignType.LEAD_GENERATION
    target_audience: Dict[str, Any] = field(default_factory=dict)
    channels: List[str] = field(default_factory=list)
    budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = "draft"
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class MarketingAutomation:
    """Main marketing automation system"""

    def __init__(self, redis_client: RedisClient, db_manager: DatabaseManager):
        self.redis_client = redis_client
        self.db_manager = db_manager
        self.automation_rules: List[AutomationRule] = []
        self.email_sequences: List[EmailSequence] = []
        self.campaigns: List[Campaign] = []
        self.leads: Dict[str, Lead] = {}
        self.lead_scores: Dict[str, LeadScore] = {}
        self.conversion_events: List[ConversionEvent] = []
        
        # Event handlers
        self.event_handlers: Dict[TriggerEvent, List[Callable]] = {
            event: [] for event in TriggerEvent
        }
        
        # Automation engine
        self.automation_engine_running = False
        self.automation_task: Optional[asyncio.Task] = None

    async def start_automation_engine(self):
        """Start the marketing automation engine"""
        if self.automation_engine_running:
            logger.warning("Automation engine already running")
            return

        self.automation_engine_running = True
        self.automation_task = asyncio.create_task(self._automation_loop())
        logger.info("Marketing automation engine started")

    async def stop_automation_engine(self):
        """Stop the marketing automation engine"""
        self.automation_engine_running = False
        if self.automation_task:
            self.automation_task.cancel()
            try:
                await self.automation_task
            except asyncio.CancelledError:
                pass
        logger.info("Marketing automation engine stopped")

    async def _automation_loop(self):
        """Main automation loop"""
        while self.automation_engine_running:
            try:
                # Process pending automation rules
                await self._process_automation_rules()
                
                # Process email sequences
                await self._process_email_sequences()
                
                # Update lead scores
                await self._update_lead_scores()
                
                # Process follow-ups
                await self._process_follow_ups()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in automation loop: {e}")
                await asyncio.sleep(60)

    async def create_lead(self, lead_data: Dict[str, Any]) -> Lead:
        """Create a new lead"""
        lead = Lead(**lead_data)
        self.leads[lead.id] = lead
        
        # Store in database
        await self._store_lead(lead)
        
        # Trigger lead created event
        await self._trigger_event(TriggerEvent.LEAD_CREATED, lead)
        
        logger.info(f"Created lead: {lead.email}")
        return lead

    async def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> Optional[Lead]:
        """Update lead information"""
        if lead_id not in self.leads:
            return None
            
        lead = self.leads[lead_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(lead, key):
                setattr(lead, key, value)
        
        lead.updated_at = datetime.utcnow()
        
        # Store in database
        await self._store_lead(lead)
        
        # Check for status changes that might trigger events
        if "status" in updates:
            await self._check_status_change_triggers(lead, updates["status"])
        
        logger.info(f"Updated lead: {lead.email}")
        return lead

    async def qualify_lead(self, lead_id: str, qualification_data: Dict[str, Any]) -> bool:
        """Qualify a lead based on criteria"""
        if lead_id not in self.leads:
            return False
            
        lead = self.leads[lead_id]
        
        # Apply qualification criteria
        score = await self._calculate_lead_score(lead, qualification_data)
        
        # Update lead score
        if lead_id not in self.lead_scores:
            self.lead_scores[lead_id] = LeadScore(lead_id=lead_id, score=score)
        else:
            self.lead_scores[lead_id].score = score
            self.lead_scores[lead_id].last_calculated = datetime.utcnow()
        
        # Update lead status if qualified
        if score >= 70:  # Qualification threshold
            lead.status = LeadStatus.QUALIFIED
            await self._trigger_event(TriggerEvent.LEAD_QUALIFIED, lead)
            logger.info(f"Lead qualified: {lead.email} (score: {score})")
            return True
        
        return False

    async def add_automation_rule(self, rule: AutomationRule):
        """Add a new automation rule"""
        self.automation_rules.append(rule)
        self.automation_rules.sort(key=lambda x: x.priority, reverse=True)
        
        # Store in database
        await self._store_automation_rule(rule)
        
        logger.info(f"Added automation rule: {rule.name}")

    async def add_email_sequence(self, sequence: EmailSequence):
        """Add a new email sequence"""
        self.email_sequences.append(sequence)
        
        # Store in database
        await self._store_email_sequence(sequence)
        
        logger.info(f"Added email sequence: {sequence.name}")

    async def track_conversion(self, lead_id: str, event_type: str, event_data: Dict[str, Any], value: Optional[float] = None):
        """Track a conversion event"""
        conversion_event = ConversionEvent(
            lead_id=lead_id,
            event_type=event_type,
            event_data=event_data,
            value=value
        )
        
        self.conversion_events.append(conversion_event)
        
        # Store in database
        await self._store_conversion_event(conversion_event)
        
        # Trigger conversion event
        await self._trigger_event(TriggerEvent.CONVERSION, conversion_event)
        
        logger.info(f"Tracked conversion: {event_type} for lead {lead_id}")

    async def _trigger_event(self, event_type: TriggerEvent, data: Any):
        """Trigger an automation event"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")

    async def _process_automation_rules(self):
        """Process pending automation rules"""
        for rule in self.automation_rules:
            if not rule.active:
                continue
                
            # Check if rule conditions are met
            if await self._check_rule_conditions(rule):
                await self._execute_rule_actions(rule)

    async def _process_email_sequences(self):
        """Process email sequences"""
        for sequence in self.email_sequences:
            if not sequence.active:
                continue
                
            # Find leads that match sequence criteria
            matching_leads = await self._find_sequence_leads(sequence)
            
            for lead in matching_leads:
                await self._send_sequence_email(sequence, lead)

    async def _update_lead_scores(self):
        """Update lead scores based on recent activity"""
        for lead_id, lead in self.leads.items():
            if lead.status in [LeadStatus.NEW, LeadStatus.QUALIFIED]:
                new_score = await self._calculate_lead_score(lead)
                if lead_id in self.lead_scores:
                    self.lead_scores[lead_id].score = new_score
                else:
                    self.lead_scores[lead_id] = LeadScore(lead_id=lead_id, score=new_score)

    async def _process_follow_ups(self):
        """Process scheduled follow-ups"""
        current_time = datetime.utcnow()
        
        for lead_id, lead in self.leads.items():
            if lead.next_follow_up and lead.next_follow_up <= current_time:
                await self._send_follow_up(lead)
                lead.next_follow_up = None

    async def _calculate_lead_score(self, lead: Lead, additional_data: Optional[Dict[str, Any]] = None) -> int:
        """Calculate lead score based on various factors"""
        score = 0
        
        # Company size scoring
        if lead.company_size == "1000+":
            score += 20
        elif lead.company_size == "500-999":
            score += 15
        elif lead.company_size == "100-499":
            score += 10
        elif lead.company_size == "50-99":
            score += 5
        
        # Job title scoring
        if lead.job_title.lower() in ["cto", "cio", "vp engineering", "director"]:
            score += 25
        elif lead.job_title.lower() in ["manager", "lead", "senior"]:
            score += 15
        elif lead.job_title.lower() in ["developer", "engineer"]:
            score += 10
        
        # Industry scoring
        if lead.industry.lower() in ["technology", "software", "ai", "machine learning"]:
            score += 15
        elif lead.industry.lower() in ["finance", "healthcare", "manufacturing"]:
            score += 10
        
        # Website presence
        if lead.website:
            score += 5
        
        # Additional data scoring
        if additional_data:
            if additional_data.get("budget") == "100k+":
                score += 20
            elif additional_data.get("budget") == "50k-100k":
                score += 15
            elif additional_data.get("budget") == "25k-50k":
                score += 10
        
        return min(score, 100)  # Cap at 100

    async def _check_rule_conditions(self, rule: AutomationRule) -> bool:
        """Check if automation rule conditions are met"""
        # Basic condition checking - can be extended with more complex logic
        return True

    async def _execute_rule_actions(self, rule: AutomationRule):
        """Execute automation rule actions"""
        for action in rule.actions:
            try:
                action_type = action.get("type")
                if action_type == "send_email":
                    await self._send_automated_email(action, rule)
                elif action_type == "update_lead":
                    await self._update_lead_from_action(action, rule)
                elif action_type == "schedule_follow_up":
                    await self._schedule_follow_up(action, rule)
                    
            except Exception as e:
                logger.error(f"Error executing action {action}: {e}")

    async def _find_sequence_leads(self, sequence: EmailSequence) -> List[Lead]:
        """Find leads that match email sequence criteria"""
        matching_leads = []
        
        for lead in self.leads.values():
            if await self._lead_matches_sequence(lead, sequence):
                matching_leads.append(lead)
        
        return matching_leads

    async def _lead_matches_sequence(self, lead: Lead, sequence: EmailSequence) -> bool:
        """Check if lead matches email sequence criteria"""
        # Basic matching logic - can be extended
        return True

    async def _send_sequence_email(self, sequence: EmailSequence, lead: Lead):
        """Send email from sequence to lead"""
        # Implementation would integrate with email service
        logger.info(f"Would send sequence email to {lead.email}")

    async def _send_follow_up(self, lead: Lead):
        """Send follow-up to lead"""
        # Implementation would integrate with email service
        logger.info(f"Would send follow-up to {lead.email}")

    async def _send_automated_email(self, action: Dict[str, Any], rule: AutomationRule):
        """Send automated email based on action"""
        # Implementation would integrate with email service
        logger.info(f"Would send automated email for rule {rule.name}")

    async def _update_lead_from_action(self, action: Dict[str, Any], rule: AutomationRule):
        """Update lead based on action"""
        # Implementation would update lead data
        logger.info(f"Would update lead for rule {rule.name}")

    async def _schedule_follow_up(self, action: Dict[str, Any], rule: AutomationRule):
        """Schedule follow-up based on action"""
        # Implementation would schedule follow-up
        logger.info(f"Would schedule follow-up for rule {rule.name}")

    async def _check_status_change_triggers(self, lead: Lead, new_status: str):
        """Check for triggers based on status change"""
        if new_status == LeadStatus.QUALIFIED:
            await self._trigger_event(TriggerEvent.LEAD_QUALIFIED, lead)
        elif new_status == LeadStatus.DEMO_SCHEDULED:
            await self._trigger_event(TriggerEvent.DEMO_SCHEDULED, lead)

    # Database storage methods
    async def _store_lead(self, lead: Lead):
        """Store lead in database"""
        # Implementation would store in database
        pass

    async def _store_automation_rule(self, rule: AutomationRule):
        """Store automation rule in database"""
        # Implementation would store in database
        pass

    async def _store_email_sequence(self, sequence: EmailSequence):
        """Store email sequence in database"""
        # Implementation would store in database
        pass

    async def _store_conversion_event(self, event: ConversionEvent):
        """Store conversion event in database"""
        # Implementation would store in database
        pass

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Get lead by ID"""
        return self.leads.get(lead_id)

    def get_leads_by_status(self, status: LeadStatus) -> List[Lead]:
        """Get leads by status"""
        return [lead for lead in self.leads.values() if lead.status == status]

    def get_lead_score(self, lead_id: str) -> Optional[int]:
        """Get lead score by ID"""
        if lead_id in self.lead_scores:
            return self.lead_scores[lead_id].score
        return None

    def get_campaign_metrics(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign metrics"""
        campaign = next((c for c in self.campaigns if c.id == campaign_id), None)
        if campaign:
            return campaign.metrics
        return {}
