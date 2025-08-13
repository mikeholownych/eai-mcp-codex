"""
Marketing analytics and performance tracking module.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from uuid import uuid4
import json
from collections import defaultdict, Counter

from ..common.redis_client import RedisClient
from ..common.database import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class ConversionEvent:
    """Conversion event for tracking"""
    id: str = field(default_factory=lambda: str(uuid4()))
    lead_id: str = ""
    event_type: str = ""
    event_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    value: Optional[float] = None
    source: str = ""
    campaign_id: Optional[str] = None
    channel: str = ""


@dataclass
class FunnelStage:
    """Funnel stage definition"""
    name: str
    order: int
    criteria: Dict[str, Any]
    conversion_rate: float = 0.0
    total_entries: int = 0
    total_exits: int = 0


@dataclass
class FunnelMetrics:
    """Funnel performance metrics"""
    funnel_id: str
    name: str
    stages: List[FunnelStage]
    total_conversions: int = 0
    overall_conversion_rate: float = 0.0
    average_time_to_convert: Optional[timedelta] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class ConversionTracker:
    """Tracks conversion events and calculates metrics"""
    
    def __init__(self, redis_client: RedisClient, db_manager: DatabaseManager):
        self.redis_client = redis_client
        self.db_manager = db_manager
        self.conversion_events: Dict[str, ConversionEvent] = {}
        
    async def track_conversion(self, event: ConversionEvent) -> bool:
        """Track a new conversion event"""
        try:
            # Store in memory
            self.conversion_events[event.id] = event
            
            # Store in Redis for real-time analytics
            await self.redis_client.hset(
                f"conversion_events:{event.lead_id}",
                event.id,
                json.dumps(event.__dict__, default=str)
            )
            
            # Store in database for persistence
            await self._store_conversion_event(event)
            
            logger.info(f"Tracked conversion event: {event.event_type} for lead {event.lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track conversion event: {e}")
            return False
    
    async def get_conversion_events(self, lead_id: str, event_type: Optional[str] = None) -> List[ConversionEvent]:
        """Get conversion events for a lead"""
        try:
            if event_type:
                return [
                    event for event in self.conversion_events.values()
                    if event.lead_id == lead_id and event.event_type == event_type
                ]
            else:
                return [
                    event for event in self.conversion_events.values()
                    if event.lead_id == lead_id
                ]
        except Exception as e:
            logger.error(f"Failed to get conversion events: {e}")
            return []
    
    async def get_conversion_rate(self, event_type: str, time_period: timedelta = timedelta(days=30)) -> float:
        """Calculate conversion rate for a specific event type"""
        try:
            cutoff_time = datetime.utcnow() - time_period
            events = [
                event for event in self.conversion_events.values()
                if event.event_type == event_type and event.timestamp >= cutoff_time
            ]
            
            if not events:
                return 0.0
                
            # This is a simplified calculation - in practice you'd want to track
            # the total number of opportunities vs conversions
            return len(events) / max(len(events), 1) * 100
            
        except Exception as e:
            logger.error(f"Failed to calculate conversion rate: {e}")
            return 0.0
    
    async def _store_conversion_event(self, event: ConversionEvent):
        """Store conversion event in database"""
        try:
            # Implementation would depend on your database schema
            # For now, we'll just log it
            logger.debug(f"Storing conversion event in database: {event.id}")
        except Exception as e:
            logger.error(f"Failed to store conversion event: {e}")


class FunnelAnalytics:
    """Analyzes funnel performance and conversion rates"""
    
    def __init__(self, redis_client: RedisClient, db_manager: DatabaseManager):
        self.redis_client = redis_client
        self.db_manager = db_manager
        self.funnels: Dict[str, FunnelMetrics] = {}
        
    async def create_funnel(self, name: str, stages: List[Dict[str, Any]]) -> FunnelMetrics:
        """Create a new conversion funnel"""
        try:
            funnel_id = str(uuid4())
            funnel_stages = []
            
            for i, stage_data in enumerate(stages):
                stage = FunnelStage(
                    name=stage_data["name"],
                    order=i,
                    criteria=stage_data.get("criteria", {}),
                    conversion_rate=0.0
                )
                funnel_stages.append(stage)
            
            funnel = FunnelMetrics(
                funnel_id=funnel_id,
                name=name,
                stages=funnel_stages
            )
            
            self.funnels[funnel_id] = funnel
            await self._store_funnel(funnel)
            
            logger.info(f"Created funnel: {name} with {len(stages)} stages")
            return funnel
            
        except Exception as e:
            logger.error(f"Failed to create funnel: {e}")
            raise
    
    async def track_funnel_progress(self, funnel_id: str, lead_id: str, stage_name: str) -> bool:
        """Track a lead's progress through a funnel stage"""
        try:
            if funnel_id not in self.funnels:
                logger.error(f"Funnel not found: {funnel_id}")
                return False
                
            funnel = self.funnels[funnel_id]
            stage = next((s for s in funnel.stages if s.name == stage_name), None)
            
            if not stage:
                logger.error(f"Stage not found: {stage_name}")
                return False
            
            # Update stage metrics
            stage.total_entries += 1
            
            # Store progress in Redis
            await self.redis_client.hset(
                f"funnel_progress:{funnel_id}:{lead_id}",
                stage_name,
                datetime.utcnow().isoformat()
            )
            
            # Update funnel metrics
            await self._update_funnel_metrics(funnel_id)
            
            logger.debug(f"Tracked funnel progress: {lead_id} -> {stage_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track funnel progress: {e}")
            return False
    
    async def get_funnel_metrics(self, funnel_id: str) -> Optional[FunnelMetrics]:
        """Get funnel performance metrics"""
        try:
            if funnel_id not in self.funnels:
                return None
                
            funnel = self.funnels[funnel_id]
            await self._update_funnel_metrics(funnel_id)
            return funnel
            
        except Exception as e:
            logger.error(f"Failed to get funnel metrics: {e}")
            return None
    
    async def _update_funnel_metrics(self, funnel_id: str):
        """Update funnel conversion rates and metrics"""
        try:
            funnel = self.funnels[funnel_id]
            
            for i, stage in enumerate(funnel.stages):
                if stage.total_entries > 0:
                    if i == 0:
                        # First stage - no previous stage to convert from
                        stage.conversion_rate = 100.0
                    else:
                        # Calculate conversion rate from previous stage
                        prev_stage = funnel.stages[i - 1]
                        if prev_stage.total_entries > 0:
                            stage.conversion_rate = (stage.total_entries / prev_stage.total_entries) * 100
                        else:
                            stage.conversion_rate = 0.0
            
            # Calculate overall conversion rate
            if funnel.stages:
                last_stage = funnel.stages[-1]
                first_stage = funnel.stages[0]
                if first_stage.total_entries > 0:
                    funnel.overall_conversion_rate = (last_stage.total_entries / first_stage.total_entries) * 100
                    funnel.total_conversions = last_stage.total_entries
            
            funnel.updated_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to update funnel metrics: {e}")
    
    async def _store_funnel(self, funnel: FunnelMetrics):
        """Store funnel in database"""
        try:
            # Implementation would depend on your database schema
            logger.debug(f"Storing funnel in database: {funnel.funnel_id}")
        except Exception as e:
            logger.error(f"Failed to store funnel: {e}")


