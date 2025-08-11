"""Pydantic models for marketing service API."""

from pydantic import BaseModel, Field, EmailStr
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4

from .sales_funnel import SalesFunnel, FunnelStage
from .lead_management import Lead, LeadStage, LeadPriority, LeadSource
from .email_service import EmailCampaign, EmailTemplate
from .a_b_testing import Experiment, Variant


# Lead Models
class LeadCreate(BaseModel):
    """Create lead request model."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    annual_revenue: Optional[str] = Field(None, max_length=50)
    lead_source: LeadSource = LeadSource.WEBSITE
    notes: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class LeadUpdate(BaseModel):
    """Update lead request model."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    annual_revenue: Optional[str] = Field(None, max_length=50)
    lead_source: Optional[LeadSource] = None
    lead_score: Optional[int] = Field(None, ge=0, le=100)
    priority: Optional[LeadPriority] = None
    stage: Optional[LeadStage] = None
    assigned_to: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class LeadResponse(BaseModel):
    """Lead response model."""
    id: str
    email: str
    first_name: str
    last_name: str
    company: Optional[str]
    job_title: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    industry: Optional[str]
    company_size: Optional[str]
    annual_revenue: Optional[str]
    lead_source: str
    lead_score: int
    priority: str
    stage: str
    assigned_to: Optional[str]
    notes: Optional[str]
    tags: List[str]
    custom_fields: Dict[str, Any]
    last_contact: Optional[datetime]
    next_follow_up: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_lead(cls, lead: Lead) -> "LeadResponse":
        """Create response model from Lead object."""
        return cls(
            id=lead.id,
            email=lead.email,
            first_name=lead.first_name,
            last_name=lead.last_name,
            company=lead.company,
            job_title=lead.job_title,
            phone=lead.phone,
            website=lead.website,
            industry=lead.industry,
            company_size=lead.company_size,
            annual_revenue=lead.annual_revenue,
            lead_source=lead.lead_source.value,
            lead_score=lead.lead_score,
            priority=lead.priority.value,
            stage=lead.stage.value,
            assigned_to=lead.assigned_to,
            notes=lead.notes,
            tags=lead.tags,
            custom_fields=lead.custom_fields,
            last_contact=lead.last_contact,
            next_follow_up=lead.next_follow_up,
            created_at=lead.created_at,
            updated_at=lead.updated_at
        )


class LeadListResponse(BaseModel):
    """Lead list response model."""
    leads: List[LeadResponse]
    total: int
    limit: int
    offset: int


# Sales Funnel Models
class FunnelStageCreate(BaseModel):
    """Create funnel stage request model."""
    name: str = Field(..., min_length=1, max_length=100)
    order: int = Field(..., ge=0)
    criteria: Dict[str, Any] = Field(default_factory=dict)
    conversion_rate: float = Field(0.0, ge=0.0, le=1.0)


class SalesFunnelCreate(BaseModel):
    """Create sales funnel request model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    stages: List[FunnelStageCreate] = Field(..., min_items=2)
    target_audience: Dict[str, Any] = Field(default_factory=dict)
    conversion_goals: Dict[str, Any] = Field(default_factory=dict)
    active: bool = True


class SalesFunnelResponse(BaseModel):
    """Sales funnel response model."""
    id: str
    name: str
    description: Optional[str]
    stages: List[Dict[str, Any]]
    target_audience: Dict[str, Any]
    conversion_goals: Dict[str, Any]
    active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_funnel(cls, funnel: SalesFunnel) -> "SalesFunnelResponse":
        """Create response model from SalesFunnel object."""
        return cls(
            id=funnel.id,
            name=funnel.name,
            description=funnel.description,
            stages=[{
                "id": stage.id,
                "name": stage.name,
                "order": stage.order,
                "criteria": stage.criteria,
                "conversion_rate": stage.conversion_rate,
                "total_entries": stage.total_entries,
                "total_exits": stage.total_exits
            } for stage in funnel.stages],
            target_audience=funnel.target_audience,
            conversion_goals=funnel.conversion_goals,
            active=funnel.active,
            created_at=funnel.created_at,
            updated_at=funnel.updated_at
        )


# Email Service Models
class EmailTemplateCreate(BaseModel):
    """Create email template request model."""
    name: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=200)
    html_content: str = Field(..., min_length=1)
    text_content: Optional[str] = None
    variables: List[str] = Field(default_factory=list)
    category: str = Field(..., max_length=100)
    active: bool = True


class EmailCampaignCreate(BaseModel):
    """Create email campaign request model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    template_id: str
    subject_line: str = Field(..., min_length=1, max_length=200)
    sender_name: str = Field(..., min_length=1, max_length=100)
    sender_email: EmailStr
    reply_to: Optional[EmailStr] = None
    target_audience: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[datetime] = None


