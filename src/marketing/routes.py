"""Marketing service API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.common.fastapi_auth import get_current_user, verify_staff_access
from .models import (
    LeadCreate, LeadUpdate, LeadResponse, LeadListResponse,
    SalesFunnelCreate, SalesFunnelResponse, FunnelStageCreate,
    EmailCampaignCreate, EmailCampaignResponse, EmailTemplateCreate,
    ExperimentCreate, ExperimentResponse, VariantCreate
)

router = APIRouter()

# Dependency to get marketing components from app state
def get_sales_funnel_manager(request: Request):
    return request.app.state.sales_funnel_manager

def get_automation(request: Request):
    return request.app.state.automation

def get_lead_manager(request: Request):
    return request.app.state.lead_manager

def get_email_service(request: Request):
    return request.app.state.email_service

def get_analytics(request: Request):
    return request.app.state.analytics

def get_ab_testing(request: Request):
    return request.app.state.ab_testing

def get_crm_integration(request: Request):
    return request.app.state.crm_integration


# Sales Funnel Routes
@router.post("/funnels", response_model=SalesFunnelResponse)
async def create_sales_funnel(
    funnel_data: SalesFunnelCreate,
    current_user: dict = Depends(get_current_user),
    funnel_manager = Depends(get_sales_funnel_manager)
):
    """Create a new sales funnel."""
    try:
        funnel = await funnel_manager.create_sales_funnel(funnel_data.dict())
        return SalesFunnelResponse.from_funnel(funnel)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/funnels", response_model=List[SalesFunnelResponse])
async def list_sales_funnels(
    current_user: dict = Depends(get_current_user),
    funnel_manager = Depends(get_sales_funnel_manager)
):
    """List all sales funnels."""
    try:
        funnels = list(funnel_manager.funnels.values())
        return [SalesFunnelResponse.from_funnel(funnel) for funnel in funnels]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/funnels/{funnel_id}", response_model=SalesFunnelResponse)
async def get_sales_funnel(
    funnel_id: str,
    current_user: dict = Depends(get_current_user),
    funnel_manager = Depends(get_sales_funnel_manager)
):
    """Get a specific sales funnel."""
    try:
        funnel = funnel_manager.funnels.get(funnel_id)
        if not funnel:
            raise HTTPException(status_code=404, detail="Funnel not found")
        return SalesFunnelResponse.from_funnel(funnel)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/funnels/{funnel_id}/leads")
async def add_lead_to_funnel(
    funnel_id: str,
    lead_data: LeadCreate,
    current_user: dict = Depends(get_current_user),
    funnel_manager = Depends(get_sales_funnel_manager)
):
    """Add a lead to a sales funnel."""
    try:
        success = await funnel_manager.add_lead_to_funnel(funnel_id, lead_data.dict())
        if success:
            return {"message": "Lead added to funnel successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add lead to funnel")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/funnels/{funnel_id}/performance")
async def get_funnel_performance(
    funnel_id: str,
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    funnel_manager = Depends(get_sales_funnel_manager)
):
    """Get funnel performance metrics."""
    try:
        time_period = timedelta(days=days)
        performance = await funnel_manager.get_funnel_performance(funnel_id, time_period)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Lead Management Routes
@router.post("/leads", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    current_user: dict = Depends(get_current_user),
    lead_manager = Depends(get_lead_manager)
):
    """Create a new lead."""
    try:
        lead = await lead_manager.create_lead(lead_data.dict())
        return LeadResponse.from_lead(lead)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/leads", response_model=LeadListResponse)
async def list_leads(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    lead_manager = Depends(get_lead_manager)
):
    """List leads with optional filtering."""
    try:
        filters = {"status": status} if status else {}
        leads = await lead_manager.search_leads(filters, limit=limit, offset=offset)
        return LeadListResponse(
            leads=[LeadResponse.from_lead(lead) for lead in leads],
            total=len(leads),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user),
    lead_manager = Depends(get_lead_manager)
):
    """Get a specific lead."""
    try:
        lead = await lead_manager.get_lead(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return LeadResponse.from_lead(lead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_data: LeadUpdate,
    current_user: dict = Depends(get_current_user),
    lead_manager = Depends(get_lead_manager)
):
    """Update a lead."""
    try:
        lead = await lead_manager.update_lead(lead_id, lead_data.dict(exclude_unset=True))
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return LeadResponse.from_lead(lead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leads/{lead_id}/qualify")
async def qualify_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user),
    lead_manager = Depends(get_lead_manager)
):
    """Qualify a lead."""
    try:
        success = await lead_manager.qualify_lead(lead_id)
        if success:
            return {"message": "Lead qualified successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to qualify lead")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Email Service Routes
@router.post("/email/templates", response_model=Dict[str, Any])
async def create_email_template(
    template_data: EmailTemplateCreate,
    current_user: dict = Depends(get_current_user),
    email_service = Depends(get_email_service)
):
    """Create an email template."""
    try:
        template = await email_service.create_template(template_data.dict())
        return {"message": "Template created successfully", "template_id": template.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/email/campaigns", response_model=EmailCampaignResponse)
async def create_email_campaign(
    campaign_data: EmailCampaignCreate,
    current_user: dict = Depends(get_current_user),
    email_service = Depends(get_email_service)
):
    """Create an email campaign."""
    try:
        campaign = await email_service.create_campaign(campaign_data.dict())
        return EmailCampaignResponse.from_campaign(campaign)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/email/campaigns/{campaign_id}/send")
async def send_email_campaign(
    campaign_id: str,
    recipients: List[Dict[str, str]],
    current_user: dict = Depends(get_current_user),
    email_service = Depends(get_email_service)
):
    """Send an email campaign."""
    try:
        success = await email_service.send_campaign(campaign_id, recipients)
        if success:
            return {"message": "Campaign sent successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to send campaign")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# A/B Testing Routes
@router.post("/ab-testing/experiments", response_model=ExperimentResponse)
async def create_experiment(
    experiment_data: ExperimentCreate,
    current_user: dict = Depends(get_current_user),
    ab_testing = Depends(get_ab_testing)
):
    """Create an A/B test experiment."""
    try:
        experiment = await ab_testing.create_experiment(experiment_data.dict())
        return ExperimentResponse.from_experiment(experiment)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ab-testing/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    current_user: dict = Depends(get_current_user),
    ab_testing = Depends(get_ab_testing)
):
    """Start an A/B test experiment."""
    try:
        success = await ab_testing.start_experiment(experiment_id)
        if success:
            return {"message": "Experiment started successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to start experiment")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ab-testing/experiments/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: str,
    current_user: dict = Depends(get_current_user),
    ab_testing = Depends(get_ab_testing)
):
    """Get A/B test experiment results."""
    try:
        results = await ab_testing.get_experiment_results(experiment_id)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Routes
@router.get("/analytics/dashboard")
async def get_marketing_dashboard(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    analytics = Depends(get_analytics)
):
    """Get marketing dashboard data."""
    try:
        time_period = timedelta(days=days)
        dashboard_data = await analytics.get_marketing_dashboard_data(time_period)
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/leads/{lead_id}/journey")
async def get_lead_journey(
    lead_id: str,
    current_user: dict = Depends(get_current_user),
    analytics = Depends(get_analytics)
):
    """Get lead journey analytics."""
    try:
        journey_data = await analytics.get_lead_journey(lead_id)
        return journey_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# CRM Integration Routes
@router.post("/crm/sync/{provider}")
async def sync_crm_data(
    provider: str,
    data_type: str,  # "contacts" or "opportunities"
    current_user: dict = Depends(get_current_user),
    crm_integration = Depends(get_crm_integration)
):
    """Sync data with CRM system."""
    try:
        if data_type == "contacts":
            # This would typically come from request body
            contacts = []
            result = await crm_integration.sync_contacts(provider, contacts)
        elif data_type == "opportunities":
            opportunities = []
            result = await crm_integration.sync_opportunities(provider, opportunities)
        else:
            raise HTTPException(status_code=400, detail="Invalid data type")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Automation Routes
@router.post("/automation/rules")
async def create_automation_rule(
    rule_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    automation = Depends(get_automation)
):
    """Create a marketing automation rule."""
    try:
        # This would need proper validation
        await automation.add_automation_rule(rule_data)
        return {"message": "Automation rule created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/automation/sequences")
async def create_email_sequence(
    sequence_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    automation = Depends(get_automation)
):
    """Create an email sequence."""
    try:
        await automation.add_email_sequence(sequence_data)
        return {"message": "Email sequence created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
