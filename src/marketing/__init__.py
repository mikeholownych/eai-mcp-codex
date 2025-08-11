"""Marketing automation and sales funnel management module."""

from .automation import (
    MarketingAutomation,
    EmailSequence,
    TriggerEvent,
    AutomationRule,
    Campaign,
    Lead,
    LeadScore,
    ConversionEvent,
)
from .email_service import EmailService, EmailTemplate, EmailCampaign
from .lead_management import LeadManager, LeadQualification, LeadScoring
from .crm_integration import CRMIntegration, SalesforceIntegration, HubSpotIntegration
from .analytics import MarketingAnalytics, ConversionTracker, FunnelAnalytics
from .a_b_testing import ABTesting, Experiment, Variant, TestResult
from .sales_funnel import SalesFunnelManager, SalesFunnel, FunnelStage, LeadJourney

__all__ = [
    "MarketingAutomation",
    "EmailSequence",
    "TriggerEvent",
    "AutomationRule",
    "Campaign",
    "Lead",
    "LeadScore",
    "ConversionEvent",
    "EmailService",
    "EmailTemplate",
    "EmailCampaign",
    "LeadManager",
    "LeadQualification",
    "LeadScoring",
    "CRMIntegration",
    "SalesforceIntegration",
    "HubSpotIntegration",
    "MarketingAnalytics",
    "ConversionTracker",
    "FunnelAnalytics",
    "ABTesting",
    "Experiment",
    "Variant",
    "TestResult",
    "SalesFunnelManager",
    "SalesFunnel",
    "FunnelStage",
    "LeadJourney",
]
