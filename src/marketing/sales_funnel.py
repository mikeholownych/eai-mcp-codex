"""
Sales funnel management system that orchestrates the complete customer journey.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from uuid import uuid4
import json

from .automation import MarketingAutomation, Lead, LeadStatus, CampaignType
from .lead_management import LeadManager, LeadQualification
from .email_service import EmailService, EmailCampaign
from .analytics import MarketingAnalytics, ConversionTracker, FunnelAnalytics
from .a_b_testing import ABTesting, Experiment, Variant
from .crm_integration import CRMIntegration

logger = logging.getLogger(__name__)


@dataclass
class FunnelStage:
    """Sales funnel stage definition"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    order: int = 0
    description: str = ""
    target_conversion_rate: float = 0.0
    current_conversion_rate: float = 0.0
    total_entries: int = 0
    total_exits: int = 0
    average_time_in_stage: Optional[timedelta] = None
    automation_rules: List[str] = field(default_factory=list)
    email_sequences: List[str] = field(default_factory=list)
    exit_criteria: Dict[str, Any] = field(default_factory=dict)
    entry_criteria: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SalesFunnel:
    """Complete sales funnel definition"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    stages: List[FunnelStage] = field(default_factory=list)
    target_audience: Dict[str, Any] = field(default_factory=dict)
    total_leads: int = 0
    total_conversions: int = 0
    overall_conversion_rate: float = 0.0
    average_time_to_convert: Optional[timedelta] = None
    revenue_target: Optional[float] = None
    current_revenue: float = 0.0
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LeadJourney:
    """Individual lead's journey through the sales funnel"""
    lead_id: str
    funnel_id: str
    current_stage: str
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    entry_date: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    total_touchpoints: int = 0
    conversion_probability: float = 0.0
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None