class MarketingAnalytics:
    """Main marketing analytics class that combines conversion tracking and funnel analytics"""
    
    def __init__(self, redis_client: RedisClient, db_manager: DatabaseManager):
        self.redis_client = redis_client
        self.db_manager = db_manager
        self.conversion_tracker = ConversionTracker(redis_client, db_manager)
        self.funnel_analytics = FunnelAnalytics(redis_client, db_manager)
        
    async def track_marketing_event(self, event_data: Dict[str, Any]) -> bool:
        """Track a marketing event (conversion, funnel progress, etc.)"""
        try:
            event_type = event_data.get("event_type", "")
            
            if event_type == "conversion":
                event = ConversionEvent(**event_data)
                return await self.conversion_tracker.track_conversion(event)
            elif event_type == "funnel_progress":
                return await self.funnel_analytics.track_funnel_progress(
                    event_data["funnel_id"],
                    event_data["lead_id"],
                    event_data["stage_name"]
                )
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to track marketing event: {e}")
            return False
    
    async def get_campaign_performance(self, campaign_id: str, time_period: timedelta = timedelta(days=30)) -> Dict[str, Any]:
        """Get performance metrics for a specific campaign"""
        try:
            cutoff_time = datetime.utcnow() - time_period
            
            # Get conversion events for the campaign
            campaign_events = [
                event for event in self.conversion_tracker.conversion_events.values()
                if event.campaign_id == campaign_id and event.timestamp >= cutoff_time
            ]
            
            # Calculate metrics
            total_events = len(campaign_events)
            unique_leads = len(set(event.lead_id for event in campaign_events))
            
            # Group by event type
            event_counts = Counter(event.event_type for event in campaign_events)
            
            # Calculate total value
            total_value = sum(event.value or 0 for event in campaign_events)
            
            return {
                "campaign_id": campaign_id,
                "time_period": str(time_period),
                "total_events": total_events,
                "unique_leads": unique_leads,
                "event_breakdown": dict(event_counts),
                "total_value": total_value,
                "average_value_per_event": total_value / total_events if total_events > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get campaign performance: {e}")
            return {}
    
    async def get_lead_journey(self, lead_id: str) -> Dict[str, Any]:
        """Get the complete journey of a lead through marketing touchpoints"""
        try:
            # Get all conversion events for the lead
            events = await self.conversion_tracker.get_conversion_events(lead_id)
            
            # Sort events by timestamp
            events.sort(key=lambda x: x.timestamp)
            
            # Get funnel progress for all funnels
            funnel_progress = {}
            for funnel_id in self.funnel_analytics.funnels:
                progress = await self.redis_client.hgetall(f"funnel_progress:{funnel_id}:{lead_id}")
                if progress:
                    funnel_progress[funnel_id] = progress
            
            return {
                "lead_id": lead_id,
                "total_events": len(events),
                "events": [
                    {
                        "event_type": event.event_type,
                        "timestamp": event.timestamp.isoformat(),
                        "value": event.value,
                        "source": event.source,
                        "campaign_id": event.campaign_id
                    }
                    for event in events
                ],
                "funnel_progress": funnel_progress,
                "first_touch": events[0].timestamp.isoformat() if events else None,
                "last_touch": events[-1].timestamp.isoformat() if events else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get lead journey: {e}")
            return {}
    
    async def get_marketing_dashboard_data(self, time_period: timedelta = timedelta(days=30)) -> Dict[str, Any]:
        """Get comprehensive marketing dashboard data"""
        try:
            cutoff_time = datetime.utcnow() - time_period
            
            # Get all events in the time period
            recent_events = [
                event for event in self.conversion_tracker.conversion_events.values()
                if event.timestamp >= cutoff_time
            ]
            
            # Calculate overall metrics
            total_conversions = len(recent_events)
            unique_leads = len(set(event.lead_id for event in recent_events))
            total_value = sum(event.value or 0 for event in recent_events)
            
            # Event type breakdown
            event_type_counts = Counter(event.event_type for event in recent_events)
            
            # Channel breakdown
            channel_counts = Counter(event.channel for event in recent_events)
            
            # Campaign breakdown
            campaign_counts = Counter(event.campaign_id for event in recent_events if event.campaign_id)
            
            # Funnel performance
            funnel_performance = {}
            for funnel_id, funnel in self.funnel_analytics.funnels.items():
                metrics = await self.funnel_analytics.get_funnel_metrics(funnel_id)
                if metrics:
                    funnel_performance[funnel_id] = {
                        "name": metrics.name,
                        "overall_conversion_rate": metrics.overall_conversion_rate,
                        "total_conversions": metrics.total_conversions,
                        "stages": [
                            {
                                "name": stage.name,
                                "conversion_rate": stage.conversion_rate,
                                "total_entries": stage.total_entries
                            }
                            for stage in metrics.stages
                        ]
                    }
            
            return {
                "time_period": str(time_period),
                "overview": {
                    "total_conversions": total_conversions,
                    "unique_leads": unique_leads,
                    "total_value": total_value,
                    "average_value_per_conversion": total_value / total_conversions if total_conversions > 0 else 0
                },
                "event_breakdown": dict(event_type_counts),
                "channel_breakdown": dict(channel_counts),
                "campaign_breakdown": dict(campaign_counts),
                "funnel_performance": funnel_performance
            }
            
        except Exception as e:
            logger.error(f"Failed to get marketing dashboard data: {e}")
            return {}
