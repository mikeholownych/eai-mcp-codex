"""Unit tests for marketing service."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from src.marketing.sales_funnel import SalesFunnelManager, SalesFunnel, FunnelStage
from src.marketing.lead_management import LeadManager, Lead, LeadStage, LeadPriority, LeadSource
from src.marketing.email_service import EmailService, EmailCampaign, EmailTemplate
from src.marketing.analytics import MarketingAnalytics, ConversionEvent
from src.marketing.a_b_testing import ABTesting, Experiment, Variant, TestStatus
from src.marketing.crm_integration import CRMIntegration, CRMContact
from src.marketing.automation import MarketingAutomation


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = Mock()
    redis.hset = AsyncMock()
    redis.hget = AsyncMock()
    redis.hgetall = AsyncMock()
    redis.delete = AsyncMock()
    redis.close = AsyncMock()
    return redis


@pytest.fixture
def mock_db():
    """Mock database manager."""
    db = Mock()
    db.execute_query = AsyncMock()
    db.execute_update = AsyncMock()
    db.disconnect = AsyncMock()
    return db


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company": "Test Corp",
        "job_title": "Manager",
        "lead_source": LeadSource.WEBSITE,
        "priority": LeadPriority.MEDIUM,
        "stage": LeadStage.NEW
    }


@pytest.fixture
def sample_funnel_data():
    """Sample funnel data for testing."""
    return {
        "name": "Test Funnel",
        "description": "Test sales funnel",
        "stages": [
            {"name": "Awareness", "order": 1, "criteria": {}},
            {"name": "Interest", "order": 2, "criteria": {}},
            {"name": "Decision", "order": 3, "criteria": {}}
        ],
        "target_audience": {"industry": "technology"},
        "conversion_goals": {"target_conversion_rate": 0.05}
    }


class TestLeadManager:
    """Test LeadManager class."""
    
    @pytest.mark.asyncio
    async def test_create_lead(self, mock_redis, mock_db, sample_lead_data):
        """Test creating a new lead."""
        lead_manager = LeadManager(mock_redis, mock_db)
        
        lead = await lead_manager.create_lead(sample_lead_data)
        
        assert lead.email == sample_lead_data["email"]
        assert lead.first_name == sample_lead_data["first_name"]
        assert lead.last_name == sample_lead_data["last_name"]
        assert lead.company == sample_lead_data["company"]
        assert lead.lead_source == sample_lead_data["lead_source"]
        assert lead.priority == sample_lead_data["priority"]
        assert lead.stage == sample_lead_data["stage"]
        assert lead.id is not None
        assert lead.created_at is not None
    
    @pytest.mark.asyncio
    async def test_update_lead(self, mock_redis, mock_db, sample_lead_data):
        """Test updating a lead."""
        lead_manager = LeadManager(mock_redis, mock_db)
        
        # Create lead first
        lead = await lead_manager.create_lead(sample_lead_data)
        
        # Update lead
        updates = {"company": "Updated Corp", "priority": LeadPriority.HIGH}
        updated_lead = await lead_manager.update_lead(lead.id, updates)
        
        assert updated_lead.company == "Updated Corp"
        assert updated_lead.priority == LeadPriority.HIGH
        assert updated_lead.updated_at > lead.created_at
    
    @pytest.mark.asyncio
    async def test_qualify_lead(self, mock_redis, mock_db, sample_lead_data):
        """Test qualifying a lead."""
        lead_manager = LeadManager(mock_redis, mock_db)
        
        # Create lead
        lead = await lead_manager.create_lead(sample_lead_data)
        
        # Qualify lead
        success = await lead_manager.qualify_lead(lead.id)
        
        assert success is True
        # Lead should be moved to qualified stage
        updated_lead = await lead_manager.get_lead(lead.id)
        assert updated_lead.stage == LeadStage.QUALIFIED


class TestSalesFunnelManager:
    """Test SalesFunnelManager class."""
    
    @pytest.mark.asyncio
    async def test_create_sales_funnel(self, mock_redis, mock_db, sample_funnel_data):
        """Test creating a new sales funnel."""
        funnel_manager = SalesFunnelManager(mock_redis, mock_db)
        
        funnel = await funnel_manager.create_sales_funnel(sample_funnel_data)
        
        assert funnel.name == sample_funnel_data["name"]
        assert funnel.description == sample_funnel_data["description"]
        assert len(funnel.stages) == 3
        assert funnel.stages[0].name == "Awareness"
        assert funnel.stages[0].order == 1
        assert funnel.id is not None
        assert funnel.created_at is not None
    
    @pytest.mark.asyncio
    async def test_add_lead_to_funnel(self, mock_redis, mock_db, sample_funnel_data, sample_lead_data):
        """Test adding a lead to a funnel."""
        funnel_manager = SalesFunnelManager(mock_redis, mock_db)
        lead_manager = LeadManager(mock_redis, mock_db)
        
        # Create funnel and lead
        funnel = await funnel_manager.create_sales_funnel(sample_funnel_data)
        lead = await lead_manager.create_lead(sample_lead_data)
        
        # Add lead to funnel
        success = await funnel_manager.add_lead_to_funnel(funnel.id, sample_lead_data)
        
        assert success is True
        # Check if lead is in funnel
        funnel_leads = await funnel_manager.get_funnel_leads(funnel.id)
        assert len(funnel_leads) > 0


class TestEmailService:
    """Test EmailService class."""
    
    @pytest.mark.asyncio
    async def test_create_template(self, mock_redis):
        """Test creating an email template."""
        email_service = EmailService(mock_redis, {})
        
        template_data = {
            "name": "Welcome Template",
            "subject": "Welcome to our platform",
            "html_content": "<h1>Welcome!</h1>",
            "text_content": "Welcome!",
            "variables": ["first_name", "company"],
            "category": "onboarding"
        }
        
        template = await email_service.create_template(template_data)
        
        assert template.name == template_data["name"]
        assert template.subject == template_data["subject"]
        assert template.html_content == template_data["html_content"]
        assert template.id is not None
    
    @pytest.mark.asyncio
    async def test_create_campaign(self, mock_redis):
        """Test creating an email campaign."""
        email_service = EmailService(mock_redis, {})
        
        campaign_data = {
            "name": "Welcome Campaign",
            "description": "Welcome new users",
            "template_id": "template_123",
            "subject_line": "Welcome to our platform",
            "sender_name": "Marketing Team",
            "sender_email": "marketing@example.com",
            "target_audience": {"user_type": "new"}
        }
        
        campaign = await email_service.create_campaign(campaign_data)
        
        assert campaign.name == campaign_data["name"]
        assert campaign.template_id == campaign_data["template_id"]
        assert campaign.sender_email == campaign_data["sender_email"]
        assert campaign.id is not None


class TestMarketingAnalytics:
    """Test MarketingAnalytics class."""
    
    @pytest.mark.asyncio
    async def test_track_marketing_event(self, mock_redis, mock_db):
        """Test tracking a marketing event."""
        analytics = MarketingAnalytics(mock_redis, mock_db)
        
        event_data = {
            "lead_id": "lead_123",
            "event_type": "email_opened",
            "source": "email_campaign",
            "campaign_id": "campaign_123",
            "value": 1.0
        }
        
        success = await analytics.track_marketing_event(event_data)
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_get_campaign_performance(self, mock_redis, mock_db):
        """Test getting campaign performance metrics."""
        analytics = MarketingAnalytics(mock_redis, mock_db)
        
        campaign_id = "campaign_123"
        time_period = timedelta(days=30)
        
        performance = await analytics.get_campaign_performance(campaign_id, time_period)
        
        assert isinstance(performance, dict)
        assert "total_emails" in performance
        assert "open_rate" in performance
        assert "click_rate" in performance


class TestABTesting:
    """Test ABTesting class."""
    
    @pytest.mark.asyncio
    async def test_create_experiment(self, mock_redis, mock_db):
        """Test creating an A/B test experiment."""
        ab_testing = ABTesting(mock_redis, mock_db)
        
        experiment_data = {
            "name": "Button Color Test",
            "description": "Test different button colors",
            "hypothesis": "Red buttons will have higher conversion",
            "variants": [
                {"name": "Control", "variant_type": "control", "content": {"color": "blue"}},
                {"name": "Variant A", "variant_type": "variant", "content": {"color": "red"}}
            ],
            "primary_metric": "conversion_rate",
            "target_audience": {"user_type": "all"}
        }
        
        experiment = await ab_testing.create_experiment(experiment_data)
        
        assert experiment.name == experiment_data["name"]
        assert experiment.hypothesis == experiment_data["hypothesis"]
        assert len(experiment.variants) == 2
        assert experiment.status == TestStatus.DRAFT
    
    @pytest.mark.asyncio
    async def test_start_experiment(self, mock_redis, mock_db):
        """Test starting an experiment."""
        ab_testing = ABTesting(mock_redis, mock_db)
        
        # Create experiment first
        experiment_data = {
            "name": "Test Experiment",
            "hypothesis": "Test hypothesis",
            "variants": [
                {"name": "Control", "variant_type": "control", "content": {}},
                {"name": "Variant", "variant_type": "variant", "content": {}}
            ],
            "primary_metric": "conversion_rate"
        }
        
        experiment = await ab_testing.create_experiment(experiment_data)
        
        # Start experiment
        success = await ab_testing.start_experiment(experiment.id)
        
        assert success is True
        # Check if experiment is now active
        updated_experiment = ab_testing.experiments.get(experiment.id)
        assert updated_experiment.status == TestStatus.ACTIVE


class TestCRMIntegration:
    """Test CRMIntegration class."""
    
    @pytest.mark.asyncio
    async def test_get_provider(self, mock_redis):
        """Test getting CRM provider."""
        config = {
            "providers": {
                "salesforce": {"api_key": "test_key", "api_url": "https://api.salesforce.com"},
                "hubspot": {"api_key": "test_key", "api_url": "https://api.hubspot.com"}
            }
        }
        
        crm_integration = CRMIntegration(mock_redis, config)
        
        provider = await crm_integration.get_provider("salesforce")
        assert provider is not None
        assert provider.config["api_key"] == "test_key"
    
    @pytest.mark.asyncio
    async def test_sync_contacts(self, mock_redis):
        """Test syncing contacts with CRM."""
        config = {
            "providers": {
                "salesforce": {"api_key": "test_key", "api_url": "https://api.salesforce.com"}
            }
        }
        
        crm_integration = CRMIntegration(mock_redis, config)
        
        contacts = [
            {"email": "test1@example.com", "first_name": "John", "last_name": "Doe"},
            {"email": "test2@example.com", "first_name": "Jane", "last_name": "Smith"}
        ]
        
        result = await crm_integration.sync_contacts("salesforce", contacts)
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "contacts_synced" in result


class TestMarketingAutomation:
    """Test MarketingAutomation class."""
    
    @pytest.mark.asyncio
    async def test_add_automation_rule(self, mock_redis, mock_db):
        """Test adding an automation rule."""
        automation = MarketingAutomation(mock_redis, mock_db)
        
        rule_data = {
            "name": "Welcome Email Rule",
            "description": "Send welcome email to new leads",
            "trigger_conditions": {"event_type": "lead_created"},
            "actions": [{"action_type": "send_email", "template_id": "welcome_template"}],
            "active": True
        }
        
        await automation.add_automation_rule(rule_data)
        
        assert len(automation.automation_rules) > 0
        rule = automation.automation_rules[0]
        assert rule.name == rule_data["name"]
        assert rule.trigger_conditions == rule_data["trigger_conditions"]
    
    @pytest.mark.asyncio
    async def test_add_email_sequence(self, mock_redis, mock_db):
        """Test adding an email sequence."""
        automation = MarketingAutomation(mock_redis, mock_db)
        
        sequence_data = {
            "name": "Onboarding Sequence",
            "description": "Welcome sequence for new users",
            "trigger_event": "user_signup",
            "emails": [
                {"template_id": "welcome", "delay_hours": 0},
                {"template_id": "getting_started", "delay_hours": 24},
                {"template_id": "feature_highlight", "delay_hours": 72}
            ],
            "delay_between_emails": 24,
            "active": True
        }
        
        await automation.add_email_sequence(sequence_data)
        
        assert len(automation.email_sequences) > 0
        sequence = automation.email_sequences[0]
        assert sequence.name == sequence_data["name"]
        assert len(sequence.emails) == 3


# Integration tests
class TestMarketingServiceIntegration:
    """Integration tests for marketing service components."""
    
    @pytest.mark.asyncio
    async def test_lead_to_funnel_workflow(self, mock_redis, mock_db):
        """Test complete workflow from lead creation to funnel progression."""
        # Initialize components
        lead_manager = LeadManager(mock_redis, mock_db)
        funnel_manager = SalesFunnelManager(mock_redis, mock_db)
        analytics = MarketingAnalytics(mock_redis, mock_db)
        
        # Create lead
        lead_data = {
            "email": "workflow@example.com",
            "first_name": "Workflow",
            "last_name": "Test",
            "company": "Workflow Corp",
            "lead_source": LeadSource.WEBSITE
        }
        
        lead = await lead_manager.create_lead(lead_data)
        assert lead.id is not None
        
        # Create funnel
        funnel_data = {
            "name": "Workflow Funnel",
            "stages": [
                {"name": "Awareness", "order": 1, "criteria": {}},
                {"name": "Interest", "order": 2, "criteria": {}},
                {"name": "Decision", "order": 3, "criteria": {}}
            ]
        }
        
        funnel = await funnel_manager.create_sales_funnel(funnel_data)
        assert funnel.id is not None
        
        # Add lead to funnel
        success = await funnel_manager.add_lead_to_funnel(funnel.id, lead_data)
        assert success is True
        
        # Track funnel progress
        await funnel_manager.track_funnel_progress(funnel.id, lead.id, "Awareness")
        
        # Get funnel performance
        performance = await funnel_manager.get_funnel_performance(funnel.id, timedelta(days=30))
        assert "total_entries" in performance
        
        # Qualify lead
        await lead_manager.qualify_lead(lead.id)
        updated_lead = await lead_manager.get_lead(lead.id)
        assert updated_lead.stage == LeadStage.QUALIFIED
    
    @pytest.mark.asyncio
    async def test_email_campaign_workflow(self, mock_redis):
        """Test complete email campaign workflow."""
        email_service = EmailService(mock_redis, {})
        
        # Create template
        template_data = {
            "name": "Test Template",
            "subject": "Test Subject",
            "html_content": "<h1>Test</h1>",
            "category": "test"
        }
        
        template = await email_service.create_template(template_data)
        assert template.id is not None
        
        # Create campaign
        campaign_data = {
            "name": "Test Campaign",
            "template_id": template.id,
            "subject_line": "Test Campaign",
            "sender_name": "Test Sender",
            "sender_email": "test@example.com"
        }
        
        campaign = await email_service.create_campaign(campaign_data)
        assert campaign.id is not None
        
        # Send campaign
        recipients = [{"email": "recipient@example.com", "name": "Test Recipient"}]
        success = await email_service.send_campaign(campaign.id, recipients)
        assert success is True


if __name__ == "__main__":
    pytest.main([__file__])