class SalesFunnelManager:
    """Manages the complete sales funnel and customer journey"""
    
    def __init__(self, redis_client, db_manager):
        self.redis_client = redis_client
        self.db_manager = db_manager
        
        # Initialize all marketing components
        self.automation = MarketingAutomation(redis_client, db_manager)
        self.lead_manager = LeadManager(redis_client, db_manager)
        self.email_service = EmailService(redis_client, db_manager)
        self.analytics = MarketingAnalytics(redis_client, db_manager)
        self.ab_testing = ABTesting(redis_client, db_manager)
        self.crm_integration = CRMIntegration(redis_client, db_manager)
        
        # Funnel management
        self.funnels: Dict[str, SalesFunnel] = {}
        self.lead_journeys: Dict[str, LeadJourney] = {}
        
    async def create_sales_funnel(self, funnel_data: Dict[str, Any]) -> SalesFunnel:
        """Create a new sales funnel"""
        try:
            # Create funnel stages
            stages = []
            for i, stage_data in enumerate(funnel_data.get("stages", [])):
                stage = FunnelStage(
                    name=stage_data["name"],
                    order=i,
                    description=stage_data.get("description", ""),
                    target_conversion_rate=stage_data.get("target_conversion_rate", 0.0),
                    automation_rules=stage_data.get("automation_rules", []),
                    email_sequences=stage_data.get("email_sequences", []),
                    exit_criteria=stage_data.get("exit_criteria", {}),
                    entry_criteria=stage_data.get("entry_criteria", {})
                )
                stages.append(stage)
            
            # Create funnel
            funnel = SalesFunnel(
                name=funnel_data["name"],
                description=funnel_data.get("description", ""),
                stages=stages,
                target_audience=funnel_data.get("target_audience", {}),
                revenue_target=funnel_data.get("revenue_target")
            )
            
            self.funnels[funnel.id] = funnel
            await self._store_funnel(funnel)
            
            logger.info(f"Created sales funnel: {funnel.name} with {len(stages)} stages")
            return funnel
            
        except Exception as e:
            logger.error(f"Failed to create sales funnel: {e}")
            raise
    
    async def add_lead_to_funnel(self, funnel_id: str, lead_data: Dict[str, Any]) -> bool:
        """Add a new lead to the sales funnel"""
        try:
            if funnel_id not in self.funnels:
                logger.error(f"Funnel not found: {funnel_id}")
                return False
            
            funnel = self.funnels[funnel_id]
            
            # Create lead
            lead = await self.automation.create_lead(lead_data)
            
            # Create lead journey
            journey = LeadJourney(
                lead_id=lead.id,
                funnel_id=funnel_id,
                current_stage=funnel.stages[0].name if funnel.stages else "unknown"
            )
            
            # Add to first stage
            if funnel.stages:
                first_stage = funnel.stages[0]
                first_stage.total_entries += 1
                
                # Track funnel progress
                await self.analytics.funnel_analytics.track_funnel_progress(
                    funnel_id, lead.id, first_stage.name
                )
                
                # Trigger stage entry automation
                await self._trigger_stage_entry_automation(funnel_id, lead.id, first_stage)
            
            # Store journey
            self.lead_journeys[lead.id] = journey
            await self._store_lead_journey(journey)
            
            # Update funnel metrics
            funnel.total_leads += 1
            await self._update_funnel_metrics(funnel_id)
            
            logger.info(f"Added lead {lead.id} to funnel {funnel.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add lead to funnel: {e}")
            return False
    
    async def advance_lead_stage(self, lead_id: str, new_stage: str, 
                                trigger_data: Optional[Dict[str, Any]] = None) -> bool:
        """Advance a lead to the next stage in the funnel"""
        try:
            if lead_id not in self.lead_journeys:
                logger.error(f"Lead journey not found: {lead_id}")
                return False
            
            journey = self.lead_journeys[lead_id]
            funnel = self.funnels.get(journey.funnel_id)
            
            if not funnel:
                logger.error(f"Funnel not found: {journey.funnel_id}")
                return False
            
            # Find current and new stage
            current_stage = next((s for s in funnel.stages if s.name == journey.current_stage), None)
            new_stage_obj = next((s for s in funnel.stages if s.name == new_stage), None)
            
            if not new_stage_obj:
                logger.error(f"Stage not found: {new_stage}")
                return False
            
            # Validate stage transition
            if not self._validate_stage_transition(current_stage, new_stage_obj, trigger_data):
                logger.warning(f"Invalid stage transition: {journey.current_stage} -> {new_stage}")
                return False
            
            # Update current stage metrics
            if current_stage:
                current_stage.total_exits += 1
            
            # Update new stage metrics
            new_stage_obj.total_entries += 1
            
            # Update lead journey
            journey.stage_history.append({
                "from_stage": journey.current_stage,
                "to_stage": new_stage,
                "timestamp": datetime.utcnow().isoformat(),
                "trigger": trigger_data
            })
            
            journey.current_stage = new_stage
            journey.last_activity = datetime.utcnow()
            
            # Track funnel progress
            await self.analytics.funnel_analytics.track_funnel_progress(
                journey.funnel_id, lead_id, new_stage
            )
            
            # Trigger stage entry automation
            await self._trigger_stage_entry_automation(journey.funnel_id, lead_id, new_stage_obj)
            
            # Update funnel metrics
            await self._update_funnel_metrics(journey.funnel_id)
            
            # Store updated journey
            await self._store_lead_journey(journey)
            
            logger.info(f"Advanced lead {lead_id} from {journey.current_stage} to {new_stage}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to advance lead stage: {e}")
            return False
    
    async def track_lead_activity(self, lead_id: str, activity_type: str, 
                                 activity_data: Dict[str, Any]) -> bool:
        """Track lead activity and update journey"""
        try:
            if lead_id not in self.lead_journeys:
                return False
            
            journey = self.lead_journeys[lead_id]
            journey.last_activity = datetime.utcnow()
            journey.total_touchpoints += 1
            
            # Track conversion event if applicable
            if activity_type in ["email_opened", "email_clicked", "website_visit", "demo_scheduled"]:
                await self.analytics.track_marketing_event({
                    "event_type": "conversion",
                    "lead_id": lead_id,
                    "event_type": activity_type,
                    "event_data": activity_data,
                    "source": "sales_funnel",
                    "campaign_id": activity_data.get("campaign_id")
                })
            
            # Update conversion probability
            journey.conversion_probability = await self._calculate_conversion_probability(lead_id)
            
            # Store updated journey
            await self._store_lead_journey(journey)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to track lead activity: {e}")
            return False
    
    async def get_funnel_performance(self, funnel_id: str, 
                                   time_period: timedelta = timedelta(days=30)) -> Dict[str, Any]:
        """Get comprehensive funnel performance metrics"""
        try:
            if funnel_id not in self.funnels:
                return {}
            
            funnel = self.funnels[funnel_id]
            
            # Get basic funnel metrics
            basic_metrics = {
                "funnel_id": funnel_id,
                "name": funnel.name,
                "total_leads": funnel.total_leads,
                "total_conversions": funnel.total_conversions,
                "overall_conversion_rate": funnel.overall_conversion_rate,
                "current_revenue": funnel.current_revenue,
                "revenue_target": funnel.revenue_target
            }
            
            # Get stage-by-stage metrics
            stage_metrics = []
            for stage in funnel.stages:
                stage_data = {
                    "name": stage.name,
                    "order": stage.order,
                    "total_entries": stage.total_entries,
                    "total_exits": stage.total_exits,
                    "current_conversion_rate": stage.current_conversion_rate,
                    "target_conversion_rate": stage.target_conversion_rate
                }
                stage_metrics.append(stage_data)
            
            # Get lead journey analytics
            journey_analytics = await self._get_journey_analytics(funnel_id, time_period)
            
            # Get A/B test results if any
            ab_test_results = await self._get_funnel_ab_test_results(funnel_id)
            
            return {
                **basic_metrics,
                "stages": stage_metrics,
                "journey_analytics": journey_analytics,
                "ab_test_results": ab_test_results,
                "time_period": str(time_period)
            }
            
        except Exception as e:
            logger.error(f"Failed to get funnel performance: {e}")
            return {}
    
    async def create_funnel_ab_test(self, funnel_id: str, test_config: Dict[str, Any]) -> Experiment:
        """Create an A/B test for funnel optimization"""
        try:
            if funnel_id not in self.funnels:
                raise ValueError(f"Funnel not found: {funnel_id}")
            
            # Create experiment variants
            variants = []
            for variant_data in test_config.get("variants", []):
                variant = Variant(
                    name=variant_data["name"],
                    variant_type=variant_data.get("type", "variant"),
                    content=variant_data.get("content", {}),
                    traffic_percentage=variant_data.get("traffic_percentage", 0.0)
                )
                variants.append(variant)
            
            # Create experiment
            experiment = await self.ab_testing.create_experiment({
                "name": f"Funnel Optimization - {self.funnels[funnel_id].name}",
                "description": test_config.get("description", ""),
                "hypothesis": test_config.get("hypothesis", ""),
                "variants": variants,
                "primary_metric": test_config.get("primary_metric", "conversion_rate"),
                "secondary_metrics": test_config.get("secondary_metrics", []),
                "target_audience": test_config.get("target_audience", {}),
                "confidence_level": test_config.get("confidence_level", 0.95)
            })
            
            logger.info(f"Created A/B test for funnel {funnel_id}: {experiment.name}")
            return experiment
            
        except Exception as e:
            logger.error(f"Failed to create funnel A/B test: {e}")
            raise
    
    async def _trigger_stage_entry_automation(self, funnel_id: str, lead_id: str, stage: FunnelStage):
        """Trigger automation rules when a lead enters a stage"""
        try:
            # Execute automation rules
            for rule_id in stage.automation_rules:
                await self.automation._trigger_event("stage_entry", {
                    "funnel_id": funnel_id,
                    "lead_id": lead_id,
                    "stage_name": stage.name,
                    "rule_id": rule_id
                })
            
            # Send email sequences
            for sequence_id in stage.email_sequences:
                await self._send_stage_email_sequence(lead_id, sequence_id, stage)
                
        except Exception as e:
            logger.error(f"Failed to trigger stage entry automation: {e}")
    
    async def _send_stage_email_sequence(self, lead_id: str, sequence_id: str, stage: FunnelStage):
        """Send email sequence for a specific stage"""
        try:
            # Get lead information
            lead = self.automation.get_lead(lead_id)
            if not lead:
                return
            
            # Create email campaign for the stage
            campaign = await self.email_service.create_campaign({
                "name": f"Stage: {stage.name} - {lead.email}",
                "subject": f"Welcome to {stage.name}",
                "recipients": [lead.email],
                "template_id": sequence_id,
                "variables": {
                    "lead_name": f"{lead.first_name} {lead.last_name}",
                    "company": lead.company,
                    "stage_name": stage.name,
                    "stage_description": stage.description
                }
            })
            
            # Send the email
            await self.email_service.send_campaign(campaign.id)
            
        except Exception as e:
            logger.error(f"Failed to send stage email sequence: {e}")
    
    def _validate_stage_transition(self, current_stage: Optional[FunnelStage], 
                                  new_stage: FunnelStage, 
                                  trigger_data: Optional[Dict[str, Any]]) -> bool:
        """Validate if a stage transition is allowed"""
        try:
            if not current_stage:
                # First stage entry is always valid
                return True
            
            # Check if new stage is next in sequence
            if new_stage.order <= current_stage.order:
                # Allow backward movement only if explicitly configured
                if not trigger_data or not trigger_data.get("allow_backward", False):
                    return False
            
            # Check exit criteria for current stage
            if current_stage.exit_criteria:
                if not self._check_exit_criteria(current_stage.exit_criteria, trigger_data):
                    return False
            
            # Check entry criteria for new stage
            if new_stage.entry_criteria:
                if not self._check_entry_criteria(new_stage.entry_criteria, trigger_data):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate stage transition: {e}")
            return False
    
    def _check_exit_criteria(self, exit_criteria: Dict[str, Any], 
                            trigger_data: Optional[Dict[str, Any]]) -> bool:
        """Check if exit criteria are met"""
        try:
            # This is a simplified implementation
            # In practice, you'd have more sophisticated criteria checking
            required_actions = exit_criteria.get("required_actions", [])
            if not required_actions:
                return True
            
            if not trigger_data:
                return False
            
            # Check if required actions are present in trigger data
            for action in required_actions:
                if action not in trigger_data.get("actions", []):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check exit criteria: {e}")
            return False
    
    def _check_entry_criteria(self, entry_criteria: Dict[str, Any], 
                             trigger_data: Optional[Dict[str, Any]]) -> bool:
        """Check if entry criteria are met"""
        try:
            # This is a simplified implementation
            # In practice, you'd have more sophisticated criteria checking
            required_conditions = entry_criteria.get("required_conditions", [])
            if not required_conditions:
                return True
            
            if not trigger_data:
                return False
            
            # Check if required conditions are met
            for condition in required_conditions:
                if not self._evaluate_condition(condition, trigger_data):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check entry criteria: {e}")
            return False
    
    def _evaluate_condition(self, condition: Dict[str, Any], 
                           trigger_data: Dict[str, Any]) -> bool:
        """Evaluate a single condition"""
        try:
            condition_type = condition.get("type", "")
            field = condition.get("field", "")
            operator = condition.get("operator", "")
            value = condition.get("value")
            
            if field not in trigger_data:
                return False
            
            actual_value = trigger_data[field]
            
            if operator == "equals":
                return actual_value == value
            elif operator == "not_equals":
                return actual_value != value
            elif operator == "greater_than":
                return actual_value > value
            elif operator == "less_than":
                return actual_value < value
            elif operator == "contains":
                return value in actual_value
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to evaluate condition: {e}")
            return False
    
    async def _calculate_conversion_probability(self, lead_id: str) -> float:
        """Calculate lead's probability of conversion"""
        try:
            # This is a simplified implementation
            # In practice, you'd use machine learning models or scoring algorithms
            
            lead = self.automation.get_lead(lead_id)
            if not lead:
                return 0.0
            
            # Base score from lead attributes
            base_score = 0.0
            
            # Company size scoring
            if lead.company_size == "enterprise":
                base_score += 20
            elif lead.company_size == "large":
                base_score += 15
            elif lead.company_size == "medium":
                base_score += 10
            elif lead.company_size == "small":
                base_score += 5
            
            # Industry scoring
            if lead.industry in ["technology", "finance", "healthcare"]:
                base_score += 15
            elif lead.industry in ["manufacturing", "retail"]:
                base_score += 10
            else:
                base_score += 5
            
            # Budget scoring
            if lead.budget == "enterprise":
                base_score += 20
            elif lead.budget == "large":
                base_score += 15
            elif lead.budget == "medium":
                base_score += 10
            elif lead.budget == "small":
                base_score += 5
            
            # Activity scoring
            journey = self.lead_journeys.get(lead_id)
            if journey:
                # More touchpoints = higher probability
                base_score += min(journey.total_touchpoints * 2, 20)
                
                # Recent activity bonus
                days_since_activity = (datetime.utcnow() - journey.last_activity).days
                if days_since_activity <= 1:
                    base_score += 15
                elif days_since_activity <= 7:
                    base_score += 10
                elif days_since_activity <= 30:
                    base_score += 5
            
            # Normalize to 0-100 scale
            probability = min(100.0, max(0.0, base_score))
            
            return probability
            
        except Exception as e:
            logger.error(f"Failed to calculate conversion probability: {e}")
            return 0.0
    
    async def _get_journey_analytics(self, funnel_id: str, 
                                    time_period: timedelta) -> Dict[str, Any]:
        """Get analytics for lead journeys in the funnel"""
        try:
            cutoff_time = datetime.utcnow() - time_period
            
            # Get all journeys for this funnel
            funnel_journeys = [
                journey for journey in self.lead_journeys.values()
                if journey.funnel_id == funnel_id and journey.entry_date >= cutoff_time
            ]
            
            if not funnel_journeys:
                return {}
            
            # Calculate journey metrics
            total_journeys = len(funnel_journeys)
            completed_journeys = len([
                j for j in funnel_journeys 
                if j.current_stage == "converted" or j.current_stage == "closed_won"
            ])
            
            # Calculate average time in funnel
            total_time = sum([
                (j.last_activity - j.entry_date).total_seconds()
                for j in funnel_journeys
            ], 0)
            
            avg_time_in_funnel = total_time / total_journeys if total_journeys > 0 else 0
            
            # Calculate stage transition rates
            stage_transitions = {}
            for journey in funnel_journeys:
                for i, transition in enumerate(journey.stage_history):
                    if i > 0:
                        from_stage = journey.stage_history[i-1]["from_stage"]
                        to_stage = transition["from_stage"]
                        key = f"{from_stage}_to_{to_stage}"
                        stage_transitions[key] = stage_transitions.get(key, 0) + 1
            
            return {
                "total_journeys": total_journeys,
                "completed_journeys": completed_journeys,
                "completion_rate": (completed_journeys / total_journeys) * 100 if total_journeys > 0 else 0,
                "average_time_in_funnel": avg_time_in_funnel,
                "stage_transitions": stage_transitions,
                "average_touchpoints": sum(j.total_touchpoints for j in funnel_journeys) / total_journeys if total_journeys > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get journey analytics: {e}")
            return {}
    
    async def _get_funnel_ab_test_results(self, funnel_id: str) -> List[Dict[str, Any]]:
        """Get A/B test results for funnel optimization"""
        try:
            # Get all experiments that might be related to this funnel
            # This is a simplified implementation
            results = []
            
            for experiment_id, experiment in self.ab_testing.experiments.items():
                if funnel_id in experiment.name.lower() or "funnel" in experiment.name.lower():
                    experiment_results = await self.ab_testing.get_experiment_results(experiment_id)
                    
                    for result in experiment_results:
                        results.append({
                            "experiment_id": experiment_id,
                            "experiment_name": experiment.name,
                            "variant_name": result.variant_name,
                            "conversion_rate": result.conversion_rate,
                            "statistical_significance": result.statistical_significance,
                            "is_winner": result.is_winner
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get funnel A/B test results: {e}")
            return []
    
    async def _update_funnel_metrics(self, funnel_id: str):
        """Update funnel performance metrics"""
        try:
            if funnel_id not in self.funnels:
                return
            
            funnel = self.funnels[funnel_id]
            
            # Calculate overall conversion rate
            if funnel.total_leads > 0:
                funnel.overall_conversion_rate = (funnel.total_conversions / funnel.total_leads) * 100
            
            # Update stage conversion rates
            for i, stage in enumerate(funnel.stages):
                if stage.total_entries > 0:
                    if i == 0:
                        stage.current_conversion_rate = 100.0
                    else:
                        prev_stage = funnel.stages[i - 1]
                        if prev_stage.total_entries > 0:
                            stage.current_conversion_rate = (stage.total_entries / prev_stage.total_entries) * 100
                        else:
                            stage.current_conversion_rate = 0.0
            
            # Calculate total conversions (leads in final stage)
            if funnel.stages:
                final_stage = funnel.stages[-1]
                funnel.total_conversions = final_stage.total_entries
            
            funnel.updated_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to update funnel metrics: {e}")
    
    async def _store_funnel(self, funnel: SalesFunnel):
        """Store funnel in database"""
        try:
            # Implementation would depend on your database schema
            logger.debug(f"Storing funnel in database: {funnel.id}")
        except Exception as e:
            logger.error(f"Failed to store funnel: {e}")
    
    async def _store_lead_journey(self, journey: LeadJourney):
        """Store lead journey in database"""
        try:
            # Implementation would depend on your database schema
            logger.debug(f"Storing lead journey in database: {journey.lead_id}")
        except Exception as e:
            logger.error(f"Failed to store lead journey: {e}")