class EmailCampaignResponse(BaseModel):
    """Email campaign response model."""
    id: str
    name: str
    description: Optional[str]
    template_id: str
    subject_line: str
    sender_name: str
    sender_email: str
    reply_to: Optional[str]
    target_audience: Dict[str, Any]
    schedule: Optional[datetime]
    status: str
    metrics: Dict[str, Any]
    created_at: datetime

    @classmethod
    def from_campaign(cls, campaign: EmailCampaign) -> "EmailCampaignResponse":
        """Create response model from EmailCampaign object."""
        return cls(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            template_id=campaign.template_id,
            subject_line=campaign.subject_line,
            sender_name=campaign.sender_name,
            sender_email=campaign.sender_email,
            reply_to=campaign.reply_to,
            target_audience=campaign.target_audience,
            schedule=campaign.schedule,
            status=campaign.status.value,
            metrics=campaign.metrics,
            created_at=campaign.created_at
        )


# A/B Testing Models
class VariantCreate(BaseModel):
    """Create A/B test variant request model."""
    name: str = Field(..., min_length=1, max_length=100)
    variant_type: str = Field(..., regex="^(control|variant)$")
    content: Dict[str, Any] = Field(default_factory=dict)
    traffic_percentage: float = Field(0.0, ge=0.0, le=1.0)


class ExperimentCreate(BaseModel):
    """Create A/B test experiment request model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    hypothesis: str = Field(..., min_length=1, max_length=500)
    variants: List[VariantCreate] = Field(..., min_items=2)
    traffic_split: Dict[str, float] = Field(default_factory=dict)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sample_size: Optional[int] = Field(None, gt=0)
    confidence_level: float = Field(0.95, ge=0.8, le=0.99)
    primary_metric: str = Field(..., min_length=1, max_length=100)
    secondary_metrics: List[str] = Field(default_factory=list)
    target_audience: Dict[str, Any] = Field(default_factory=dict)


class ExperimentResponse(BaseModel):
    """A/B test experiment response model."""
    id: str
    name: str
    description: Optional[str]
    hypothesis: str
    status: str
    variants: List[Dict[str, Any]]
    traffic_split: Dict[str, float]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    sample_size: Optional[int]
    confidence_level: float
    primary_metric: str
    secondary_metrics: List[str]
    target_audience: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_experiment(cls, experiment: Experiment) -> "ExperimentResponse":
        """Create response model from Experiment object."""
        return cls(
            id=experiment.id,
            name=experiment.name,
            description=experiment.description,
            hypothesis=experiment.hypothesis,
            status=experiment.status.value,
            variants=[{
                "id": variant.id,
                "name": variant.name,
                "variant_type": variant.variant_type.value,
                "content": variant.content,
                "traffic_percentage": variant.traffic_percentage,
                "is_winner": variant.is_winner,
                "metrics": variant.metrics
            } for variant in experiment.variants],
            traffic_split=experiment.traffic_split,
            start_date=experiment.start_date,
            end_date=experiment.end_date,
            sample_size=experiment.sample_size,
            confidence_level=experiment.confidence_level,
            primary_metric=experiment.primary_metric,
            secondary_metrics=experiment.secondary_metrics,
            target_audience=experiment.target_audience,
            created_at=experiment.created_at,
            updated_at=experiment.updated_at
        )


# Analytics Models
class ConversionMetrics(BaseModel):
    """Conversion metrics model."""
    total_conversions: int
    conversion_rate: float
    revenue: float
    average_order_value: float
    time_period: timedelta


class FunnelMetrics(BaseModel):
    """Funnel metrics model."""
    funnel_id: str
    total_entries: int
    total_conversions: int
    overall_conversion_rate: float
    stage_metrics: List[Dict[str, Any]]
    time_period: timedelta


# CRM Integration Models
class CRMSyncRequest(BaseModel):
    """CRM sync request model."""
    provider: str = Field(..., min_length=1, max_length=50)
    data_type: str = Field(..., regex="^(contacts|opportunities)$")
    data: List[Dict[str, Any]] = Field(..., min_items=1)
    sync_options: Dict[str, Any] = Field(default_factory=dict)


class CRMSyncResponse(BaseModel):
    """CRM sync response model."""
    success: bool
    contacts_synced: int
    opportunities_synced: int
    errors: List[str]
    sync_timestamp: datetime


# Automation Models
class AutomationRuleCreate(BaseModel):
    """Create automation rule request model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    trigger_conditions: Dict[str, Any] = Field(..., min_items=1)
    actions: List[Dict[str, Any]] = Field(..., min_items=1)
    active: bool = True
    priority: int = Field(0, ge=0, le=100)


class EmailSequenceCreate(BaseModel):
    """Create email sequence request model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    trigger_event: str = Field(..., min_length=1, max_length=100)
    emails: List[Dict[str, Any]] = Field(..., min_items=1)
    delay_between_emails: int = Field(..., ge=1)  # hours
    active: bool = True
