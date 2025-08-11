"""
Lead management system for marketing and sales funnel.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from uuid import uuid4
import json
from enum import Enum

from ..common.redis_client import RedisClient
from ..common.database import DatabaseManager

logger = logging.getLogger(__name__)


class LeadSource(str, Enum):
    """Lead source values"""
    WEBSITE = "website"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    REFERRAL = "referral"
    PAID_ADS = "paid_ads"
    CONTENT_MARKETING = "content_marketing"
    EVENTS = "events"
    COLD_OUTREACH = "cold_outreach"
    PARTNER = "partner"
    OTHER = "other"


class LeadPriority(str, Enum):
    """Lead priority values"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class LeadStage(str, Enum):
    """Lead stage values"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


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
    annual_revenue: str = ""
    lead_source: LeadSource = LeadSource.WEBSITE
    lead_score: int = 0
    priority: LeadPriority = LeadPriority.MEDIUM
    stage: LeadStage = LeadStage.NEW
    assigned_to: str = ""
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    last_contact: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LeadActivity:
    """Lead activity tracking"""
    id: str = field(default_factory=lambda: str(uuid4()))
    lead_id: str = ""
    activity_type: str = ""
    description: str = ""
    user_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LeadQualification:
    """Lead qualification criteria"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    criteria: Dict[str, Any] = field(default_factory=dict)
    score_weight: int = 0
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LeadScore:
    """Lead scoring configuration"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    criteria: Dict[str, Any] = field(default_factory=dict)
    score_value: int = 0
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


class LeadManager:
    """Lead management system"""

    def __init__(self, redis_client: RedisClient, database_manager: DatabaseManager):
        self.redis_client = redis_client
        self.database_manager = database_manager
        
        # Lead storage
        self.leads: Dict[str, Lead] = {}
        
        # Lead activities
        self.activities: Dict[str, List[LeadActivity]] = {}
        
        # Qualification criteria
        self.qualification_criteria: List[LeadQualification] = []
        
        # Scoring rules
        self.scoring_rules: List[LeadScore] = []
        
        # Lead pipeline stages
        self.pipeline_stages = {
            LeadStage.NEW: {"name": "New Leads", "color": "#3B82F6"},
            LeadStage.CONTACTED: {"name": "Contacted", "color": "#8B5CF6"},
            LeadStage.QUALIFIED: {"name": "Qualified", "color": "#10B981"},
            LeadStage.PROPOSAL: {"name": "Proposal", "color": "#F59E0B"},
            LeadStage.NEGOTIATION: {"name": "Negotiation", "color": "#EF4444"},
            LeadStage.CLOSED_WON: {"name": "Closed Won", "color": "#059669"},
            LeadStage.CLOSED_LOST: {"name": "Closed Lost", "color": "#6B7280"}
        }

    async def create_lead(self, lead_data: Dict[str, Any]) -> Lead:
        """Create a new lead"""
        # Generate lead ID
        lead_id = str(uuid4())
        lead_data["id"] = lead_id
        
        # Set default values
        lead_data.setdefault("created_at", datetime.utcnow())
        lead_data.setdefault("updated_at", datetime.utcnow())
        lead_data.setdefault("stage", LeadStage.NEW)
        lead_data.setdefault("lead_score", 0)
        lead_data.setdefault("priority", LeadPriority.MEDIUM)
        
        # Create lead object
        lead = Lead(**lead_data)
        
        # Store lead
        self.leads[lead_id] = lead
        
        # Initialize activities list
        self.activities[lead_id] = []
        
        # Add creation activity
        await self.add_activity(lead_id, "lead_created", "Lead created", "system")
        
        # Auto-qualify lead
        await self.qualify_lead(lead_id)
        
        # Auto-score lead
        await self.score_lead(lead_id)
        
        logger.info(f"Created new lead: {lead.email} ({lead_id})")
        return lead

    async def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> Optional[Lead]:
        """Update lead information"""
        if lead_id not in self.leads:
            logger.error(f"Lead not found: {lead_id}")
            return None
        
        lead = self.leads[lead_id]
        
        # Track changes for activity log
        changes = []
        for key, value in updates.items():
            if hasattr(lead, key) and getattr(lead, key) != value:
                old_value = getattr(lead, key)
                changes.append(f"{key}: {old_value} → {value}")
                setattr(lead, key, value)
        
        # Update timestamp
        lead.updated_at = datetime.utcnow()
        
        # Log changes
        if changes:
            change_description = "; ".join(changes)
            await self.add_activity(lead_id, "lead_updated", f"Lead updated: {change_description}", "system")
        
        # Re-qualify and re-score if relevant fields changed
        if any(key in updates for key in ["company", "industry", "company_size", "annual_revenue"]):
            await self.qualify_lead(lead_id)
        
        if any(key in updates for key in ["company", "industry", "company_size", "annual_revenue", "lead_source"]):
            await self.score_lead(lead_id)
        
        logger.info(f"Updated lead: {lead.email} ({lead_id})")
        return lead

    async def delete_lead(self, lead_id: str) -> bool:
        """Delete a lead"""
        if lead_id not in self.leads:
            logger.error(f"Lead not found: {lead_id}")
            return False
        
        # Remove lead
        lead_email = self.leads[lead_id].email
        del self.leads[lead_id]
        
        # Remove activities
        if lead_id in self.activities:
            del self.activities[lead_id]
        
        logger.info(f"Deleted lead: {lead_email} ({lead_id})")
        return True

    async def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Get lead by ID"""
        return self.leads.get(lead_id)

    async def search_leads(self, filters: Dict[str, Any] = None, 
                          sort_by: str = "created_at", sort_order: str = "desc",
                          limit: int = 100, offset: int = 0) -> List[Lead]:
        """Search leads with filters"""
        leads = list(self.leads.values())
        
        # Apply filters
        if filters:
            filtered_leads = []
            for lead in leads:
                match = True
                for key, value in filters.items():
                    if hasattr(lead, key):
                        lead_value = getattr(lead, key)
                        if isinstance(value, (list, tuple)):
                            if lead_value not in value:
                                match = False
                                break
                        elif lead_value != value:
                            match = False
                            break
                    else:
                        match = False
                        break
                
                if match:
                    filtered_leads.append(lead)
            
            leads = filtered_leads
        
        # Sort leads
        reverse = sort_order.lower() == "desc"
        if sort_by == "lead_score":
            leads.sort(key=lambda x: x.lead_score, reverse=reverse)
        elif sort_by == "priority":
            priority_order = {LeadPriority.LOW: 1, LeadPriority.MEDIUM: 2, 
                            LeadPriority.HIGH: 3, LeadPriority.URGENT: 4}
            leads.sort(key=lambda x: priority_order.get(x.priority, 0), reverse=reverse)
        elif sort_by == "stage":
            stage_order = {LeadStage.NEW: 1, LeadStage.CONTACTED: 2, LeadStage.QUALIFIED: 3,
                          LeadStage.PROPOSAL: 4, LeadStage.NEGOTIATION: 5, 
                          LeadStage.CLOSED_WON: 6, LeadStage.CLOSED_LOST: 7}
            leads.sort(key=lambda x: stage_order.get(x.stage, 0), reverse=reverse)
        else:
            leads.sort(key=lambda x: getattr(x, sort_by, x.created_at), reverse=reverse)
        
        # Apply pagination
        return leads[offset:offset + limit]

    async def add_activity(self, lead_id: str, activity_type: str, description: str, 
                          user_id: str = "system", metadata: Dict[str, Any] = None) -> LeadActivity:
        """Add activity to lead"""
        if lead_id not in self.leads:
            logger.error(f"Lead not found: {lead_id}")
            return None
        
        activity = LeadActivity(
            lead_id=lead_id,
            activity_type=activity_type,
            description=description,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        if lead_id not in self.activities:
            self.activities[lead_id] = []
        
        self.activities[lead_id].append(activity)
        
        logger.info(f"Added activity to lead {lead_id}: {activity_type}")
        return activity

    async def get_lead_activities(self, lead_id: str, limit: int = 50) -> List[LeadActivity]:
        """Get activities for a lead"""
        if lead_id not in self.activities:
            return []
        
        activities = self.activities[lead_id]
        return sorted(activities, key=lambda x: x.created_at, reverse=True)[:limit]

    async def qualify_lead(self, lead_id: str) -> bool:
        """Qualify lead based on criteria"""
        if lead_id not in self.leads:
            return False
        
        lead = self.leads[lead_id]
        
        # Apply qualification criteria
        qualification_score = 0
        for criteria in self.qualification_criteria:
            if not criteria.active:
                continue
            
            if self._meets_criteria(lead, criteria.criteria):
                qualification_score += criteria.score_weight
        
        # Determine if qualified (score >= 50)
        is_qualified = qualification_score >= 50
        
        # Update lead stage if qualified
        if is_qualified and lead.stage == LeadStage.NEW:
            lead.stage = LeadStage.QUALIFIED
            lead.updated_at = datetime.utcnow()
            
            await self.add_activity(
                lead_id, 
                "lead_qualified", 
                f"Lead qualified with score: {qualification_score}", 
                "system"
            )
        
        logger.info(f"Lead {lead_id} qualification: score={qualification_score}, qualified={is_qualified}")
        return is_qualified

    async def score_lead(self, lead_id: str) -> int:
        """Score lead based on scoring rules"""
        if lead_id not in self.leads:
            return 0
        
        lead = self.leads[lead_id]
        
        # Apply scoring rules
        total_score = 0
        for rule in self.scoring_rules:
            if not rule.active:
                continue
            
            if self._meets_scoring_conditions(lead, rule.conditions):
                total_score += rule.score_value
        
        # Update lead score
        lead.lead_score = total_score
        lead.updated_at = datetime.utcnow()
        
        # Update priority based on score
        if total_score >= 80:
            lead.priority = LeadPriority.URGENT
        elif total_score >= 60:
            lead.priority = LeadPriority.HIGH
        elif total_score >= 40:
            lead.priority = LeadPriority.MEDIUM
        else:
            lead.priority = LeadPriority.LOW
        
        logger.info(f"Lead {lead_id} scored: {total_score}, priority: {lead.priority}")
        return total_score

    def _meets_criteria(self, lead: Lead, criteria: Dict[str, Any]) -> bool:
        """Check if lead meets qualification criteria"""
        for field, condition in criteria.items():
            if not hasattr(lead, field):
                continue
            
            lead_value = getattr(lead, field)
            
            if isinstance(condition, dict):
                # Complex condition
                if "min" in condition and lead_value < condition["min"]:
                    return False
                if "max" in condition and lead_value > condition["max"]:
                    return False
                if "values" in condition and lead_value not in condition["values"]:
                    return False
            elif isinstance(condition, (list, tuple)):
                # List of allowed values
                if lead_value not in condition:
                    return False
            else:
                # Exact match
                if lead_value != condition:
                    return False
        
        return True

    def _meets_scoring_conditions(self, lead: Lead, conditions: List[Dict[str, Any]]) -> bool:
        """Check if lead meets scoring conditions"""
        for condition in conditions:
            if not self._meets_criteria(lead, condition):
                return False
        return True

    async def move_lead_stage(self, lead_id: str, new_stage: LeadStage, 
                             user_id: str = "system", notes: str = "") -> bool:
        """Move lead to new stage"""
        if lead_id not in self.leads:
            return False
        
        lead = self.leads[lead_id]
        old_stage = lead.stage
        
        # Update stage
        lead.stage = new_stage
        lead.updated_at = datetime.utcnow()
        
        # Add activity
        activity_description = f"Lead moved from {old_stage} to {new_stage}"
        if notes:
            activity_description += f": {notes}"
        
        await self.add_activity(lead_id, "stage_changed", activity_description, user_id)
        
        logger.info(f"Lead {lead_id} moved from {old_stage} to {new_stage}")
        return True

    async def assign_lead(self, lead_id: str, user_id: str) -> bool:
        """Assign lead to user"""
        if lead_id not in self.leads:
            return False
        
        lead = self.leads[lead_id]
        old_assignee = lead.assigned_to
        
        # Update assignment
        lead.assigned_to = user_id
        lead.updated_at = datetime.utcnow()
        
        # Add activity
        if old_assignee:
            activity_description = f"Lead reassigned from {old_assignee} to {user_id}"
        else:
            activity_description = f"Lead assigned to {user_id}"
        
        await self.add_activity(lead_id, "lead_assigned", activity_description, user_id)
        
        logger.info(f"Lead {lead_id} assigned to {user_id}")
        return True

    async def schedule_follow_up(self, lead_id: str, follow_up_date: datetime, 
                                user_id: str = "system", notes: str = "") -> bool:
        """Schedule follow-up for lead"""
        if lead_id not in self.leads:
            return False
        
        lead = self.leads[lead_id]
        lead.next_follow_up = follow_up_date
        lead.updated_at = datetime.utcnow()
        
        # Add activity
        activity_description = f"Follow-up scheduled for {follow_up_date.strftime('%Y-%m-%d %H:%M')}"
        if notes:
            activity_description += f": {notes}"
        
        await self.add_activity(lead_id, "follow_up_scheduled", activity_description, user_id)
        
        logger.info(f"Follow-up scheduled for lead {lead_id}: {follow_up_date}")
        return True

    async def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get pipeline summary by stage"""
        summary = {}
        
        for stage in LeadStage:
            stage_leads = [lead for lead in self.leads.values() if lead.stage == stage]
            summary[stage.value] = {
                "count": len(stage_leads),
                "value": sum(lead.lead_score for lead in stage_leads),
                "leads": [{"id": lead.id, "email": lead.email, "company": lead.company} 
                         for lead in stage_leads[:10]]  # Top 10 leads per stage
            }
        
        return summary

    async def get_lead_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get lead analytics for specified period"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Filter leads by date
        recent_leads = [lead for lead in self.leads.values() 
                       if lead.created_at >= cutoff_date]
        
        # Calculate metrics
        total_leads = len(recent_leads)
        qualified_leads = len([lead for lead in recent_leads 
                             if lead.stage in [LeadStage.QUALIFIED, LeadStage.PROPOSAL, 
                                             LeadStage.NEGOTIATION, LeadStage.CLOSED_WON]])
        converted_leads = len([lead for lead in recent_leads 
                             if lead.stage == LeadStage.CLOSED_WON])
        
        # Calculate conversion rates
        qualification_rate = (qualified_leads / total_leads * 100) if total_leads > 0 else 0
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        # Lead source breakdown
        source_breakdown = {}
        for lead in recent_leads:
            source = lead.lead_source.value
            source_breakdown[source] = source_breakdown.get(source, 0) + 1
        
        return {
            "period_days": days,
            "total_leads": total_leads,
            "qualified_leads": qualified_leads,
            "converted_leads": converted_leads,
            "qualification_rate": round(qualification_rate, 2),
            "conversion_rate": round(conversion_rate, 2),
            "source_breakdown": source_breakdown,
            "average_lead_score": sum(lead.lead_score for lead in recent_leads) / total_leads if total_leads > 0 else 0
        }

    async def add_qualification_criteria(self, criteria_data: Dict[str, Any]) -> LeadQualification:
        """Add qualification criteria"""
        criteria = LeadQualification(**criteria_data)
        self.qualification_criteria.append(criteria)
        
        logger.info(f"Added qualification criteria: {criteria.name}")
        return criteria

    async def add_scoring_rule(self, rule_data: Dict[str, Any]) -> LeadScore:
        """Add scoring rule"""
        rule = LeadScore(**rule_data)
        self.scoring_rules.append(rule)
        
        logger.info(f"Added scoring rule: {rule.name}")
        return rule

    def get_pipeline_stages(self) -> Dict[str, Dict[str, str]]:
        """Get pipeline stages configuration"""
        return self.pipeline_stages
